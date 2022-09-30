"""Testing the enzy_htp.structure.Atom class.

Author: Chris Jurich <chris.jurich@vanderbilt.edu
Date: 2022-03-19
"""
import itertools
import os
import numpy as np
import pandas as pd
from typing import List
from copy import deepcopy
import pytest
from biopandas.pdb import PandasPdb

from enzy_htp.core.file_system import lines_from_file
from enzy_htp.structure.atom import Atom
from enzy_htp.structure.structure_io import PDBParser

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f"{CURR_DIR}/data/"

def test_deepcopy():
    """test the hehavior of copy.deepcopy on Atom() under a Structure()
    context"""
    stru = PDBParser().get_structure(f"{DATA_DIR}12E8_small_four_chain.pdb")
    atom_list = stru[0][0][1:3] + stru[0][1][1:2] # target for deepcopy
    new_list = deepcopy(atom_list)
    # ensure the list is new
    assert id(atom_list) != id(new_list)
    # ensure every atom is new
    for i, j in zip(atom_list, new_list):
        assert id(i) != id(j)
    # ensure parent of every atom is None
    assert all(i.parent is None for i in new_list)

# TODO recover when need
@pytest.mark.TODO
def test_distance():
    """Making sure that the .distance() method works."""
    TEST_PDB_NAME = f"{CURR_DIR}/data/atom_test_pdb.pdb"
    RAW_ATOMS: pd.DataFrame = PandasPdb().read_pdb(TEST_PDB_NAME).df["ATOM"]
    atoms: List[Atom] = list(map(lambda pr: Atom(**pr[1]), RAW_ATOMS.iterrows()))
    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=0, y_coord=0, z_coord=1)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=0, y_coord=1, z_coord=0)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=1, y_coord=0, z_coord=0)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=-1, y_coord=0, z_coord=0)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=0, y_coord=-1, z_coord=0)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=0, y_coord=0, z_coord=-1)
    assert np.isclose(atom1.distance(atom2), 1)
    assert np.isclose(atom2.distance(atom1), 1)

    atom1 = Atom(x_coord=0, y_coord=0, z_coord=0)
    atom2 = Atom(x_coord=0, y_coord=0, z_coord=0)
    assert np.isclose(atom1.distance(atom2), 0)
    assert np.isclose(atom2.distance(atom1), 0)
