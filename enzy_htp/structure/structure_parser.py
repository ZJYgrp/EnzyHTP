"""Structure parser function that takes a pdb file as input and returns an enzy_htp.structure.Structure() object.
Setup as a single function. Users should only call the high level function structure_from_pdb(). Other functions that exist in the 
file help to categorize Residue() objects and organize the Chain() id's in a consistent, repdocucible way.

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2022-03-29
"""
import os
import string
import warnings
import numpy as np
import pandas as pd
from typing import Union
from copy import deepcopy
from collections import defaultdict
from biopandas.pdb import PandasPdb
from typing import List, Set, Dict, Tuple

from .atom import Atom
from .metal_atom import MetalUnit
from .residue import Residue
from .solvent import Solvent, residue_to_solvent
from .ligand import Ligand, residue_to_ligand
from .metal_atom import MetalUnit, residue_to_metal
from .chain import Chain
from .structure import Structure
from enzy_htp.core import _LOGGER
import enzy_htp.core.file_system as fs
import enzy_htp.chemical as chem


def legal_chain_names(mapper: Dict[str, List[Residue]]) -> List[str]:
    """Small helper method that determines the legal chain names given a Residue() mapper.
    Uses all of the available 26 capitalized letters and returns in reverse order. Returns an empty list when all are occupied."""
    result = list(string.ascii_uppercase)
    taken = set(list(mapper.keys()))
    result = list(filter(lambda s: s not in taken, result))
    return list(reversed(result))


def name_chains(mapper: Dict[str, List[Residue]]) -> None:
    """Function takes a defaultdict(list) of Residues and ensures consistent naming of chains with no blanks."""
    key_names = set(list(map(lambda kk: kk.strip(), mapper.keys())))
    if "" not in key_names:
        return mapper
    unnamed = list(mapper[""])
    del mapper[""]

    names = legal_chain_names(mapper)
    unnamed = sorted(unnamed, key=lambda r: r.min_line())
    new_chain: List[Residue] = []

    for res in unnamed:
        if not new_chain:
            new_chain.append(res)
        elif new_chain[-1].neighbors(res):
            new_chain.append(res)
        else:
            mapper[names.pop()] = deepcopy(new_chain)
            new_chain = [res]
    if new_chain:
        mapper[names.pop()] = deepcopy(new_chain)
    return mapper


def categorize_residue(residue: Residue) -> Union[Residue, Ligand, Solvent, MetalUnit]:
    """Method that takes a default Residue() and converts it into its specialized Residue() inherited class."""
    # TODO(CJ): I need to add in stuff here for the solvent types.
    if residue.is_canonical():
        residue.rtype = chem.ResidueType.CANONICAL
        return residue

    if (residue.name
            in chem.METAL_MAPPER):  # TODO(CJ): implement more OOP method for this
        return residue_to_metal(residue)

    if residue.is_solvent():  # TODO(CJ): make sure this logic is 100% right
        return residue_to_solvent(residue)

    return residue_to_ligand(residue)


def build_residues(
        df: pd.DataFrame,
        keep: str = "first") -> Dict[str, Union[Residue, Ligand, Solvent, MetalUnit]]:
    """Helper method that builds Residue() or derived Residue() objects from a dataframe generated by BioPandas.
    Returns as a dict() with (key, value) pairs of (residue_key, Union[Residue,Ligand,Solvent,MetalUnit]).""" #@shaoqz: should we also explain the keep here?
    mapper = defaultdict(list)
    for i, row in df.iterrows():
        aa = Atom(**row)
        mapper[aa.residue_key()].append(aa)
    # for k,v in mapper.items():
    # print(k,len(v))
    result: Dict[str, Residue] = dict()
    for res_key, atoms in mapper.items():
        result[res_key] = Residue(residue_key=res_key,
                                  atoms=sorted(atoms, key=lambda a: a.atom_number))
    for (res_key, res) in result.items():
        result[res_key] = categorize_residue(res)
        if keep != "all":
            result[res_key].resolve_alt_loc(keep)
            result[res_key].remove_alt_loc()
            # result[res_key].remove_occupancy() #@shaoqz: what happened here?
    return result


def build_chains(mapper: Dict[str, Residue]) -> Dict[str, Chain]:
    """Helper method that builds the Chain() objects from a dict() of (residue_key, Residue()) pairs generated by build_residues()."""
    chain_mapper = defaultdict(list)
    for res in mapper.values():
        chain_mapper[res.chain()].append(res)
    chain_mapper = name_chains(chain_mapper)
    result: Dict[str, Chain] = dict()
    # ok this is where we handle missing chain ids
    for chain_name, residues in chain_mapper.items():
        result[chain_name] = Chain(chain_name, sorted(residues, key=lambda r: r.idx()))
    return result


def check_valid_pdb(pdbname: str) -> None:
    """Helper function that ensures the supplied pdbname is a valid pdb file.
    Private to structure.structure_parser.py. Should NOT be called externally."""
    ext: str = fs.get_file_ext(pdbname)
    if ext.lower() != ".pdb":
        _LOGGER.error(f"Supplied file '{pdbname}' is NOT a PDB file. Exiting...")
        exit(1)

    if not os.path.exists(pdbname):
        _LOGGER.error(f"Supplied file '{pdbname}' does NOT exist. Exiting...")
        exit(1)

    for idx, ll in enumerate(fs.lines_from_file(pdbname)):
        if not ll.isascii():
            _LOGGER.error(
                f"The PDB '{pdbname}' contains non-ASCII text and is invalid in line {idx}: '{ll}'. Exiting..."
            )
            exit(1)


def ligand_from_pdb(fname: str, net_charge: float = None) -> Ligand:
    """Creates a Ligand() object from a supplied .pdb file. Checks that the input file both exists and is ASCII format."""

    def get_charge_mapper(fname: str) -> dict:
        """Helper method that gets charges"""
        lines = fs.lines_from_file(fname)
        result = dict()
        for ll in lines:
            raw_charge = ll[78:80].strip()
            if not raw_charge:
                continue
            mult = 1
            temp = ''
            for ch in raw_charge:
                if ch != '-':
                    temp += ch
                else:
                    mult = -1
            result[(ll[21].strip(), int(ll[6:11]))] = mult * int(temp)
        return result

    check_valid_pdb(fname)
    warnings.filterwarnings("ignore")
    # adapt general input // converge to a list of PDB_line (resi_lines)
    parser = PandasPdb()
    parser.read_pdb(fname)
    temp_df = pd.concat((parser.df["ATOM"], parser.df["HETATM"]))
    charge_mapper = get_charge_mapper(fname)
    #TODO(CJ): put this into its own function
    for (cname, a_id), charge in charge_mapper.items():
        #print(cname, a_id, charge)
        mask = ((temp_df.chain_id == cname) & (temp_df.atom_number == a_id)).to_numpy()
        idx = np.where(mask)[0][0]
        temp_df.at[idx, 'charge'] = charge
    atoms = list(map(
        lambda pr: Atom(**pr[1]),
        temp_df.iterrows(),
    ))
    residue_name = set(list(map(lambda a: a.residue_name, atoms)))
    residue_number = set(list(map(lambda a: a.residue_number, atoms)))
    chain_id = set(list(map(lambda a: a.chain_id, atoms)))
    assert len(residue_name) == 1
    assert len(residue_number) == 1
    assert len(chain_id) == 1
    # TODO(CJ): should I set the chain for this if it is blank?
    key = f"{list(chain_id)[0]}.{list(residue_name)[0]}.{list(residue_number)[0]}"
    result = Residue(key, atoms)
    result = residue_to_ligand(result)
    result.net_charge = net_charge  # TODO(CJ): make net_charge a getter/setter
    return result


def structure_from_pdb(fname: str, keep: str = "first") -> Structure:
    """Method that creates a Structure() object from a supplied .pdb file. Checks that the input file both exists and is ASCII format."""
    # TODO(CJ): Update this docstring
    check_valid_pdb(fname)
    parser = PandasPdb()
    parser.read_pdb(fname)
    res_mapper: Dict[str, Residue] = build_residues(
        pd.concat((parser.df["ATOM"], parser.df["HETATM"])),
        keep  #@shaoqz: so it works with multichains w/o chain id? I saw that four chains in test file
    )
    chain_mapper: Dict[str, Chain] = build_chains(res_mapper)
    return Structure(list(chain_mapper.values()))


def get_ligand_name(fname: str) -> str:
    # TODO(CJ): add the documentation here
    # TODO(CJ): make this more efficient
    # TODO(CJ): add testing for this
    ligand: Ligand = ligand_from_pdb(fname)
    return deepcopy(ligand.name())
