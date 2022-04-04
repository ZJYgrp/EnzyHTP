"""Testing the enzy_htp.structure.structure_parser function.

Author: Chris Jurich <chris.jurich@vanderbilt.edu
Date: 2022-03-31
"""
import os
import pytest
import string
import pandas as pd
from typing import Dict
from biopandas.pdb import PandasPdb

from enzy_htp.core import file_system as fs
from enzy_htp.structure import structure_parser as sp
from enzy_htp.structure import Structure,Residue,Chain, structure_from_pdb


CURRDIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f"{CURRDIR}/data/"

def test_check_valid_pdb_good_input():
    """Good input for the check_valid_pdb() helper method."""
    dummy_pdb = f"{CURRDIR}/dummy.pdb"
    assert not os.path.exists(dummy_pdb)
    fs.write_lines(dummy_pdb, ["line1", "line2"])
    assert not sp.check_valid_pdb(dummy_pdb)
    fs.safe_rm(dummy_pdb)
    assert not os.path.exists(dummy_pdb)


def test_check_valid_pdb_bad_input():
    """Good input for the check_valid_pdb() helper method."""
    # non pdb file
    txt_file = "not_pdb.txt"
    assert not os.path.exists(txt_file)
    with pytest.raises(SystemExit) as exe:
        sp.check_valid_pdb(txt_file)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    # pdb that doesn't exist
    pdb_imaginary = "not_real.pdb"
    with pytest.raises(SystemExit) as exe:
        sp.check_valid_pdb(pdb_imaginary)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    non_ascii_pdb = f"{CURRDIR}/bad_pdb.pdb"
    assert not os.path.exists(non_ascii_pdb)
    fs.write_lines(non_ascii_pdb, ["日本人 中國的"])
    assert os.path.exists(non_ascii_pdb)

    with pytest.raises(SystemExit) as exe:
        sp.check_valid_pdb(non_ascii_pdb)

    assert exe
    assert exe.type == SystemExit
    assert exe.value.code == 1

    fs.safe_rm(non_ascii_pdb)
    assert not os.path.exists(non_ascii_pdb)


def test_legal_chain_names():
    """Making sure all legal chains are created given a starting Residue() mapper."""
    ALL_NAMES = list(string.ascii_uppercase)
    result1 = sp.legal_chain_names(dict())
    assert set(result1) == set(ALL_NAMES)

    dummy_mapper = dict(zip(ALL_NAMES, range(len(ALL_NAMES))))
    result2 = sp.legal_chain_names(dummy_mapper)
    assert not result2

    ALL_NAMES.remove("A")
    dummy_mapper = dict(zip(ALL_NAMES, range(len(ALL_NAMES))))
    result3 = sp.legal_chain_names(dummy_mapper)
    assert result3 == ["A"]


def test_name_chains():
    """Ensuring that the name_chains() correctly names new chains."""
    def get_chains( fname ) -> Dict[str,Chain]:
        """Helper testing method to get the chains from a PDB file."""
        reader = PandasPdb()
        reader.read_pdb( fname )
        res_mapper : Dict[str, Residue] = sp.build_residues( reader.df['ATOM'] ) 
        chain_mapper : Dict[str, Chain] = sp.build_chains( res_mapper )
        return chain_mapper
    two_chain = f"{DATA_DIR}/two_chain.pdb"
    three_chain = f"{DATA_DIR}/three_chain.pdb"
    four_chain = f"{DATA_DIR}/four_chain.pdb"
    two_mapper : Dict[str, Chain] = get_chains( two_chain )
    three_mapper : Dict[str, Chain] = get_chains( three_chain )
    four_mapper : Dict[str, Chain] = get_chains( four_chain )
    two_mapper = sp.name_chains( two_mapper )
    three_mapper = sp.name_chains( three_mapper )
    four_mapper = sp.name_chains( four_mapper )

    assert set(two_mapper.keys()) == {"A","B"}
    assert set(three_mapper.keys()) == {"A","B","C"}
    assert set(four_mapper.keys()) == {"A","B","C","D"}

def test_name_chains_already_named():
    """Ensuring that the name_chains() does not changed already named chains."""
    already_named = {'A':[],'B':[]}
    already_named = sp.name_chains( already_named )
    assert set(already_named.keys()) == {'A','B'}


def test_categorize_residues():
    assert False
