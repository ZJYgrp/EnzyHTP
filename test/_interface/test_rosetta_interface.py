"""Testing enzy_htp._interface.rosetta_interface.py
Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2024-02-16
"""
from pathlib import Path
import pickle
import re
import numpy as np
import pytest
import os

from enzy_htp.core.clusters.accre import Accre
import enzy_htp.core.file_system as fs
from enzy_htp._config.armer_config import ARMerConfig
from enzy_htp import PDBParser
from enzy_htp import interface, config

DATA_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/data/"
WORK_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/work_dir/"
sp = PDBParser()
ri = interface.rosetta

def test_relax_w_stru():
    """as said in the name. make sure relax works Structure() input."""
    config.rosetta.RELAX = "$ROSETTA3/source/bin/relax.mpi.linuxgccrelease"
    config.system.MPI_EXECUTABLE = "mpiexec"
    test_stru = sp.get_structure(f"{DATA_DIR}KE_07_R7_2_S.pdb")
    scores = ri.relax(
        test_stru,
        nstruct=3,
        constrain_relax_to_start_coords=False,
        coord_constrain_sidechains=False,
        ramp_constraints=False,
        use_cartesian=True,
        scorefxn="ref2015_cart",
        cluster_job_config={
            "cluster" : Accre(),
            "res_keywords" : {
                "partition" : "production",
                "node_cores" : "24",
                "account" : "yang_lab",
                "walltime" : "10:00:00",
            }
        },
        delete_crash=False,
    )
    assert len(scores) == 3
    for pdb_file in scores["description"]:
        assert Path(pdb_file).exists()

def test_get_ddg_fold():
    """as said in the name."""
    test_ddg_file = f"{DATA_DIR}test.ddg"
    ddg_engine = ri.build_cartesian_ddg_engine()
    result = ddg_engine.get_ddg_fold(test_ddg_file)
    assert np.isclose(result, 12.069600000000037, atol=1e-6)
