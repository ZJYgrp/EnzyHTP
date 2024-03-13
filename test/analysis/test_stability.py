"""Testing enzy_htp.analysis.stability.py

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2024-03-12"""
import os
import numpy as np

from enzy_htp.analysis import ddg_fold_of_mutants
from enzy_htp import PDBParser
from enzy_htp.mutation import assign_mutant
from enzy_htp.core.clusters.accre import Accre

DATA_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/data/"
STRU_DATA_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/../test_data/diversed_stru/"
WORK_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/work_dir/"
sp = PDBParser()

def test_ddg_fold_of_mutants():
    """as name.
    use data from EnzyHTP 1.0 as answer"""
    test_stru = sp.get_structure(f"{STRU_DATA_DIR}KE_07_R7_2_S.pdb")
    mutant_space = assign_mutant(
        test_stru,
        "{E24V,K162I,R163L},{S29K,E24V,K162L,R163L}"
    )
    result = ddg_fold_of_mutants(
        test_stru,
        mutant_space,
        cluster_job_config = {
            "cluster" : Accre(),
            "res_keywords" : {
                "partition" : "production",
                "account" : "yang_lab",
            }
        },
        work_dir=WORK_DIR,
    )

    mut_1 = tuple(mutant_space[0])
    mut_2 = tuple(mutant_space[1])
    assert np.isclose(result[mut_1], -5.8368, atol=1)
    assert np.isclose(result[mut_2], -6.4792, atol=1)
