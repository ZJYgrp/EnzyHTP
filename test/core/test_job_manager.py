from core.job_manager import *

command_2_run = ['g16 < xxx.gjf > xxx.out']
env_setting =  ['module load GCC/6.4.0-2.28  OpenMPI/2.1.1', 
                'module load Amber/17-Python-2.7.14', 
                'module unload Python/2.7.14 numpy/1.13.1-Python-2.7.14']
res_keyword = { 'core_type' : 'cpu',
                'node_cores' : '24',
                'job_name' : 'job_name',
                'partition' : 'production',
                'mem_per_core' : '4G',
                'walltime' : '24:00:00',
                'account' : 'xxx'}

def test_submit_by_keyword():
    job = ClusterJob('test_g16', cluster= accre.Accre()) # create a job first so that can config with useful cluster presets
    job.config(
        command = command_2_run,
        env_setting = env_setting,
        res_keyword = res_keyword
    )
    job.submit(debug=1, script_path='./test/core/test_file/test.cmd')

