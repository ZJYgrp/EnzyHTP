import json
from typing import List, Tuple, Dict, Set

from rdkit import Chem as _rchem
import numpy as np
import pandas as pd
import enzy_htp as eh
from pathlib import Path
from copy import deepcopy
from collections import defaultdict

from enzy_htp import interface, config
from enzy_htp.core import file_system as fs

from enzy_htp.core import _LOGGER

import enzy_htp.chemical as chem
from enzy_htp.structure import PDBParser, Structure, Ligand, Mol2Parser, Chain
from enzy_htp.structure.structure_constraint import StructureConstraint
from enzy_htp._interface import Mole2Cavity

from .align_ligand import align_ligand, mimic_torsions


from enzy_htp.geometry import minimize as geo_minimize





def seed_ligand(stru: Structure, ligand:Ligand, method:str='alphafill', minimize:bool=False, constraints:List[StructureConstraint]=None, work_dir:str=None, **kwargs) -> Structure:

    if not work_dir:
        work_dir = config['system.SCRATCH_DIR']

    fs.safe_mkdir(work_dir)


    if method == 'alphafill':
        _seed_alphafill(stru, ligand, work_dir=work_dir, **kwargs)
    elif method == 'ligand_analog':
        _seed_ligand_analog(stru, ligand, work_dir=work_dir, **kwargs) 

    if minimize:
        sele = f'(chain {ligand.parent.name} and resi {ligand.idx})'
        #sele = f'byres polymer.protein within 2 of {lig_sele} or {lig_sele}'
        geo_minimize(stru, movemap=[
            {'sele':sele, 'bb':'true', 'chi':'true', 'bondangle':'true'}, 
            {'sele':f'not ({sele})', 'bb':'false', 'chi':'false', 'bondangle':'false'}, 

        ],n_iter=1)


def _seed_alphafill(stru: Structure,
                        ligand:Ligand,
                     work_dir: str,
                     #similarity_cutoff: float = 0.75,
                     clash_radius: float = 2.0, #TODO(CJ); get rid of this
                     **kwargs) -> Ligand:
    """Implementation function that places a specified ligand into a structure using the alphafill 
    algorithm (https://doi.org/10.1038/s41592-022-01685-y). SHOULD NOT be called directly by the user. 
    Instead, call `enzy_htp.preparation.place_ligand.place_ligand()`. Assumes that the input Ligand() has PDB style naming 
    and is in the .mol2 format. When scanning alphafill transplants, the algorithm looks for exact atom label
    matches. If none are found, then a similarity score is calculated which is:

    intersection(candidate atoms, template atoms) / max( number candidate atoms, number template atoms )

    Args:
        stru: Structure() where the Ligand() will be added.
        ligand: The Ligand() object that is being placed.
        work_dir: Directory where all temporary files will be saved.
        similarity_cutoff: How similar a Ligand() and template must be to get considered.
        clash_radius: Radius cutoff (Angstroms) for clash counting between two heavy atoms.

    Returns:
        An aligned, deepcopied Ligand().
    """
    _LOGGER.info(f"Beginnning placement of ligand {ligand} into the structure...")
    _LOGGER.info(f"Calling out to AlphaFill to fill structure...")

    structure_start:str=f"{work_dir}/afill_temp.pdb"
    fs.safe_rm(structure_start)

    similarity_cutoff:float = kwargs.get('similarity_cutoff', 0.45)

    parser = PDBParser()
    parser.save_structure(structure_start, stru)
    
    to_delete:List[str] = list()

    session = interface.pymol.new_session()
    ligand_chain:str = ligand.parent.name
    ligand_idx:str = str(ligand.idx)
    interface.pymol.general_cmd(session, [
        ('load', structure_start),
        ('remove', f'chain {ligand_chain} and resi {ligand_idx}'),
        ('save', structure_start, 'polymer.protein'),
        ('delete', 'all')
    ])

    lines:List[str]=fs.lines_from_file(structure_start)

    for lidx, ll in enumerate(lines): #epic fix
        lines[lidx] = ll[0:76]

    fs.write_lines(structure_start, lines)

    (filled_structure, transplant_info_fpath) = interface.alphafill.fill_structure(structure_start,use_cache=kwargs.get('use_cache',False))
    _LOGGER.info("Filled structure using AlphaFill!")
    
    transplant_info = json.load(open(transplant_info_fpath, 'r'))
   
    transplant_data = defaultdict(list)
    for hit in transplant_info['hits']:
        identity = hit['identity']
        for tt in hit['transplants']:
            transplant_data['analogue_id'].append( tt['analogue_id'] )
            transplant_data['identity'].append( identity )
            transplant_data['asym_id'].append( tt['asym_id'] )
            transplant_data['clash_count'].append(tt['clash']['clash_count'])
    
    df = pd.DataFrame(transplant_data)
    #TODO(CJ): add logging and actually use the similarity_cutoff 
    memo = dict()
    atom_names:List[List[str]] = list()
    for i, row in df.iterrows():
        if len(row.analogue_id) <= 2:
            atom_names.append(set([row.analogue_id]))
            continue
        temp_file:str = interface.pymol.fetch(row.analogue_id, out_dir=work_dir)
        to_delete.append( str(Path(temp_file).absolute()) )
        if row.analogue_id not in memo:
            interface.pymol.general_cmd(session, [('load', temp_file)])
            memo[row.analogue_id] = set(interface.pymol.collect(session, 'memory', 'name'.split())['name'].to_list())
            interface.pymol.general_cmd(session, [('delete', 'all')])

        atom_names.append(memo[row.analogue_id])

    df['atom_names'] = atom_names
   
    ligand_atoms:Set[str]=set([aa.name for aa in ligand.atoms])
    
    similarity_score:List[float] = list()
    for i, row in df.iterrows():
        numerator:int=len(row.atom_names.intersection(ligand_atoms))
        denominator:int=max(len(ligand_atoms), len(row.atom_names))
        similarity_score.append(numerator/denominator)

    df['similarity_score'] = similarity_score
    similarity_mask = df.similarity_score >= similarity_cutoff

    if not similarity_mask.sum():
        _LOGGER.error(f"No transplants exist with similarity_cutoff of {similarity_cutoff:.3f}! Exiting...")
        exit( 1 )
    
    df = df[similarity_mask].reset_index(drop=True)
    similarity = df.similarity_score.to_numpy()
    df = df[np.isclose(similarity, np.max(similarity))].reset_index(drop=True)

    df.sort_values(by='clash_count',inplace=True)
    selected_id:str=df.asym_id[0]

    molfile:str=f"{work_dir}/temp.pdb"
    reactant:str=f"{work_dir}/temp_ligand.mol2"
    template:str=f"{work_dir}/template_ligand.mol2"
    outfile:str=f"{work_dir}/aligned_ligand.mol2"
    to_delete.extend([molfile, reactant, template, outfile, structure_start, filled_structure, transplant_info_fpath])

    parser.save_structure(molfile, stru)

    Mol2Parser().save_ligand(reactant, ligand)
    
    pp_chains:List[str] = list()
    for cc in stru.chains:
        if cc.is_polypeptide():
            pp_chains.append(f"chain {cc.name}")

    interface.pymol.general_cmd(session, [('delete', 'all'), ("load", filled_structure), ("remove", "solvent"), ("load", molfile),
                                          ("align", f"{Path(filled_structure).stem} and ({' or '.join(pp_chains)})", f"{Path(molfile).stem} and ({' or '.join(pp_chains)})"),
                                          ("delete", Path(molfile).stem),
                                          ("save", template, f"chain {selected_id} and segi {selected_id}")])
    
    analogue_code = df.analogue_id[0]
    session = interface.pymol.new_session()

    df = interface.pymol.collect(session, template, 'name x y z'.split())
    
    session = interface.pymol.new_session()
    args = [('fetch', analogue_code), ('remove', 'hydrogens')]

    for i, row in df.iterrows():
        args.append(('alter_state', 1, f"name {row['name']}", f"(x, y, z) = ({row.x}, {row.y}, {row.z})"))

    args.append(('save', template))

    interface.pymol.general_cmd(session, args)


    if ligand.is_ligand():
        outfile = mimic_torsions(template, reactant)
    else:
        fs.safe_mv(template, outfile)

    aligned_ligand:Ligand=Mol2Parser().get_ligand(outfile)
    
    for a1 in ligand.atoms:
        for a2 in aligned_ligand.atoms:
            if a1.name == a2.name:
                a1.coord = a2.coord



def _seed_ligand_analog(stru, ligand, work_dir, **kwargs):

    analog_file:str=f"{work_dir}/analog.mol2"
    analog_template_file:str=f"{work_dir}/analog_template.mol2"

    parser = Mol2Parser()
    parser.save_ligand(analog_file, kwargs['analog'])
    parser.save_ligand(analog_template_file, kwargs['analog_template'])

    analog = mimic_torsions(analog_template_file, analog_file)
    
    analog = parser.get_ligand(analog_file)

    target_location = None

    for atom in analog.atoms:
        if atom.name == kwargs['analog_atom']:
            target_location = np.array(atom.coord)
            break
    
    assert target_location is not None

    current_location = None
    for atom in ligand.atoms:
        if atom.name == kwargs['seed_atom']:
            current_location = np.array(atom.coord)
            break

    assert current_location is not None
    shift = target_location - current_location

    ligand.shift( shift )