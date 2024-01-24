"""Testing the PrmtopParser class in the enzy_htp.structure.structure_io.prmtop_io

Author: QZ Shao <shaoqz@icloud.com>
Date: 2024-01-23
"""
from pathlib import Path

import pytest

import enzy_htp.core.file_system as fs
from enzy_htp.structure.structure_io import PrmtopParser

BASE_DIR = Path(__file__).absolute().parent
DATA_DIR = f"{BASE_DIR}/../data"

def test_prmtop_parser_get_stru():
    """make sure function works as expected"""
    test_prmtop = f"{DATA_DIR}/KE_07_R7_2_S_10f.prmtop"
    test_stru = PrmtopParser().get_structure(test_prmtop)
    assert test_stru.residues

def test_parse_version():
    """test using content from an example file: {DATA_DIR}/KE_07_R7_2_S_10f.prmtop"""
    test_content = "%VERSION  VERSION_STAMP = V0001.000  DATE = 01/03/24 16:27:03                  \n"
    assert PrmtopParser._parse_version(test_content) == {
        "VERSION_STAMP" : "V0001.000",
        "DATE" : "01/03/24 16:27:03",
    }

def test_parse_title():
    """test using content from an example file: {DATA_DIR}/KE_07_R7_2_S_10f.prmtop"""
    test_content = " TITLE                                                                     \n%FORMAT(20a4)                                                                   \ndefault_name                                                                    \n"
    assert PrmtopParser._parse_title(test_content) == {
        "TITLE" : "default_name"
    }

def test_parse_prmtop_file():
    """test using an example file"""
    test_prmtop = f"{DATA_DIR}/KE_07_R7_2_S_10f.prmtop"
    
    PrmtopParser._parse_prmtop_file(test_prmtop)

# TODO
def test_parse_prmtop():
    """Testing that PrmtopParser._parse_prmtop_file() method works. It essentially loads the supplied
    prmtop file and ensures that the correct number of items are extracted for the majority of keys.
    """
    data = PrmtopParser._parse_prmtop_file(f"{DATA_DIR}/prmtop_1")

    assert data

    n_atoms: int = 23231
    num_bond: int = 85
    num_ang: int = 186
    n_ptra: int = 190
    n_types: int = 19
    n_bond_h: int = 21805
    n_bond_a: int = 1450
    n_thet: int = 3319
    n_phi: int = 6138
    n_phi_h: int = 6551
    nnb: int = 43036
    n_phb: int = 1
    n_res: int = 6967

    assert len(data['ATOM_NAME']) == n_atoms
    assert len(data['CHARGE']) == n_atoms
    assert len(data['ATOMIC_NUMBER']) == n_atoms
    assert len(data['MASS']) == n_atoms
    assert len(data['ATOM_TYPE_INDEX']) == n_atoms
    assert len(data['NUMBER_EXCLUDED_ATOMS']) == n_atoms
    assert len(data['NONBONDED_PARM_INDEX']) == n_types**2
    assert len(data['RESIDUE_LABEL']) == n_res
    assert len(data['RESIDUE_POINTER']) == n_res
    assert len(data['BOND_FORCE_CONSTANT']) == num_bond
    assert len(data['BOND_EQUIL_VALUE']) == num_bond
    assert len(data['ANGLE_FORCE_CONSTANT']) == num_ang
    assert len(data['ANGLE_EQUIL_VALUE']) == num_ang
    assert len(data['DIHEDRAL_FORCE_CONSTANT']) == n_ptra
    assert len(data['DIHEDRAL_PERIODICITY']) == n_ptra
    assert len(data['DIHEDRAL_PHASE']) == n_ptra
    assert len(data['SCEE_SCALE_FACTOR']) == n_ptra
    assert len(data['SOLTY']) == 52
    assert len(data['LENNARD_JONES_ACOEF']) == (n_types * (n_types + 1)) / 2
    assert len(data['LENNARD_JONES_BCOEF']) == (n_types * (n_types + 1)) / 2
    assert len(data['BONDS_INC_HYDROGEN']) == 3 * n_bond_h
    assert len(data['BONDS_WITHOUT_HYDROGEN']) == 3 * n_bond_a
    assert len(data['ANGLES_INC_HYDROGEN']) == 4 * n_thet
    assert len(data['DIHEDRALS_INC_HYDROGEN']) == 5 * n_phi_h
    assert len(data['DIHEDRALS_WITHOUT_HYDROGEN']) == 5 * n_phi
    assert len(data['EXCLUDED_ATOMS_LIST']) == nnb
    assert len(data['HBOND_ACOEF']) == n_phb
    assert len(data['HBOND_BCOEF']) == n_phb
    assert len(data['HBCUT']) == n_phb
    assert len(data['AMBER_ATOM_TYPE']) == n_atoms
    assert len(data['TREE_CHAIN_CLASSIFICATION']) == n_atoms
    assert len(data['JOIN_ARRAY']) == n_atoms
    assert len(data['IROTAT']) == n_atoms
    assert len(data['RADII']) == n_atoms


def test_parse_prmtop_no_file():
    """Checking that PrmtopParser._parse_prmtop_file() throws an error if the listed file does not exist."""

    dne = Path('./dne')

    assert not dne.exists()

    with pytest.raises(ValueError) as exe:
        PrmtopParser._parse_prmtop_file(dne)

    assert exe

