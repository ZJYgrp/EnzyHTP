'''Testing the PDBParser class in the enzy_htp.structure.structure_io.pdb_io
This class is for parsing in and out from PDB to Structure

Author: QZ Shao <shaoqz@icloud.com>
Date: 2022-09-08
'''
from collections import defaultdict
import itertools
import logging
import os
import string
import pandas as pd
from typing import Dict
import pytest
from biopandas.pdb import PandasPdb

from enzy_htp.core import _LOGGER
from enzy_htp.structure.structure_io.pdb_io import PDBParser
from enzy_htp.structure.structure_io._interface import StructureParserInterface
from enzy_htp.core import file_system as fs
import enzy_htp.chemical as chem
from enzy_htp.structure import (
    Structure,
    Residue,
    Chain,
    structure_from_pdb,
    Atom,
    MetalUnit,
    Ligand,
    Solvent,
)

# pylint: disable=protected-access, invalid-name
_LOGGER.setLevel(logging.DEBUG)
CURRDIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f'{CURRDIR}/../data/'
sp = PDBParser()

@pytest.mark.interface
def test_get_structure():
    '''
    just make sure it wont crash now
    maybe convert back to file and assert
    '''
    pdb_file_path = f'{DATA_DIR}1Q4T_ligand_test.pdb'

    stru = sp.get_structure(pdb_file_path)

def test_check_valid_pdb_good_input():
    '''Good input for the check_valid_pdb() helper method.'''
    # make dummy file
    dummy_pdb = f'{CURRDIR}/dummy.pdb'
    assert not os.path.exists(dummy_pdb)
    fs.write_lines(dummy_pdb, ['line1', 'line2'])
    # test
    assert not sp._check_valid_pdb(dummy_pdb)
    fs.safe_rm(dummy_pdb)
    assert not os.path.exists(dummy_pdb)

def test_check_valid_pdb_bad_input():
    '''Good input for the check_valid_pdb() helper method.'''
    # non pdb file
    txt_file = 'not_pdb.txt'
    assert not os.path.exists(txt_file)
    with pytest.raises(SystemExit) as exe:
        sp._check_valid_pdb(txt_file)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    # pdb that doesn't exist
    pdb_imaginary = 'not_real.pdb'
    with pytest.raises(SystemExit) as exe:
        sp._check_valid_pdb(pdb_imaginary)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    non_ascii_pdb = f'{CURRDIR}/bad_pdb.pdb'
    assert not os.path.exists(non_ascii_pdb)
    fs.write_lines(non_ascii_pdb, ['日本人 中國的'])
    assert os.path.exists(non_ascii_pdb)

    with pytest.raises(SystemExit) as exe:
        sp._check_valid_pdb(non_ascii_pdb)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    fs.safe_rm(non_ascii_pdb)
    assert not os.path.exists(non_ascii_pdb)

def test_get_target_model():
    '''
    test if _get_target_model is getting the correct model
    '''
    pdb_file = f'{DATA_DIR}/3EZB_nmr.pdb'
    # answer 0
    mdl_0_answer = f'{DATA_DIR}3EZB_nmr_mdl_0.pdb'
    answer_0_pdb = PandasPdb()
    answer_0_pdb.read_pdb(mdl_0_answer)
    mdl_0_answer_atom = list(answer_0_pdb.df['ATOM']['atom_number'])
    # answer 1
    mdl_1_answer = f'{DATA_DIR}3EZB_nmr_mdl_1.pdb'
    answer_1_pdb = PandasPdb()
    answer_1_pdb.read_pdb(mdl_1_answer)
    mdl_1_answer_atom = list(answer_1_pdb.df['ATOM']['atom_number'])

    test_pdb = PandasPdb()
    test_pdb.read_pdb(pdb_file)
    target_model_df, target_model_ter_df = sp._get_target_model(test_pdb.df, model=0)
    assert len(target_model_ter_df['record_name']) == 2
    assert list(target_model_df['atom_number']) == mdl_0_answer_atom

    target_model_df, target_model_ter_df = sp._get_target_model(test_pdb.df, model=1)
    assert len(target_model_ter_df['record_name']) == 2
    assert list(target_model_df['atom_number']) == mdl_1_answer_atom

def test_resolve_missing_chain_id_complete_missing():
    test_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = test_mdl_pdb.df['ATOM']
    target_ter_df = test_mdl_pdb.df['OTHERS'].query('record_name == "TER"')
    # answer
    answer_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_answer.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df_chain_ids = list(answer_mdl_pdb.df['ATOM']['chain_id'])

    sp._resolve_missing_chain_id(target_df, target_ter_df)

    assert list(target_df['chain_id']) == answer_df_chain_ids

def test_resolve_missing_chain_id_partial_missing():
    test_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_part.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = test_mdl_pdb.df['ATOM']
    target_ter_df = test_mdl_pdb.df['OTHERS'].query('record_name == "TER"')
    # answer
    answer_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_answer.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df_chain_ids = list(answer_mdl_pdb.df['ATOM']['chain_id'])

    sp._resolve_missing_chain_id(target_df, target_ter_df)

    assert list(target_df['chain_id']) == answer_df_chain_ids

def test_resolve_missing_chain_id_partial_atom_missing():
    test_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_part_atom.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = test_mdl_pdb.df['ATOM']
    target_ter_df = test_mdl_pdb.df['OTHERS'].query('record_name == "TER"')
    # answer
    answer_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_answer.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df_chain_ids = list(answer_mdl_pdb.df['ATOM']['chain_id'])

    sp._resolve_missing_chain_id(target_df, target_ter_df)

    assert list(target_df['chain_id']) == answer_df_chain_ids

def test_resolve_missing_chain_id_redundant_ter():
    '''
    in this case there are one redundant ter
    '''
    test_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_red_ter.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = test_mdl_pdb.df['ATOM']
    target_ter_df = test_mdl_pdb.df['OTHERS'].query('record_name == "TER"')
    # answer
    answer_mdl = f'{DATA_DIR}3EZB_nmr_no_chain_id_answer.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df_chain_ids = list(answer_mdl_pdb.df['ATOM']['chain_id'])

    sp._resolve_missing_chain_id(target_df, target_ter_df)

    assert list(target_df['chain_id']) == answer_df_chain_ids

def test_resolve_missing_chain_id_simple():
    '''Ensuring that the _resolve_missing_chain_id() correctly names new chains.'''

    def get_chains(fname) -> Dict[str, Chain]:
        '''Helper testing method to get the chains from a PDB file.'''
        input_pdb = PandasPdb()
        input_pdb.read_pdb(fname)
        target_model_df, target_model_ter_df = sp._get_target_model(input_pdb.df, 0)
        return target_model_df, target_model_ter_df

    two_chain = f'{DATA_DIR}/two_chain.pdb'
    three_chain = f'{DATA_DIR}/three_chain.pdb'
    four_chain = f'{DATA_DIR}/four_chain.pdb'
    two_df, two_ter_df  = get_chains(two_chain)
    three_df, three_ter_df = get_chains(three_chain)
    four_df, four_ter_df = get_chains(four_chain)
    sp._resolve_missing_chain_id(two_df, two_ter_df)
    sp._resolve_missing_chain_id(three_df, three_ter_df)
    sp._resolve_missing_chain_id(four_df, four_ter_df)

    assert set(two_df['chain_id'].values) == {'A', 'B'}
    assert len(two_df[two_df['chain_id'] == 'A']) == 12
    assert len(two_df[two_df['chain_id'] == 'B']) == 30
    assert set(three_df['chain_id'].values) == {'A', 'B', 'C'}
    assert len(three_df[three_df['chain_id'] == 'A']) == 12
    assert len(three_df[three_df['chain_id'] == 'B']) == 15
    assert len(three_df[three_df['chain_id'] == 'C']) == 14
    assert set(four_df['chain_id'].values) == {'A', 'B', 'C', 'D'}
    assert len(four_df[four_df['chain_id'] == 'A']) == 12
    assert len(four_df[four_df['chain_id'] == 'B']) == 15
    assert len(four_df[four_df['chain_id'] == 'C']) == 7
    assert len(four_df[four_df['chain_id'] == 'D']) == 6

@pytest.mark.long
def test_get_legal_pdb_chain_ids():
    ALL_NAMES = list(string.ascii_uppercase) + list(map(lambda x: str(x), range(50000)))
    result1 = sp._get_legal_pdb_chain_ids([])
    assert set(result1) == set(ALL_NAMES)

    ALL_NAMES.remove('A')
    result3 = sp._get_legal_pdb_chain_ids(['A'])
    assert set(result3) == set(ALL_NAMES)

def test_resolve_alt_loc_first():
    '''test resolve alt loc recored demoed in 3NIR'''
    test_mdl = f'{DATA_DIR}3NIR_alt_loc_test.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = pd.concat((test_mdl_pdb.df['ATOM'],test_mdl_pdb.df['HETATM']), ignore_index=True)
    print(target_df)
    # answer
    answer_mdl = f'{DATA_DIR}3NIR_alt_loc_answer_A.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df = pd.concat((answer_mdl_pdb.df['ATOM'],answer_mdl_pdb.df['HETATM']), ignore_index=True)

    sp._resolve_alt_loc(target_df)

    assert list(target_df['atom_number']) == list(answer_df['atom_number'])

def test_resolve_alt_loc_keep_B():
    '''test resolve alt loc recored demoed in 3NIR'''
    test_mdl = f'{DATA_DIR}3NIR_alt_loc_test.pdb'
    test_mdl_pdb = PandasPdb()
    test_mdl_pdb.read_pdb(test_mdl)
    target_df = pd.concat((test_mdl_pdb.df['ATOM'],test_mdl_pdb.df['HETATM']), ignore_index=True)
    print(target_df)
    # answer
    answer_mdl = f'{DATA_DIR}3NIR_alt_loc_answer_B.pdb'
    answer_mdl_pdb = PandasPdb()
    answer_mdl_pdb.read_pdb(answer_mdl)
    answer_df = pd.concat((answer_mdl_pdb.df['ATOM'],answer_mdl_pdb.df['HETATM']), ignore_index=True)

    sp._resolve_alt_loc(target_df, keep='B')

    assert list(target_df['atom_number']) == list(answer_df['atom_number'])

def test_build_atom():
    '''
    a weak teat of _build_atom that insure no missing residue
    '''
    pdb_file_path = f'{DATA_DIR}1Q4T_atom_res_ch_build_test.pdb'
    input_pdb = PandasPdb()
    input_pdb.read_pdb(pdb_file_path)
    target_df = pd.concat((input_pdb.df['ATOM'], input_pdb.df['HETATM']), ignore_index=True)

    atom_mapper: Dict[tuple, Atom] = sp._build_atoms(target_df)
    df_residue = target_df.groupby(['residue_number', 'chain_id'])
    assert len(atom_mapper) == len(df_residue)

def test_build_residue():
    '''
    a weak teat of _build_atom that insure no missing residue
    just make sure the number of chains and the idx_change_mapper is correct
    and ligand is found
    also test for _categorize_residue ligand case
    '''
    pdb_file_path = f'{DATA_DIR}1Q4T_atom_res_ch_build_test.pdb'
    input_pdb = PandasPdb()
    input_pdb.read_pdb(pdb_file_path)
    target_df = pd.concat((input_pdb.df['ATOM'], input_pdb.df['HETATM']), ignore_index=True)
    atom_mapper: Dict[tuple, Atom] = sp._build_atoms(target_df)

    res_mapper, idx_change_mapper = sp._build_residues(atom_mapper)
    assert set(res_mapper.keys()) == set(['A','B','C','D'])
    assert idx_change_mapper == {('A', 152): ('C', 152), ('A', 153): ('C', 153), ('A', 370): ('C', 370), 
         ('A', 371): ('C', 371), ('A', 372): ('C', 372), ('A', 373): ('C', 373), ('A', 374): ('C', 374), 
         ('A', 375): ('C', 375), ('A', 376): ('C', 376), ('B', 152): ('D', 152), ('B', 153): ('D', 153), 
         ('B', 371): ('D', 371), ('B', 372): ('D', 372), ('B', 373): ('D', 373), ('B', 374): ('D', 374), 
         ('B', 375): ('D', 375), ('B', 376): ('D', 376), ('B', 377): ('D', 377), ('B', 378): ('D', 378)}
    all_residue = list(itertools.chain.from_iterable(res_mapper.values()))
    assert len(all_residue) == len(atom_mapper)
    assert len(list(filter(lambda x: x.rtype is chem.ResidueType.LIGAND, all_residue))) == 2

def test_categorize_residue_canonical():
    pdb_file_path = f'{DATA_DIR}/two_chain.pdb'
    input_pdb = PandasPdb()
    input_pdb.read_pdb(pdb_file_path)
    target_df = input_pdb.df['ATOM']
    atom_mapper = sp._build_atoms(target_df)
    res_mapper = defaultdict(list)
    for res_key, atoms in atom_mapper.items():
        res_mapper[res_key[0]].append(Residue(int(res_key[1]), res_key[2] ,atoms))

    sp._categorize_pdb_residue(res_mapper)
    all_residue = list(itertools.chain.from_iterable(res_mapper.values()))
    assert len(list(filter(lambda x: x.rtype is not chem.ResidueType.CANONICAL, all_residue))) == 0

def test_categorize_residue_metal():
    pdb_file_path = f'{DATA_DIR}/just_metal.pdb'
    input_pdb = PandasPdb()
    input_pdb.read_pdb(pdb_file_path)
    row = input_pdb.df['HETATM'].iloc[0]
    zn_atom = Atom(row)
    res_mapper = defaultdict(list)
    res_key = (row['chain_id'].strip(), row['residue_number'], row['residue_name'].strip(), row['record_name'].strip())
    res_mapper[res_key[0]].append(Residue(int(res_key[1]), res_key[2] ,[zn_atom]))

    sp._categorize_pdb_residue(res_mapper)
    all_residue = list(res_mapper.values())[0]
    assert all_residue[0].rtype is chem.ResidueType.METAL

def test_categorize_residue_noncanonical():
    pdb_file_path = f'{DATA_DIR}/5JT3_noncanonical_test.pdb'
    input_pdb = PandasPdb()
    input_pdb.read_pdb(pdb_file_path)
    target_df = pd.concat((input_pdb.df['ATOM'], input_pdb.df['HETATM']), ignore_index=True)
    atom_mapper = sp._build_atoms(target_df)
    res_mapper = defaultdict(list)
    for res_key, atoms in atom_mapper.items():
        res_mapper[res_key[0]].append(Residue(int(res_key[1]), res_key[2] ,atoms))

    sp._categorize_pdb_residue(res_mapper)
    all_residue = list(itertools.chain.from_iterable(res_mapper.values()))
    assert len(list(filter(lambda x: x.rtype is chem.ResidueType.NONCANONICAL, all_residue))) == 1

# def test_build_chains():
#     '''Ensuring the structure_parser.build_chains() method correctly aggregates Residue() objects into Chain() objects.'''
#     pdb_file = f'{DATA_DIR}/four_chain.pdb'
#     reader = PandasPdb()
#     reader.read_pdb(pdb_file)
#     res_mapper: Dict[str, Residue] = sp.build_residues(
#         pd.concat((reader.df['ATOM'], reader.df['HETATM']))
#     )
#     chain_mapper: Dict[str, Chain] = sp.build_chains(res_mapper)

#     assert set(chain_mapper.keys()) == {'A', 'B', 'C', 'D'}
#     assert len(chain_mapper['A']) == 2
#     print(chain_mapper['B'].residues())
#     assert len(chain_mapper['B']) == 3
#     assert len(chain_mapper['C']) == 1
#     assert len(chain_mapper['D']) == 1

#     atom_counts = [12, 15, 7, 6]
#     for ac, chain in zip(atom_counts, chain_mapper.values()):
#         assert chain.num_atoms() == ac
#         for res in chain.residues():
#             assert isinstance(res, Residue)

# def test_build_chains_wANISOU(): # TODO(shaoqz): fix this by fixing missing chain id
#     '''test if works well with PDB that contain ANISOU records'''
#     pdb_file = f'{DATA_DIR}/four_chain_no_id_ANISOU.pdb'
#     reader = PandasPdb()
#     reader.read_pdb(pdb_file)
#     res_mapper: Dict[str, Residue] = sp.build_residues(
#         pd.concat((reader.df['ATOM'], reader.df['HETATM']))
#     )
#     chain_mapper: Dict[str, Chain] = sp.build_chains(res_mapper)
#     for key in chain_mapper:
#         print(key)

# def test_structure_from_pdb_bad_input():
#     '''Checking that the main method structure_parser.structure_from_pdb() fails for bad input.'''
#     with pytest.raises(SystemExit) as exe:
#         sp.structure_from_pdb('dne.pdb')

#     assert exe
#     assert exe.type == SystemExit
#     assert exe.value.code == 1


# def test_structure_from_pdb_simple():
#     '''Checking that the main method structure_parser.structure_from_pdb() works for simple cases.'''
#     pdb_name = f'{DATA_DIR}/two_chain.pdb'
#     structure: Structure = structure_from_pdb(pdb_name)

#     chain_A_target = ['A.ALA.10', 'A.THR.11']
#     chain_B_target = ['B.GLY.12', 'B.GLY.13', 'B.ASN.14', 'B.LEU.15', 'B.PRO.16']
#     assert structure.num_chains == 2
#     (chain_A, chain_B) = structure.chains
#     assert chain_A_target == list(map(str, chain_A))
#     assert chain_B_target == list(map(str, chain_B))


# def test_structure_from_pdb_mixed_case():
#     '''Checking that the main method structure_parser.structure_from_pdb() works for cases with mixed Residue() types..'''
#     mixed_pdb = f'{DATA_DIR}/mixed_residues.pdb'
#     structure: Structure = structure_from_pdb(mixed_pdb)
#     assert structure.num_chains == 5
#     all_residues = structure.residues

#     assert all_residues[0].is_canonical()
#     assert all_residues[1].is_canonical()
#     assert all_residues[2].is_canonical()
#     assert all_residues[3].is_canonical()
#     assert all_residues[4].is_ligand()
#     assert all_residues[5].is_metal()
#     assert all_residues[6].is_solvent()

#     assert isinstance(all_residues[0], Residue)
#     assert isinstance(all_residues[1], Residue)
#     assert isinstance(all_residues[2], Residue)
#     assert isinstance(all_residues[3], Residue)
#     assert isinstance(all_residues[4], Ligand)
#     assert isinstance(all_residues[5], MetalUnit)
#     assert isinstance(all_residues[6], Solvent)


# def test_ligand_from_pdb():
#     '''Checking that the method structure_parser.ligand_from_pdb() works for a simple case and returns a Ligand().'''
#     ligand_pdb = f'{DATA_DIR}/just_ligand.pdb'
#     ligand = sp.ligand_from_pdb(ligand_pdb)
#     assert ligand.is_ligand()
#     assert len(ligand.atoms) == 7
#     assert ligand.name == 'FAH'


# def test_ligand_from_pdb_bad_input():
#     '''Checking that the method structure_parser.ligand_from_pdb() fails for a bad input.'''
#     with pytest.raises(SystemExit) as exe:
#         sp.ligand_from_pdb('dne.pdb')

#     assert exe
#     assert exe.type == SystemExit
#     assert exe.value.code == 1

# #TODO(CJ): add tests for structure_parser.get_ligand_name()