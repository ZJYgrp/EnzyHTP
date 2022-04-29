from random import choice
import os
import pytest

from Class_PDB import *
from helper import is_empty_dir
from AmberMaps import Resi_map2

test_file_paths = []
test_file_dirs = []

@pytest.mark.mutation
def _random_gen_good_MutaFlag_for_test(stru, abbr=0):
    '''
    this should be seperate from Add_MutaFlag
    '''
    if abbr:
        chain = stru.chains[0]
    else:
        chain = choice(stru.chains)
    residue = choice(chain.residues)
    chain_id = chain.id
    residue_name = Resi_map2[residue.name]
    residue_id = str(residue.id)
    target_residue_name = choice(Resi_list[:-1])

    if abbr:
        test_flag = residue_name + residue_id + target_residue_name
    else:
        test_flag = residue_name + chain_id + residue_id + target_residue_name
    
    correct_answer = (residue_name, chain_id, residue_id, target_residue_name)

    return test_flag, correct_answer

# how should we determine how many types of input should one function contain.
@pytest.mark.mutation
def test_Add_MutaFlag_good_assign_mutaflag_canonical():
    '''
    test assign a specific reasonable mutation to a canonical amino acid
    '''
    pdb_obj = PDB('./test/testfile_Class_PDB/FAcD.pdb')  # what should we do if there's a general input for all test?
    # create an random input of "XA##B"
    pdb_obj.get_stru()

    # test single input
    test_flag_0, correct_answer = _random_gen_good_MutaFlag_for_test(pdb_obj.stru)
    print('test_Add_MutaFlag_assign_good_mutaflag_canonical(): MutaFlag used for test: ' + test_flag_0)
    pdb_obj.Add_MutaFlag(test_flag_0)
    assert pdb_obj.MutaFlags == [correct_answer]

    pdb_obj.MutaFlags = []
    # test list input
    test_flag_list = []
    correct_answer = []
    for i in range(10):  # pylint: disable:=unused-variable
        flag_i, answer_i = _random_gen_good_MutaFlag_for_test(pdb_obj.stru)
        test_flag_list.append(flag_i)
        correct_answer.append(answer_i)
    print('test_Add_MutaFlag_assign_good_mutaflag_canonical(): MutaFlag used for test:', test_flag_list)
    pdb_obj.Add_MutaFlag(test_flag_list)
    assert pdb_obj.MutaFlags == correct_answer

    pdb_obj.MutaFlags = []
    # test abbreviated input
    test_flag_1, correct_answer = _random_gen_good_MutaFlag_for_test(pdb_obj.stru, abbr=1)
    print('test_Add_MutaFlag_assign_good_mutaflag_canonical(): MutaFlag used for test: ' + test_flag_1)
    pdb_obj.Add_MutaFlag(test_flag_1)
    assert pdb_obj.MutaFlags == [correct_answer]

@pytest.mark.mutation
def test_Add_MutaFlag_good_random():
    '''
    test random generate a mutation
    '''
    pdb_obj = PDB('./test/testfile_Class_PDB/FAcD.pdb')  # what should we do if there's a general input for all test?

    pdb_obj.Add_MutaFlag('r')

    assert pdb_obj.MutaFlags # How should we test this? It's just write the same thing

# good non-canonical
# bad input wrong original residue
# bad input chain index out of range
# bad input residue index out of range
# bad input self mutation
# very-bad input random character
# very-bad input other obj type

# good PDB multichains
# good PDB ligand
# good PDB non-c AA
# good PDB solvent
# bad PDB

@pytest.mark.md
def test_PDB2FF_keep():
    pdb_obj = PDB('./test/testfile_Class_PDB/FAcD.pdb', wk_dir='./test/testfile_Class_PDB')
    prm_files = pdb_obj.PDB2FF(local_lig=1)
    test_file_paths.extend(prm_files) #clean up record
    test_file_paths.extend([pdb_obj.cache_path+'/leap.in', 
                            './tmp/tmp.inpcrd', 
                            pdb_obj.cache_path+'/leap.out',
                            pdb_obj.lig_dir+'/cache/ligand_temp2.pdb',
                            pdb_obj.lig_dir+'/cache/ligand_temp3.pdb',
                            pdb_obj.lig_dir+'/cache/ligand_temp.mol2',
                            './leap.log'])
    test_file_dirs.extend([pdb_obj.lig_dir+'/cache'])

    for f in prm_files:
        assert os.path.isfile(f)
        assert os.path.getsize(f) != 0 # prmtop will be 0K if failed

    assert len(pdb_obj.prepi_path) != 0

@pytest.mark.md
@pytest.mark.accre
def test_pdbmd_with_job_manager():
    pass

@pytest.mark.qm
@pytest.mark.accre
def test_pdb2qmcluster_with_job_manager():
    pass

### utilities ###
@pytest.mark.clean
def test_clean_files():
    # clean files
    for f_path in test_file_paths:
        if os.path.isfile(f_path):
            os.remove(f_path)
            print(f'removed {f_path}')
        else:
            print(f'no such file {f_path}')
            
@pytest.mark.clean            
def test_clean_dirs():
    # clean dirs
    for f_dir in test_file_dirs:
        if is_empty_dir(f_dir) != 2:
            if is_empty_dir(f_dir):
                os.removedirs(f_dir)
                print(f'removed {f_dir}')
            else:
                print(f'{f_dir} is not empty. wont rm it')