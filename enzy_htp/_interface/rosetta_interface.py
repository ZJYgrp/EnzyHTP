"""Defines a RosettaInterface class that serves as a bridge for enzy_htp to utilize the Rosetta modelling
suite. Uses the RosettaConfig class found in enzy_htp/_config/rosetta_config.py. Supported operations include mutation,
relaxation (minimization), scoring, ligand parameterization, and the ability to use RosettaScripts.
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2023-03-28
"""
from __future__ import annotations
import copy
import os
import re
import shutil
from pathlib import Path
from copy import deepcopy
from subprocess import CompletedProcess, SubprocessError
from plum import dispatch
from xml.dom import minidom
import xml.etree.cElementTree as ET
from collections import namedtuple
from typing import Any, Dict, List, Tuple, Set, Union, Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from enzy_htp import config as eh_config
from enzy_htp.mutation_class.mutation import Mutation
from enzy_htp.structure import Structure, PDBParser, Mol2Parser, Ligand
from enzy_htp.structure.structure_operation import remove_non_peptide
from enzy_htp.structure.structure_constraint import StructureConstraint, ResiduePairConstraint
from enzy_htp._config.rosetta_config import RosettaConfig, default_rosetta_config
from enzy_htp.core import _LOGGER
from enzy_htp.core import file_system as fs
from enzy_htp.core import env_manager as em
from enzy_htp.core.job_manager import ClusterJob
from enzy_htp.core.exception import RosettaError

from .base_interface import BaseInterface
from .handle_types import ddGFoldEngine, ddGResultEgg, ModelingEngine, ModelingResultEgg

class RosettaOptions:
    """Holds options for running generic functions in the Rosetta molecular modelling suite. Serves
    as a dict() and supports [] operator usage so that options can be set and then subsequently accessed
    or written to a file. Allows namespace nesting with the ':' character.

    Attributes:
        data_: The dict() holding various settings.
        script_vars_: A dict() with a special case of (key, value) pairs that defines script variables for a RosettaScripts run.
    """
    
    def __init__(self):
        """Simplistic constructor that initializes the data_ and script_vars_ dict()'s"""

        self.data_ = dict()
        self.script_vars_ = dict()


    def convert_script_vars_(self) -> None:
        """Private method which converts the script variables to a 'parser:script_vars' variable."""

        if not self.script_vars_:
            return

        result = str()

        for key_name, value in self.script_vars.items():
            result += f" {key_name}={self.convert_value_(value)}"

        self['parser:script_vars'] = result


    @property
    def script_vars(self) -> Dict:  
        """Getter for the dict() of script variables in this options object."""
        return self.script_vars_

    def __setitem__(self, key:str, value:Any) -> None:
        """Allows bracket operator setting for the options, with support for namespace
        nesting with the ':' character.

        Args:
            key: Name of the key/variable name as a str().
            value: Value of the variable. Must be able to be converted to a str().

        Returns:
            Nothing.
        """
        tks:List[str] = key.split(':')
        ptr = self.data_
        n_tks = len(tks)
        for tidx, tt in enumerate(tks):
            if tidx == n_tks - 1 :
                break
            new_ptr = ptr.get(tt, None)
            if not new_ptr:
                ptr[tt] = dict()
                new_ptr = ptr[tt]

            ptr = new_ptr

        ptr[tks[-1]] = value


    def __getitem__(self, key:str) -> Any:
        """Allows bracket operating getting for the options, with support for namespace
        nesting with the ':' character. Raises error if unsupported key.

        Args:
            key: Name of the variable to be accessed as a str().

        Returns:
            The value associated with the key.
        """
        tks:List[str] = key.split(':')
        ptr = self.data_
        tks = list(reversed(tks))
        tt = tks.pop()
        while tks:
            ptr = ptr.get(tt)
            if ptr is None:
                err_msg:str = f"No stored variable '{key}'. Encountered problem with namespace '{tt}'."
                _LOGGER.error(err_msg)
                raise TypeError( err_msg )
                                
            tt = tks.pop()
        
        result = ptr.get(tt)
        if result is None:
            err_msg:str = f"No stored variable '{key}'. Encountered problem with namespace '{tt}'."
            _LOGGER.error(err_msg)
            raise TypeError( err_msg )

        return result


    def convert_value_(self, value:Any) -> str:
        """Helper method that converts an arbitrary value to a str() supported by Rosetta.

        Args:
            value: The Any-type value to convert.

        Returns:
            The supplied type converted to a str().
        """
        
        if isinstance(value, list):
            return ' '.join(map(lambda vv: self.convert_value_(vv), value))

        if isinstance(value, bool):
            if value == True:
                return 'true'
            else:
                return 'false'

        if isinstance(value, str):
            return f"'{value}'"

        return f"{value}"


    def to_file(self, fname:str) -> str:
        """Writes the options to a file that can be parsed at the commandline.

        Args: 
            fname: The filename as a str() to write the options to.

        Returns:
            The name of the written options filepath.
        """
        self.convert_script_vars_()
        depth = 0
        lines = list()
        self.traverse_options_(self.data_, lines, depth)
        fs.write_lines(fname, lines)
        return fname

    def traverse_options_(self, data:Dict, lines:List[str], depth:int) -> None:
        """Helper method that traverses the options in the dict() and converts
        them into lines that can be written to a file.

        Args:
            data: The data Dict() with (key, value) pairs to convert to lines.
            lines: The lines to add the (key, value) pairs.
            depth: What is the starting indent to use here?
        
        Returns:
            Nothing.
        """
        insert:str = ' '*4*depth
        for key_name, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{insert}-{key_name}")
                self.traverse_options_(value,  lines, depth+1)
            else:
                if key_name == 'script_vars':
                    lines.append(f"{insert}-{key_name} {value}")
                else:
                    lines.append(f"{insert}-{key_name} {self.convert_value_(value)}")

class RosettaScriptsElement:

    def __init__(self, tag:str, **kwargs):

        self.tag_ = tag
        self.attrib = dict()
        self.children_ = list()


        children_temp = kwargs.pop('children', None)

        if children_temp:
            self.children_ = children_temp

        for k, v in kwargs.items():
            self.attrib[k] = v

    @property
    def children(self) -> List["RosettaScriptsElement"]:
        return self.children_

    @property
    def tag(self) -> str:
        return self.tag_


    def has_children(self) -> bool:
        return len(self.children_) 

    def add_child(self, child: "RosettaScriptsElement") -> None:

        self.children_.append( child )

    def to_lines(self, offset:int = 2) -> List[str]:

        prefix:str=' '*offset*4
        content:List[str] = []

        opening_line:str = f"{prefix}<{self.tag}"

        for att_name, att_value in self.attrib.items():

            opening_line += f" {att_name}=\"{att_value}\""

        if self.has_children():
            opening_line += ">"
            content.append( opening_line )
            for child in self.children_:
                content.extend( child.to_lines( offset + 1 ) )

            content.append( f"{prefix}</{self.tag}>" )

        else:
            opening_line += "/>"
            content.append( opening_line )


        return content 


class RosettaScriptsProtocol:

    def __init__(self):
        self.sections = defaultdict(list)
        self.section_names = "SCORINGGRIDS SCOREFXNS RESIDUE_SELECTORS PACKER_PALETTES TASKOPERATIONS MOVE_MAP_FACTORIES SIMPLE_METRICS FILTERS MOVERS PROTOCOLS OUTPUT".split()

    def add_element(self, section:str, element:RosettaScriptsElement) -> None:
        #TODO(CJ): add checks

        if section not in section_names:
            #TODO(CJ):
            pass

        self.sections[section].append( element )


    def add_scorefunction(self, scorefxn: RosettaScriptsElement) -> None:

        self.add_element("SCOREFXNS", scorefxn)

    def add_residue_selector(self, res_selector: RosettaScriptsElement) -> None:
        self.add_element("RESIDUE_SELECTORS", res_selector)

    def add_mover(self, mover: RosettaScriptsElement) -> None:
        self.add_element("MOVERS", mover)

    def add_filter(self, r_filter: RosettaScriptsElement) -> None:
        self.add_element("FILTERS", r_filter)


    def add_simple_metric(self, simple_metric: RosettaScriptsElement) -> None:
        self.add_element("SIMPLE_METRICS", simple_metric)

    def add_protocol(self, protocol: RosettaScriptsElement) -> None:

        self.add_element("PROTOCOLS", protocol)


    def add_scoring_grid(self, scoring_grid: RosettaScriptsElement) -> None:

        self.add_element("SCORINGGRIDS", scoring_grid)

    def to_file(self, fname:str) -> str:

        content:List[str] = [ "<ROSETTASCRIPTS>"] 

        for sn in self.section_names:
            if sn == "SCORINGGRIDS":
                if not self.sections[sn]:
                    continue
                opening_line = f"    <SCORINGGRIDS"                

                #TODO(CJ): fix for multiple scoring grids
                grid = self.sections[sn][0]

                for k, v in grid.attrib.items():
                    opening_line += f" {k}=\"{v}\""
                opening_line += ">"
                content.append( opening_line )

                for child in grid.children:
                    content.extend( child.to_lines(2) )


                content.append("    </SCORINGGRIDS>")
                continue

            content.append(f"    <{sn}>")

            for ss in self.sections[sn]:
                content.extend( ss.to_lines() )

            content.append(f"    </{sn}>")

        content.append("</ROSETTASCRIPTS>")

        fs.write_lines(fname, content)

        return fname

class RosettaScriptsEgg(ModelingResultEgg):
    score_file:str
    pdb_files:List[str]

class RosettaScriptsEngine(ModelingEngine):

    def __init__(self, interface, protocol: RosettaScriptsProtocol, opts:RosettaOptions, work_dir:str):
        self._parent_interface = interface
        self._work_dir = work_dir
        self._protocol = protocol
        self._opts = opts

    @property
    def parent_interface(self):
        return self._parent_interface

    @property
    def work_dir(self) -> str:
        return self._work_dir

    @property
    def protocol(self) -> RosettaScriptsProtocol:
        return self._protocol

    @property
    def opts(self) -> RosettaOptions:
        return self._opts

    def engine(self) -> str:
        return "rosetta"
        pass

    def make_input_files(self, stru: Structure):
        pass

    def make_job(self, stru:Structure,  opts:RosettaOptions) -> Tuple[ClusterJob, RosettaScriptsEgg]:
        if not isinstance(stru, Structure):
            _LOGGER.error("only allow Structure as `stru`")
            raise TypeError

        # 2. make .gjf file
        fs.safe_mkdir(self.work_dir)
        temp_gjf_file, gchk_path = self._make_gjf_file(stru)

        # 3. make cmd
        spe_cmd, gout_path = self.parent_interface.make_gaussian_cmd(temp_gjf_file)

        # 4. assemble ClusterJob
        cluster = self.cluster_job_config["cluster"]
        res_keywords = self.cluster_job_config["res_keywords"]
        env_settings = cluster.G16_ENV["CPU"]
        sub_script_path = fs.get_valid_temp_name(f"{self.work_dir}/submit_{self.name}.cmd")
        job = ClusterJob.config_job(
            commands = spe_cmd,
            cluster = cluster,
            env_settings = env_settings,
            res_keywords = res_keywords,
            sub_dir = "./", # because path are relative
            sub_script_path = sub_script_path
        )
        job.mimo = { # only used for translate clean up
            "temp_gin": [temp_gjf_file],
        }

        # 5. make result egg
        result_egg = GaussianQMResultEgg(
            gout_path = gout_path,
            gchk_path = gchk_path,
            stru=stru,
            parent_job = job,
        )

        return (job, result_egg)

        pass

    def run(self, stru:Structure) -> List[Structure]:

        _parser = PDBParser()
        score_file:str = self.parent_interface.run_rscripts(stru, self.protocol, self.opts, self.work_dir)

        results = self.parent_interface.parse_score_file(score_file)
        structures = list()

        for i, row in results.iterrows():
            row_dict = row.to_dict()

            pdb_file = f"{self.work_dir}/{row_dict.pop('description')}.pdb"
            stru = _parser.get_structure(pdb_file)

            for rk, rv in row_dict.items():
                stru.data[rk] = rv

            structures.append( stru )

        return structures



    def translate(self, egg: RosettaScriptsEgg):
        pass


@dataclass
class RosettaCartesianddGEgg(ddGResultEgg):
    """This class define the result egg of cartesian ddg
    calculation"""
    ddg_file: str
    parent_job: ClusterJob


class RosettaCartesianddGEngine(ddGFoldEngine):
    """The cartesian_ddg engine of Rosetta. Configures with

    num_iter:
        the number of iterations of the Cartesian ddG calculation
    force_iter:
        If this flag is on the protocol will stop when the results converge on a score
    score_cutoff:
        If the lowest energy scores are within this cutoff the protocol will end early.
    fa_max_dis:
        modify fa_atr and fa_sol behavior, really important for protein stability
        (default: 9.0)  
    scorefxn:
        the name of the Rosetta scoring function used.
    save_mutant_pdb:
        whether save mutants pdb generated by Rosetta.
    cluster_job_config:
        dictionary that assign arguments for ClusterJob.config_job
        For `res_keywords` it works as it updates the default dict.
        (For example for MD it updates ARMerConfig.MD_GPU_RES or
        ARMerConfig.MD_CPU_RES depending on the core_type.)
        NOTE that it is also used to config resources (num cores, core type) even if local run is specified.
        key list: [cluster, res_keywords]
    keep_in_file:
        whether the function will keep the input file after completion.
    work_dir:
        the working dir that contains all the temp/result files.
    """
    def __init__(
            self,
            interface,
            num_iter: int,
            force_iter: bool,
            score_cutoff: float,
            fa_max_dis: float,
            scorefxn: float,
            cluster_job_config: Dict,
            relax_cluster_job_config: Dict,
            relax_nstruct: int,
            save_mutant_pdb: float,
            keep_in_file: bool,
            work_dir: str,
        ):
        self._parent_interface = interface
        self._num_iter = num_iter
        self._force_iter = force_iter
        self._score_cutoff = score_cutoff
        self._fa_max_dis = fa_max_dis
        self._scorefxn = scorefxn
        self._cluster_job_config = cluster_job_config
        self._relax_cluster_job_config = relax_cluster_job_config
        self._relax_nstruct = relax_nstruct
        self._save_mutant_pdb = save_mutant_pdb
        self._keep_in_file = keep_in_file
        self._work_dir = work_dir

    # region == attribute ==
    @property
    def engine(self) -> str:
        """the engine name that should be hardcoded in each concrete class"""
        return "rosetta"

    @property
    def parent_interface(self) -> RosettaInterface:
        """getter for _parent_interface"""
        return self._parent_interface

    @property
    def num_iter(self) -> int:
        """getter for _num_iter"""
        return self._num_iter

    @property
    def force_iter(self) -> bool:
        """getter for _force_iter"""
        return self._force_iter

    @property
    def score_cutoff(self) -> float:
        """getter for _score_cutoff"""
        return self._score_cutoff

    @property
    def fa_max_dis(self) -> float:
        """getter for _fa_max_dis"""
        return self._fa_max_dis

    @property
    def scorefxn(self) -> float:
        """getter for _scorefxn"""
        return self._scorefxn

    @property
    def cluster_job_config(self) -> Dict:
        """getter for _cluster_job_config"""
        return self._cluster_job_config

    @property
    def relax_cluster_job_config(self) -> Dict:
        """getter for _relax_cluster_job_config"""
        return self._relax_cluster_job_config

    @property
    def relax_nstruct(self) -> int:
        """getter for _relax_nstruct"""
        return self._relax_nstruct

    @property
    def save_mutant_pdb(self) -> float:
        """getter for _save_mutant_pdb"""
        return self._save_mutant_pdb

    @property
    def keep_in_file(self) -> bool:
        """getter for _keep_in_file"""
        return self._keep_in_file

    @property
    def work_dir(self) -> str:
        """getter for _work_dir"""
        return self._work_dir
    # endregion

    def action_on_wt(self, stru: Structure) -> Structure:
        """apply some action on the wild-type. For cartesian ddg, they are:
        1. relax the structure using the same scoring function.
        
        Returns:
            return a copy of the changed structure."""
        stru = copy.deepcopy(stru)
        # 0. remove ligands
        remove_non_peptide(stru)
        # TODO deal with NCAA
        
        # 1. relax
        fs.safe_mkdir(self.work_dir)
        relax_dir = f"{self.work_dir}/wt_relax/"
        score_df = self.parent_interface.relax(
            stru,
            nstruct=self.relax_nstruct,
            use_cartesian=True,
            scorefxn="ref2015_cart",
            cluster_job_config=self.relax_cluster_job_config,
            output_dir=relax_dir,
            # turn off un-necessary default
            constrain_relax_to_start_coords=False,
            coord_constrain_sidechains=False,
            ramp_constraints=False,
            delete_crash=True,
            )
        new_stru = self.parent_interface.get_structure_from_score(score_df)

        return new_stru

    def make_job(self, stru: Structure, mutant: Iterable[Mutation]) -> Tuple[ClusterJob, RosettaCartesianddGEgg]:
        """the method that makes a ClusterJob that runs the cartesian ddg"""
        # 1. input
        if not isinstance(stru, Structure):
            _LOGGER.error("only allow Structure as `stru`")
            raise TypeError
        if (not isinstance(mutant, list) and not isinstance(mutant, tuple)) or not isinstance(mutant[0], Mutation):
            _LOGGER.error("only allow List[Mutation] as `mutant`")
            raise TypeError

        # 2. make input file
        fs.safe_mkdir(self.work_dir)
        temp_pdb_file = self._make_pdb_file(stru)
        temp_mut_file, ddg_out_path = self._make_mut_file(mutant) # the output path is determined by the input path. will get_valid for out

        # 3. make cmd
        _cmd = self.parent_interface.make_cart_ddg_cmd(
            pdb_path=temp_pdb_file,
            mut_file=temp_mut_file,
            num_iter=self.num_iter,
            force_iter=self.force_iter,
            score_cutoff=self.score_cutoff,
            fa_max_dis=self.fa_max_dis,
            scorefxn=self.scorefxn,
            save_mutant_pdb=self.save_mutant_pdb,
        )

        # 4. assemble ClusterJob
        cluster = self.cluster_job_config["cluster"]
        res_keywords = self.cluster_job_config["res_keywords"]
        env_settings = cluster.ROSETTA_ENV["serial_CPU"]
        sub_script_path = fs.get_valid_temp_name(f"{self.work_dir}/submit_cart_ddg.cmd")
        job = ClusterJob.config_job(
            commands = _cmd,
            cluster = cluster,
            env_settings = env_settings,
            res_keywords = res_keywords,
            sub_dir = "./", # because path are relative
            sub_script_path = sub_script_path
        )
        job.mimo = { # only used for translate clean up
            "temp_files": [temp_mut_file, temp_pdb_file],
        }

        # 5. make result egg
        result_egg = RosettaCartesianddGEgg(
            ddg_file = ddg_out_path,
            parent_job=job,
        )

        return (job, result_egg)

    def run(self, stru: Structure, mutant: List[Mutation]) -> float:
        """the method that runs the cartesian ddg"""
        # 1. input
        if not isinstance(stru, Structure):
            _LOGGER.error("only allow Structure as `stru`")
            raise TypeError
        if (not isinstance(mutant, list) and not isinstance(mutant, tuple)) or not isinstance(mutant[0], Mutation):
            _LOGGER.error("only allow List[Mutation] as `mutant`")
            raise TypeError

        # 2. make input file
        fs.safe_mkdir(self.work_dir)
        temp_pdb_file = self._make_pdb_file(stru)
        temp_mut_file, ddg_out_path = self._make_mut_file(mutant) # the output path is determined by the input path. will get_valid for out

        # 3. make cmd
        _cmd = self.parent_interface.make_cart_ddg_cmd(
            pdb_path=temp_pdb_file,
            mut_file=temp_mut_file,
            num_iter=self.num_iter,
            force_iter=self.force_iter,
            score_cutoff=self.score_cutoff,
            fa_max_dis=self.fa_max_dis,
            scorefxn=self.scorefxn,
            save_mutant_pdb=self.save_mutant_pdb,
        )
        _cmd_exe = _cmd.split(" ")[0]
        _cmd_args = _cmd.split(" ")[1:]

        # 4. run cmd
        this_run = self.parent_interface.env_manager_.run_command(
            exe=_cmd_exe,
            args=_cmd_args,
        )
        self.check_dgg_fold_error(ddg_out_path, this_run)

        # 5. make result
        ddg_fold = self.get_ddg_fold(ddg_out_path)

        # 6. clean up
        fs.clean_temp_file_n_dir([temp_mut_file, temp_pdb_file])
        # archive
        fs.safe_mkdir(f"{self.work_dir}/results")
        fs.safe_mv(ddg_out_path, f"{self.work_dir}/results/{Path(ddg_out_path).name}")

        return ddg_fold

    def translate(self, result_egg: RosettaCartesianddGEgg) -> float:
        """the method convert engine specific results to general output"""
        ddg_file = result_egg.ddg_file
        parent_job = result_egg.parent_job

        # error check
        self.check_dgg_fold_error(ddg_file, result_egg.parent_job)

        ddg_fold = self.get_ddg_fold(ddg_file)

        # clean up
        clean_up_target = [result_egg.parent_job.job_cluster_log,
                           result_egg.parent_job.sub_script_path]
        if not self.keep_in_file:
            clean_up_target.extend(parent_job.mimo["temp_files"])
        fs.clean_temp_file_n_dir(clean_up_target)
        # archive
        fs.safe_mkdir(f"{self.work_dir}/results")
        fs.safe_mv(ddg_file, f"{self.work_dir}/results/{Path(ddg_file).name}")

        return ddg_fold

    def check_dgg_fold_error(self,
                        ddg_file: str,
                        stdstream_source: Union[ClusterJob,
                                                CompletedProcess,
                                                SubprocessError]):
        """a check for whether an error occurs in the ddg is needed everytime before generating
        a final number.
        Possible error info places:
        1. stdout/stderr
        2. ROSETTA_CRASH.log (this file is wrote by all Rosetta exec under the folder)
        The goal is to summarize each error type and give suggestions."""
        # 0. ddg file not exists or dont have content --> Error occured
        if not Path(ddg_file).exists() or os.path.getsize(ddg_file) == 0:
            # collect error info
            error_info_list = []
            # 1. stdout stderr
            if isinstance(stdstream_source, ClusterJob):
                with open(stdstream_source.job_cluster_log) as f:
                    stderr_stdout = f.read()
                    error_info_list.append(f"stdout/stderr(from job log):{os.linesep*2}{stderr_stdout}")
            elif isinstance(stdstream_source, CompletedProcess):
                error_info_list.append(f"stdout:{os.linesep*2}{stdstream_source.stdout}")
                error_info_list.append(f"stderr:{os.linesep*2}{stdstream_source.stderr}")
            elif isinstance(stdstream_source, SubprocessError):
                error_info_list.append(f"stdout:{os.linesep*2}{stdstream_source.stdout}")
                error_info_list.append(f"stderr:{os.linesep*2}{stdstream_source.stderr}")
            else:
                _LOGGER.error("Only allow ClusterJob, CompletedProcess, SubprocessError as input types for `stdstream_source`")
                raise TypeError
            # 2. ROSETTA_CRASH.log file
            # TODO finish this with a real example
            # normally will be a Error termination of Gaussian

            _LOGGER.error(f"Rosetta cartesian_ddg didn't finish normally.{os.linesep}{os.linesep.join(error_info_list)}")
            raise RosettaError(error_info_list)

    def _make_mut_file(self, mutant: List[Mutation]) -> Tuple[str]:
        """make a temporary mut_file.
        NOTE that the final result file path is determined by the mut_file path.
        To avoid overwriting results from parallel runs, mut_file path is determined by
        finding a non-existing result file path under self.work_dir.
        If the file exists, will change the filename to {self.name}_{index}.txt
        NOTE that Rosetta made the .ddg file always under the current folder

        Return: (path of the mut_file and the result file)"""
        # path
        # 1. repel with existing .ddg file
        temp_result_file_path = fs.get_valid_temp_name("mutations.ddg")
        # 2. repel with upcoming .ddg file
        temp_mut_file_path = f"{temp_result_file_path.removesuffix('ddg')}txt"
        temp_mut_file_path = fs.get_valid_temp_name(f"{self.work_dir}/{temp_mut_file_path}")
        # 3. finalize
        temp_result_file_path = f"{Path(temp_mut_file_path).stem}.ddg"

        # content
        mut_file_lines = [
            f"total {len(mutant)}",
            f"{len(mutant)}",
        ]
        for mut in mutant:
            mut_file_lines.append(f"{mut.get_orig(True)} {mut.res_idx} {mut.get_target(True)}")
            # NOTE potential risk that it could be the pose number is used here.
        mut_file_lines.append(
            ""
        )

        fs.write_lines(temp_mut_file_path, mut_file_lines)

        return temp_mut_file_path, temp_result_file_path

    def _make_pdb_file(self, stru: Structure) -> str:
        """make the pdb file for the cartesian ddg calculation"""
        result = fs.get_valid_temp_name(f"{self.work_dir}/cart_ddg_temp.pdb")
        rosetta_stru = copy.deepcopy(stru)
        self.parent_interface.rename_atoms(rosetta_stru)
        PDBParser().save_structure(result, rosetta_stru)
        
        return result

    def get_ddg_fold(self, ddg_file: str, method: str="average") -> float:
        """calculate the ddG_fold number from the .ddg file."""
        score_df = pd.read_csv(ddg_file, delim_whitespace=True, header=None)
        group_by_variant = score_df.groupby(2)
        if method == "average":
            for tag, value in group_by_variant[3].mean().items():
                tag: str
                value: float
                if tag.startswith("WT_"):
                    wt_value = value
                if tag.startswith("MUT_"):
                    mut_value = value
            result = mut_value - wt_value
        else:
            _LOGGER.error(f"method {method} is not supported")
            raise ValueError

        return result


class RosettaInterface(BaseInterface):
    """Class that provides an interface for enzy_htp to utilize the Rosetta molecular modelling software suite. Supported 
    operations include relaxation (minimzation), scoring, ligand parameterization, and the ability to use RosettaScripts.

    Attributes:
        config_	: The RosettaConfig() class which provides settings for both running Rosetta and maintaining a compatible environment.
        env_manager_ : The EnvironmentManager() class which ensures all required environment elements exist.
        compatible_env_ : A bool() indicating if the current environment is compatible with the object itself.
    """

    def __init__(self, parent, config: RosettaConfig = None) -> None:
        """Simplistic constructor that optionally takes an RosettaConfig object as its only argument.
        Calls parent class.
        """
        super().__init__(parent, config, default_rosetta_config)

    def _delete_score_file(self, working_dir: str = './') -> None:
        """Helper method that deletes the score.sc file in the specified directory.

        Args:
            working_dir: The directory to look for the score.sc file in. Defaults to './'

        Returns:
            Nothing.
        """
        score_file = working_dir + "/score.sc"
        fs.safe_rm(score_file)

    def _delete_crash_log(self) -> None:
        """Helper method that deletes the ROSETTA_CRASH.log file in the current working directory. ROSETTA_CRASH.log
        should always be in the current working directory.

        Args:
            Nothing. 

        Returns:
            Nothing.
        """
        fs.safe_rm('./ROSETTA_CRASH.log')

    def rename_atoms(self, stru: Structure) -> None:
        """Renames residues and atoms to be compatible with Rosetta naming and functions.
        
        Args:
            stru: The Structure() to perform renaming on.

        Returns:
            Nothing. 
        """
        nterm_mapper:Dict = {"H1":"1H", "H2":"2H", "H3":"3H"}
        his_mapper:Dict = {"HB2":"1HB", "HB3":"2HB"}
        _LOGGER.info("Beginning renaming...")
        changed_residues:int = 0
        changed_atoms:int = 0
        for res in stru.residues:
            if not res.is_canonical():
                continue
            
            if res.name in "HID HIS HIE".split():
                res.name = "HIS"
                changed_residues += 1
                for aa in res.atoms:
                    if aa.name in his_mapper:
                        aa.name = his_mapper[aa.name]
                        changed_atoms += 1

            for aa in res.atoms:
                if aa.name in nterm_mapper:
                    aa.name = nterm_mapper[aa.name]
                    changed_atoms += 1
        _LOGGER.info(f"Finished renaming! Changed {changed_residues} residues and {changed_atoms} atoms.")

    def run_rosetta_scripts(self, opts: List[str], logfile: str = None) -> None:
        """Method that runs the rosettascripts executabl along with the supplied options. Optionally outputs
        the stdout to a specified logfile. Note that no sanitation is performed prior to running.

        Args:
            opts: a list() of str() to be run by the RosettaScripts executable.
            logfile: The file to output the stdout log to. Optional.

        Returns:
            Nothing,
        """

        if logfile:
            opts.extend([">", str(logfile)])

        self.env_manager_.run_command(self.config_.ROSETTA_SCRIPTS, opts, quiet_fail=True)

        if logfile:
            _LOGGER.info(f"Saved RosettaScripts log to '{Path(logfile).absolute}'.")

    def parse_score_file(self, fname: str) -> pd.DataFrame:
        """Method that parses a score file into a Pandas Dataframe. Only encodes lines that begin with SCORE.

        Args:
            fname: Path to the score file. Will error if does not exist.

        Returns:
            A pandas dataframe containing the data in the supplied score file.
        """

        if not Path(fname).exists():
            _LOGGER.error(f"The suppliied file '{fname}' does not exist. Exiting...")
            exit(1)

        lines: List[str] = fs.lines_from_file(fname)

        lines = list(filter(lambda ll: ll.startswith('SCORE:'), lines))

        data = list(map(lambda ll: ll.split()[1:], lines))

        df = pd.DataFrame(data=data[1:], columns=data[0])

        column_names = list(df.columns)
        for cn in column_names:
            if cn == 'description':
                continue
            df[cn] = df[cn].astype('float')

        return df

    def get_structure_from_score(
            self, score_df: pd.DataFrame,
            base_dir: str = "",
            target: str = "min_total",
            clean_up_pdb: bool = True) -> Structure:
        """get the structure of need from a score dataframe.

        Args:
            score_df:
                the target score.sc based DataFrame
            base_dir:
                the base dir that the run associated with the score uses.
                (it completes the relative path in the description when the relax
                is ran in a different dir. NOTE that if `output_dir` is used
                this base_dir is to complete output_dir if it is also relative.)
            target:
                the target structure based on the score.
                (default: obtain the structure with the minimum (most negative) total score)
            clean_up_pdb:
                whether clean up all the PDB files after parsing."""
        # locate the PDB
        if target == "min_total":
            idx = score_df["total_score"].idxmin()
        else:
            _LOGGER.error(f"unexpected keyword for target found {target}")
            raise ValueError

        pdb_path = score_df["description"][idx]
        # parse the PDB
        result = PDBParser().get_structure(f"{base_dir}{pdb_path}")
        # TODO need to rename to convention.

        if clean_up_pdb:
            for temp_pdb_path in score_df["description"]:
                fs.clean_temp_file_n_dir([temp_pdb_path])

        return result

    def parameterize_ligand(self, mol: Ligand, charge:int=None, work_dir:str=None) -> Tuple[str, str]:
        """Parameterizes the input ligand for use in the RosettaLigand protocol. Takes an input file with the ligand,
        as well as the name of the residue in PDB format (3 capitalized letters) as well as optionally where the output
        directory where the .params and .pdb files should be saved. The underlying script only supports .mol, .mol2, 
        and .sdf formats. Can also add conformers to end of .params file when conformers file is supplied. Function 
        exits on invalid inputs. 
        TODO(CJ): fix this documentation            
        Args:
            molfile: The name of the input file as a str().
            res_name: The all-capitalized, three letter string of the ligand in PDB format.
            outfile: Where the .params file should be saved. Optional.
            conformers: The conformers file for the given ligand. Optional.

        Returns:
            A tuple() with the layout of (.params file, .pdb file)            

        """
        if work_dir is None:
            work_dir = "./"

        res_name:str=mol.name
        molfile:str = f"{work_dir}/{res_name}.mol2"
        conformers:str=f"{work_dir}/{res_name}_conformers.pdb"
        params_file:str=f"./{res_name}.params"
        _parser = Mol2Parser()
        _parser.save_ligand(molfile, mol)
        flags: List[str] = [self.config_.PARAMS_SCRIPT, f"{molfile}", f"--name={res_name}", "--clobber", "--keep-names" ]
       
        indices = list()
        for aidx,aa in enumerate(mol.atoms):
            if aa.element == 'H':
                continue
            indices.append( aidx + 1 )
            
        if len(indices) <= 2:            
            flags.append( f"--nbr_atom={indices[0]}" )
        

        self.env_manager_.run_command(self.config_.PY_2_7, flags)
        fs.safe_rm(f"{res_name}_0001.pdb")
        
        params_file = fs.safe_mv(params_file, work_dir)
        params_content:List[str]=fs.lines_from_file(params_file)

        if charge is not None:
            params_content.append(
                f"NET_FORMAL_CHARGE {charge}"
            )

        _LOGGER.info(params_file)

        n_conformers:int=mol.n_conformers()
        if n_conformers > 1:
            conformer_file_content:List[str] = list()
            mol2_temp:str=f"{work_dir}/__temp_ligand_mol2.mol2"
            _LOGGER.info(f"Detected {n_conformers} in ligand {res_name}")
            _parser = Mol2Parser()
            session = self.parent().pymol.new_session()
            for cidx in range(1, n_conformers):
                conf = mol.get_ligand_conformer(cidx)
                fs.safe_rm(mol2_temp)
                _parser.save_ligand(mol2_temp, conf)
                pdb_conf:str=self.parent().pymol.convert(session, mol2_temp, new_ext='.pdb')
                conformer_file_content.extend(fs.lines_from_file(pdb_conf))
                fs.safe_rm(pdb_conf)

            conformer_file_content = list(filter(lambda ll: ll.startswith('HETATM') or ll.startswith('END'), conformer_file_content))

            fs.write_lines(conformers, conformer_file_content) 

            params_content.append(f"PDB_ROTAMERS {conformers}")

            fs.safe_rm(mol2_temp)

        fs.write_lines(params_file, params_content)
        
        return params_file 

    def make_cart_ddg_cmd(
            self, 
            pdb_path: str, 
            mut_file: str, 
            num_iter: int,
            force_iter: bool,
            score_cutoff: float,
            fa_max_dis: float,
            scorefxn: float,
            save_mutant_pdb: bool,
            # TODO figure out arguments
        ) -> str:
        """make the command line str for running cartesin ddg"""
        cart_ddg_exe = self.config_.get_cart_ddg_exe()
        flags = [
            f"-in:file:s {pdb_path}",
            f"-ddg::mut_file {mut_file}",
            f"-ddg:iterations {num_iter}",
            f"-force_iterations {str(force_iter).lower()}",
            f"-ddg::score_cutoff {score_cutoff}",
            f"-ddg::cartesian",
            f"-ddg::dump_pdbs {str(save_mutant_pdb).lower()}",
            f"-fa_max_dis {fa_max_dis}",
            f"-score:weights {scorefxn}",
            f"-ddg::legacy false",
            f"-mute all",
        ]
        result = [f"{cart_ddg_exe}"] + flags
        result = " \\\n".join(result)

        return result

    def make_rosetta_scripts_cmd(
        self, 
        pdb_path,
        

    def relax(
        self,
        infile: Union[Structure, str],
        nstruct: int,
        scorefxn: str = None,
        use_cartesian: bool = False,
        ignore_zero_occupancy: bool = True, # TODO make a function that handles making options specifically. (since a lot of them are the same.)
        full_atom: bool = True,
        detect_disulf: bool = True,
        linmem_ig: int = 10,
        constrain_relax_to_start_coords: bool = True,
        coord_constrain_sidechains: bool = True,
        ramp_constraints: bool = True,
        prefix: str = None,
        overwrite: bool = True,
        extra_flags: List[str] = None,
        output_dir: str = './rosetta_relax',
        delete_scores: bool = True,
        delete_crash: bool = True,
        cluster_job_config: Dict = None,
        job_check_period: int = 180,
    ) -> pd.DataFrame:
        """Runs Rosetta's relax protocol on the supplied .pdb file, returning the path to the relaxaed structure as 
        well as a dictionary with all characteristics found in the score.sc file. Function provides direct access to a 
        number of commandline options and the ability to add arbitrary commandline options at the end. 

        NOTE: The majority of crashes from this function are due to bad atom names.

        Args:
            infile: A str() with the path to the .pdb file to relax. Or a Structure() in Rosetta naming convention.
            nstruct: Number of structures to create. 
            ignore_zero_occupancy: If relax should ignore atoms with zero occupancy. True by default.
            full_atom: If relax should do full atom relaxation. True by default.
            detect_disulf: If Rosetta should detect disulfide bonds. True by default.
            linmem_ig: Number of recent rotamers to store. 10 by default.
            constrain_relax_to_start_coords: If the backbone atoms should be constrained. True by default.
            coord_constrain_sidechains: If the sidechain heavy atoms should be constrained. True by default.
            ramp_constraints: If the constraints should be ramped during initial relaxation stage. True by default.
            prefix: str() with prefix for output file names. None and not used by default.
            overwrite: If results should be overwritten. True by default.
            extra_flags: A List[str] of extra flags to be added to the commandline. Empty by default. NOT CHECKED FOR CORRECTNESS. 
            output_dir: The output directory where the files will be saved. './' by default.
            delete_scores: Whether the score.sc file should be deleted after running. True by default.
            delete_crash: Whether the ROSETTA_CRASH.log file should be deleted after running. True by default.

        Returns:
            pandas DataFrame containing the results and energies of the relaxed structures. Description column contains
            full paths to relaxed files. 
        """
        # 1. dispatch for input
        clean_targets = []
        if isinstance(infile, str):
            fs.check_file_exists(infile)
            if Path(infile).suffix != '.pdb':
                _LOGGER.error(f"Expected input file format is .pdb. {infile} is an invalid entry. Exiting...")
                exit(1)
        elif isinstance(infile, Structure):
            # convert Structure to a PDB
            temp_pdb_path = fs.get_valid_temp_name("temp_rosetta_relax.pdb")
            # TODO apply StructureTranslator here
            stru = copy.deepcopy(infile)
            self.rename_atoms(stru)
            PDBParser().save_structure(temp_pdb_path, stru)
            infile = temp_pdb_path
            clean_targets.append(temp_pdb_path)
        else:
            _LOGGER.error(f"Found unsupported input type: {type(infile)}")
            raise TypeError

        # 2. prepare cmd TODO move this to a seperate function
        score_file = fs.get_valid_temp_name(f"{output_dir}/temp_score.sc")
        flags: List[str] = [
            f"-in:file:s '{infile}'",
            f"-nstruct {nstruct}",
            f"-linmem_ig {linmem_ig}",
            f"-out:file:scorefile {Path(score_file).name}",
        ]
        flags.append(f"-ignore_zero_occupancy {'true' if ignore_zero_occupancy else 'false'}")
        flags.append(f"-relax:constrain_relax_to_start_coords {'true' if constrain_relax_to_start_coords else 'false'}")
        flags.append(f"-coord_constrain_sidechains {'true' if coord_constrain_sidechains else 'false'}")
        flags.append(f"-ramp_constraints {'true' if ramp_constraints else 'false'}")
        flags.append(f"-out:path:all {output_dir}")
        flags.append(f"-relax:cartesian {'true' if use_cartesian else 'false'}")

        if full_atom:
            flags.append("-in:file:fullatom")

        if detect_disulf:
            flags.append("-in:detect_disulf")

        if prefix:
            flags.append(f"-out:prefix '{prefix}'")

        if overwrite:
            flags.append("-overwrite")

        if scorefxn:
            flags.append(f"-score:weights {scorefxn}")

        if extra_flags:
            flags.extend(extra_flags)

        # 3. execute
        fs.safe_mkdir(output_dir)
        
        if cluster_job_config:  # parallel, armer
            cluster = cluster_job_config["cluster"]
            res_keywords =  self.config().DEFAULT_RELAX_RES_KEYWORDS | cluster_job_config["res_keywords"]
            env_settings = cluster.ROSETTA_ENV["parallel_CPU"]
            sub_script_path = fs.get_valid_temp_name(f"{output_dir}/submit_rosetta_relax.cmd")
            num_cores = res_keywords["node_cores"]
            _cmd = f"{self.config().RELAX_MPI_EXEC} {num_cores} {self.config().RELAX_MPI} {' '.join(flags)}"
            job = ClusterJob.config_job(
                commands = _cmd,
                cluster = cluster,
                env_settings = env_settings,
                res_keywords = res_keywords,
                sub_dir = "./", # because some path are relative
                sub_script_path = sub_script_path
            )
            job.submit()
            job.wait_to_end(period=job_check_period)

            # clean up
            fs.clean_temp_file_n_dir([
                job.sub_script_path,
                job.job_cluster_log,
            ])
        else: # serial, local
            self.env_manager_.run_command(self.config_.RELAX, flags)

        df: pd.DataFrame = self.parse_score_file(score_file)

        df['description'] = df.apply(lambda row: f"{output_dir}/{row.description}.pdb", axis=1)

        if delete_scores:
            clean_targets.append(score_file)

        if delete_crash:
            self._delete_crash_log()

        fs.clean_temp_file_n_dir(clean_targets)

        return df

    def score(
        self,
        infile: str,
        ignore_zero_occupancy: bool = True,
        overwrite: bool = True,
        extra_flags: List[str] = None,
        output_dir: str = './',
        delete_scores: bool = True,
        delete_crash: bool = True,
    ) -> float:
        """Provides the total score in Rosetta Energy Units (REU) for a given structure. Uses default flags but can have behavior modified
        via supplied extra_flags. Returns the total score in REU.

        Arguments:
            infile: A str() with the path to the .pdb file to relax. 
            ignore_zero_occupancy: If relax should ignore atoms with zero occupancy. True by default.
            overwrite: If results should be overwritten. True by default.
            extra_flags: A List[str] of extra flags to be added to the commandline. Empty by default. NOT CHECKED FOR CORRECTNESS. 
            output_dir: The output directory where the files will be saved. './' by default.
            delete_scores: Whether the score.sc file should be deleted after running. True by default.
            delete_crash: Whether the ROSETTA_CRASH.log file should be deleted after running. True by default.

        Returns:
            Score of structure in file in REU.

        """
        fs.check_file_exists(infile)

        flags: List[str] = [
            f"-in:file:s '{infile}'",
            "-ignore_unrecognized_res",
        ]

        flags.append(f"-ignore_zero_occupancy {'true' if ignore_zero_occupancy else 'false'}")
        flags.append(f"-out:path:all {output_dir}")

        if overwrite:
            flags.append("-overwrite")

        if extra_flags:
            flags.extend(extra_flags)

        fs.safe_rm(f"{output_dir}/score.sc")

        fs.safe_mkdir(output_dir)

        self.env_manager_.run_command(self.config_.SCORE, flags)

        df: pd.DataFrame = self.parse_score_file(f"{output_dir}/score.sc")

        if len(df) != 1:
            _LOGGER.error("Found more than one entry in score.sc file. Exiting...")
            exit(1)

        if delete_scores:
            self._delete_score_file(output_dir)

        if delete_crash:
            self._delete_crash_log()

        return df.iloc[0].total_score

    def relax_loops(
        self,
        infile: str,
        nstruct: int,
        ignore_zero_occupancy: bool = True,
        full_atom: bool = True,
        detect_disulf: bool = True,
        linmem_ig: int = 10,
        constrain_relax_to_start_coords: bool = True,
        coord_constrain_sidechains: bool = True,
        ramp_constraints: bool = True,
        prefix: str = None,
        overwrite: bool = True,
        extra_flags: List[str] = None,
        output_dir: str = './',
        delete_scores: bool = True,
        delete_crash: bool = True,
    ) -> pd.DataFrame:
        """

        Args:
            infile: A str() with the path to the .pdb file to relax. 
            nstruct: Number of structures to create. 
            ignore_zero_occupancy: If relax should ignore atoms with zero occupancy. True by default.
            full_atom: If relax should do full atom relaxation. True by default.
            detect_disulf: If Rosetta should detect disulfide bonds. True by default.
            linmem_ig: Number of recent rotamers to store. 10 by default.
            constrain_relax_to_start_coords: If the backbone atoms should be constrained. True by default.
            coord_constrain_sidechains: If the sidechain heavy atoms should be constrained. True by default.
            ramp_constraints: If the constraints should be ramped during initial relaxation stage. True by default.
            prefix: str() with prefix for output file names. None and not used by default.
            overwrite: If results should be overwritten. True by default.
            extra_flags: A List[str] of extra flags to be added to the commandline. Empty by default. NOT CHECKED FOR CORRECTNESS. 
            output_dir: The output directory where the files will be saved. './' by default.
            delete_scores: Whether the score.sc file should be deleted after running. True by default.
            delete_crash: Whether the ROSETTA_CRASH.log file should be deleted after running. True by default.


        Returns:
            pandas DataFrame containing the results and energies of the relaxed structures. Description column contains
            full paths to relaxed files. 
        """
        #TODO(CJ):should also be able to take a Structure as input.
        fs.check_file_exists(infile)

        if Path(infile).suffix != '.pdb':
            _LOGGER.error(f"Expected input file format is .pdb. {infile} is an invalid entry. Exiting...")
            exit(1)

        fs.safe_rm(f'{output_dir}/score.sc')
        #/dors/meilerlab/apps/rosetta/rosetta-3.13/main/source/bin/relax.default.linuxgccrelease
        #-out:prefix $prefix
        #-out:file:scorefile ${prefix}.sc &
        flags: List[str] = [
            f"-in:file:s '{infile}'",
            f"-nstruct {nstruct}",
            f"-linmem_ig {linmem_ig}",
        ]

        flags.append(f"-ignore_zero_occupancy {'true' if ignore_zero_occupancy else 'false'}")
        flags.append(f"-relax:constrain_relax_to_start_coords {'true' if constrain_relax_to_start_coords else 'false'}")
        flags.append(f"-coord_constrain_sidechains {'true' if coord_constrain_sidechains else 'false'}")
        flags.append(f"-ramp_constraints {'true' if ramp_constraints else 'false'}")
        flags.append(f"-out:path:all {output_dir}")

        if full_atom:
            flags.append("-in:file:fullatom")

        if detect_disulf:
            flags.append("-in:detect_disulf")

        if prefix:
            flags.append(f"-out:prefix '{prefix}'")

        if overwrite:
            flags.append("-overwrite")

        if extra_flags:
            flags.extend(extra_flags)

        fs.safe_mkdir(output_dir)

        self.env_manager_.run_command(self.config_.RELAX, flags)

        df: pd.DataFrame = self.parse_score_file(f'{output_dir}/score.sc')

        df['description'] = df.apply(lambda row: f"{output_dir}/{row.description}.pdb", axis=1)

        if delete_scores:
            self._delete_score_file(output_dir)

        if delete_crash:
            self._delete_crash_log()

        return df

    def write_script(self, fname: str, args: List[Dict]) -> str:
        """Writes an XML script to be used with RosettaScripts. Each element of the XML script is represented
        as a dict() within a list() of args. Note that each element dict() is required to have two keys, "parent"
        and "tag". "parent" refers to which element it should be nested under. In the case that there are multiple
        levels of nesting, they are joined by "." characters. The "tag" is the tag name of the element but note
        that there is NO checking for whether or not the included element tags are valid.
        
        Args:
            fname: The .xml file to save the script contents to.
            args: A list() of dict()'s where each is an element in the final .xml file. 
            
        Returns:
            The name of the script file.
        """

        def _find_node(elem: ET.Element, name: str) -> ET.Element:
            """Helper function that recursively finds the specified parent XML node. Assumes that supplied name
            str() is correctly delimited with '.' characters. DOES NOT check for correctness of nam.e

            Args:
                elem: The ET.Element to search within.
                name: The str() name to search for.

            Return:
                The XML node with the target tag name.
            """
            tks: List[str] = name.split('.', 1)

            target: str = tks[0]

            result: ET.Element = None
            if elem.tag == target:
                result = elem
            else:
                for ee in elem:
                    if ee.tag == target:
                        result = ee
                        break
                else:
                    _LOGGER.error(f"There is no element with tag name '{target}' at this level. Exiting...")
                    exit(1)

            if len(tks) > 1:
                return _find_node(result, tks[1])
            else:
                return result

        root = ET.Element("ROSETTASCRIPTS")
        ET.SubElement(root, "RESIDUE_SELECTORS")
        ET.SubElement(root, "SCOREFXNS")
        ET.SubElement(root, "LIGAND_AREAS")
        ET.SubElement(root, "INTERFACE_BUILDERS")
        ET.SubElement(root, "MOVEMAP_BUILDERS")
        #ET.SubElement(root, "SCORINGGRIDS")
        ET.SubElement(root, "TASKOPERATIONS")
        ET.SubElement(root, "SIMPLE_METRICS")
        ET.SubElement(root, "FILTERS")
        ET.SubElement(root, "MOVERS")
        ET.SubElement(root, "PROTOCOLS")
        ET.SubElement(root, "OUTPUT")

        for arg in args:
            parent_name = arg.pop("parent", None)
            tag_name = arg.pop("tag", None)
            target_node = None

            bad: bool = False

            if not parent_name:
                #TODO(CJ): check if the parent name has an equal sign specifying the target node
                # more than what you would specify it otherwise
                _LOGGER.error("No parent name supplied in XML element dict()!")
                bad = True

            if bad:
                _LOGGER.error("Problems with XML elements detected. Exiting...")
                exit(1)

            child_nodes = arg.pop('child_nodes', list())
            #if arg.get('append_elements_only', False):
            #    _ = arg.pop('append_elements_only')
            #    target_node = _find_node(root, tag_name)
            #    for attrib, value in arg.items():
            #        target_node.set( attrib, value )

            #else:
            parent: ET.Element = _find_node(root, parent_name)

            if arg.get('append_elements_only', False):
                _ = arg.pop('append_elements_only')
                if tag_name == "SCORINGGRIDS":
                    parent: ET.Element = _find_node(root, 'ROSETTASCRIPTS')
                    target_node = ET.Element(tag_name)
                    parent.insert(0, target_node)
                    #target_node = ET.SubElement(parent[0], tag_name )
                else:
                    target_node = ET.SubElement(parent, tag_name)

                for attrib, value in arg.items():
                    target_node.set(attrib, value)
            else:
                target_node = ET.SubElement(parent, tag_name, attrib=arg)

            if child_nodes:
                for cn in child_nodes:
                    child_child_nodes = cn.pop('child_nodes', None)
                    tag_name = cn.pop('tag', None)
                    _ = cn.pop('parent', None)
                    #TODO(CJ): make this recursive so it actually works for super nested things
                    placed_child = ET.SubElement(target_node, tag_name, attrib=cn)

                    if child_child_nodes:
                        for ccn in child_child_nodes:
                            tag_name = ccn.pop('tag', None)
                            _ = ccn.pop('parent', None)
                            _ = ET.SubElement(placed_child, tag_name, attrib=ccn)

        for rr in root:
            rr.text = "\n\t"

        xmlstr: str = minidom.parseString(ET.tostring(root)).toprettyxml()
        xml_content: List[str] = xmlstr.replace('<?xml version="1.0" ?>\n', '').splitlines()

        xml_content = list(filter(lambda ll: len(ll.strip()) > 0, xml_content))

        fs.write_lines(fname, xml_content)

        return fname

    def loop_relax(
        self,
        infile: str,
        nstruct: int,
        ignore_zero_occupancy: bool = True,
        detect_disulf: bool = True,
        linmem_ig: int = 10,
        overwrite: bool = True,
        extra_flags: List[str] = None,
        output_dir: str = './',
        delete_scores: bool = True,
        delete_crash: bool = True,
    ) -> pd.DataFrame:
        """TODO
        Args:
            infile: A str() with the path to the .pdb file to relax. 
            nstruct: Number of structures to create. 
            ignore_zero_occupancy: If relax should ignore atoms with zero occupancy. True by default.
            detect_disulf: If Rosetta should detect disulfide bonds. True by default.
            linmem_ig: Number of recent rotamers to store. 10 by default.
            overwrite: If results should be overwritten. True by default.
            extra_flags: A List[str] of extra flags to be added to the commandline. Empty by default. NOT CHECKED FOR CORRECTNESS. 
            output_dir: The output directory where the files will be saved. './' by default.
            delete_scores: Whether the score.sc file should be deleted after running. True by default.
            delete_crash: Whether the ROSETTA_CRASH.log file should be deleted after running. True by default.

        Returns:
            pandas DataFrame containing the results and energies of the relaxed structures. Description column contains
            full paths to relaxed files. 
        """
        fs.check_file_exists(infile)

        if Path(infile).suffix != '.pdb':
            _LOGGER.error(f"Expected input file format is .pdb. {infile} is an invalid entry. Exiting...")
            exit(1)

        fs.safe_rm(f'{output_dir}/score.sc')
        flags: List[str] = [
            f"-in:file:s '{infile}'",
            f"-nstruct {nstruct}",
            f"-linmem_ig {linmem_ig}",
        ]

        df: pd.DataFrame = self.parent().pymol.collect('production.pdb', 'resi ss resn'.split(), sele='name CA')
        df['resi'] = df.resi.astype(int)

        ss = []
        for i, row in df.iterrows():
            if row.resn.upper() in "MG ZN HG".split():
                ss.append('M')
            else:
                ss.append(row.ss)

        df['ss'] = ss

        elements: List[Dict] = [
            {
                'parent': 'SCOREFXNS',
                'tag': 'ScoreFunction',
                'name': 'score_fxn',
                'weights': 'ref2015'
            },
            {
                'parent': 'MOVERS',
                'tag': 'FastRelax',
                'name': 'fast_relax',
                'scorefxn': 'score_fxn'
            },
            {
                'parent': 'MOVERS.FastRelax',
                'tag': 'MoveMap',
                'name': 'move_map'
            },
        ]

        temp: Dict[str, str] = deepcopy({
            'state': df.iloc[0].ss,
            'start': df.iloc[0].resi,
            'end': df.iloc[0].resi,
        })

        for i, row in df.iterrows():
            #TODO(CJ): need to ignore the non-amino acid stuff here
            if row.ss == temp['state']:
                temp['end'] = row.resi
            else:
                elements.append(
                    deepcopy({
                        'parent': 'MOVERS.FastRelax.MoveMap',
                        'tag': 'Span',
                        'begin': str(temp['start']),
                        'end': str(temp['end']),
                        'chi': 'true',
                        'bb': 'true' if temp['state'] == 'L' else 'false'
                    }))
                temp = deepcopy({
                    'state': row.ss,
                    'start': row.resi,
                    'end': row.resi,
                })

        elements.append(
            deepcopy({
                'parent': 'MOVERS.FastRelax.MoveMap',
                'tag': 'Span',
                'begin': str(temp['start']),
                'end': str(temp['end']),
                'chi': 'true',
                'bb': 'true' if temp['state'] == 'L' else 'false'
            }))

        elements.append({'parent': 'PROTOCOLS', 'tag': 'Add', 'mover_name': 'fast_relax'})

        fpath = Path(infile)
        xml_input: str = fpath.parent / "__temp.xml"
        xml_script = self.write_script(xml_input, elements)

        flags.extend(['-parser:protocol', str(xml_input.absolute())])

        flags.append(f"-ignore_zero_occupancy {'true' if ignore_zero_occupancy else 'false'}")
        flags.append(f"-out:path:all {output_dir}")

        if detect_disulf:
            flags.append("-in:detect_disulf")

        if overwrite:
            flags.append("-overwrite")

        if extra_flags:
            flags.extend(extra_flags)

        fs.safe_mkdir(output_dir)

        self.run_rosetta_scripts(flags)

        df: pd.DataFrame = self.parse_score_file(f'{output_dir}/score.sc')

        df['description'] = df.apply(lambda row: f"{output_dir}/{row.description}.pdb", axis=1)

        if delete_scores:
            self._delete_score_file(output_dir)

        if delete_crash:
            self._delete_crash_log()

        return df

    def create_cst_pdb_line(self, cst:ResiduePairConstraint, idx: int) -> str:
        """Creates a str() PDB line in the appropriate format so that Rosetta can apply the constrained geometry
        described by the RosettaCst. This line goes in the corresponding PDB file.
        
        Args:
            idx: The index of the RosettaCst as an int().
            
        Returns:
            The PDB line corresponding to the RosettaCst.

        """
        return f"REMARK 666 MATCH TEMPLATE {cst.residue1.parent.name} {cst.residue1.name}  {cst.residue1.idx:>3} MATCH MOTIF {cst.residue2.parent.name} {cst.residue2.name}  {cst.residue2.idx:>3}  {idx:>3}  1"

    def create_cst_lines(self, cst:ResiduePairConstraint) -> List[str]:
        """Creates a List[str] which describes the constrained geometries in the required enzyme design format for Rosetta.
        These lines go into the corresponding .cst file."""
        cst_content: List[str] = list()
        cst_content.append("CST::BEGIN")
        cst_content.append(f"   TEMPLATE::  ATOM_MAP: 1 atom_name: {' '.join(map(lambda aa: aa.name, cst.residue1_atoms))}")
        cst_content.append(f"   TEMPLATE::  ATOM_MAP: 1 residue3: {cst.residue1.name}")
        cst_content.append("")
        cst_content.append(f"   TEMPLATE::  ATOM_MAP: 2 atom_name: {' '.join(map(lambda aa: aa.name, cst.residue2_atoms))}")
        cst_content.append(f"   TEMPLATE::  ATOM_MAP: 2 residue3: {cst.residue2.name}")
        cst_content.append("")

        for ridx, (rname, rule) in enumerate(cst.child_constraints):
            end = 0                
            if rule.is_angle_constraint() or rule.is_dihedral_constraint():
                end = 1
            cst_content.append(f"   CONSTRAINT::  {rname:>10}: {float(rule.target_value):6.2f} {float(rule.params['rosetta']['tolerance']):6.2f} {float(rule.params['rosetta']['penalty']):6.2f} {end}")

        cst_content.append("CST::END")

        return cst_content

    def write_constraint_file(self, stru:Structure, constraints:List[StructureConstraint], work_dir:str = None) -> str:
        #TODO(CJ): this!
        if work_dir is None:
            work_dir = "./"
    
        lines:List[str] = list()
        for cst in constraints:
            if cst.is_distance_constraint():
                assert False
                pass
            elif cst.is_angle_constraint():
                assert False
            elif cst.is_dihedral_constraint():
                assert False
            elif cst.is_residue_pair_constraint():
                for (cst_name, child_cst) in cst.child_constraints:
                    if child_cst.is_distance_constraint():
                        ridx_1:int=stru.absolute_index(child_cst.atoms[0].parent, indexed=1)
                        ridx_2:int=stru.absolute_index(child_cst.atoms[1].parent, indexed=1)
                        lines.append(
                            f"AtomPair {child_cst.atoms[0].name} {ridx_1} {child_cst.atoms[1].name} {ridx_2} LINEAR_PENALTY {child_cst.target_value:.2f} 0.00 {child_cst['rosetta']['tolerance']:.2f} {child_cst['rosetta']['penalty']:.2f}"
                        )
                    elif child_cst.is_angle_constraint():
                        ridx_1:int=stru.absolute_index(child_cst.atoms[0].parent, indexed=1)
                        ridx_2:int=stru.absolute_index(child_cst.atoms[1].parent, indexed=1)
                        ridx_3:int=stru.absolute_index(child_cst.atoms[2].parent, indexed=1)
                        lines.append(
                            f"Angle {child_cst.atoms[0].name} {ridx_1} {child_cst.atoms[1].name} {ridx_2} {child_cst.atoms[2].name} {ridx_3} LINEAR_PENALTY {np.radians(child_cst.target_value):.2f} 0.00 {np.radians(child_cst['rosetta']['tolerance']):.2f} {child_cst['rosetta']['penalty']/np.radians(1):.2f}"
                        )
                    else:
                        assert False

        fs.safe_mkdir(work_dir)
        fname:str = f"{work_dir}/constraints.cst"
        fs.write_lines(fname, lines )
        return fname 

    def integrate_enzdes_constraints(self, stru:Structure, constraints:List[StructureConstraint], work_dir:str=None) -> Tuple[str,str]:
        #TODO(CJ): update this

        if work_dir is None:
            work_dir = "./"

        fs.safe_mkdir(work_dir)

        _LOGGER.info("Beginning RosettaCst constraint integration...")
        parser = PDBParser()
        file_str = parser.get_file_str(stru, if_renumber=False, if_fix_atomname=False)
    
        pdb_content: List[str] = ["HEADER                                            xx-MMM-xx"]
        cst_content: List[str] = list()
        counter = 1
        for cidx, cst in enumerate(constraints):
            if cst.is_residue_pair_constraint():
                pdb_content.append(self.create_cst_pdb_line(cst, counter))
                cst_content.extend(self.create_cst_lines(cst))
                counter += 1
    
        pdb_file: str = f"{work_dir}/start.pdb"
        cst_file: str = f"{work_dir}/rdock.cst"
    
        if not Path(pdb_file).exists():
            fs.write_lines(pdb_file, pdb_content + file_str.splitlines())
    
        if not Path(cst_file).exists():
            fs.write_lines(cst_file, cst_content)
    
        _LOGGER.info("RosettaCst constraint integration successful! Relevant files:")
        _LOGGER.info(f"\t.pdb file: {Path(pdb_file).absolute()}")
        _LOGGER.info(f"\t.cst file: {Path(cst_file).absolute()}")
    
        return (pdb_file, cst_file)

    def score_energy(self, cst) -> float: 
        """TODO(CJ): add documentation"""

        if cst.is_residue_pair_constraint():
            total:float = 0.0
            for (_,child_cst) in self.child_constraints:
                total += self.score_energy(child_cst)
            return total

        penalty:float = cst['rosetta']['penalty'] 
        tolerance:float = cst['rosetta']['tolerance']
        difference:float = abs(cst.current_geometry() - cst.target_value)
        
        if difference <= tolerance:
            return 0.0
        else:
            return penalty * (difference - tolerance)

    # region == engines ==
    def build_cartesian_ddg_engine(
        self,
        num_iter: int = "default",
        force_iter: bool = "default",
        score_cutoff: float = "default",
        fa_max_dis: float = "default",
        scorefxn: float = "default",
        relax_nstruct: int = "default",
        # execution config
        cluster_job_config: Dict = "default",
        relax_cluster_job_config: Dict = "default",
        save_mutant_pdb: float = False,
        keep_in_file: bool = False,
        work_dir: str = "default",
        **kwargs,
    ) -> RosettaCartesianddGEngine:
        """constructor for RosettaCartesianddGEngine(). Config everything for a cartesian ddg
        calculation besides the actual WT structure and mutant.
        (based on https://www.rosettacommons.org/docs/latest/cartesian-ddG)

        Args:
            num_iter:
                the number of iterations of the Cartesian ddG calculation
            force_iter:
                If this flag is on the protocol will stop when the results converge on a score
            score_cutoff:
                If the lowest energy scores are within this cutoff the protocol will end early.
            fa_max_dis:
                modify fa_atr and fa_sol behavior, really important for protein stability
                (default: 9.0)  
            scorefxn:
                the name of the Rosetta scoring function used.
            relax_nstruct:
                the nstruct of the relax on the WT before calculating the ddg
            save_mutant_pdb:
                whether save mutants pdb generated by Rosetta.
            cluster_job_config:
                dictionary that assign arguments for ClusterJob.config_job
                For `res_keywords` it works as it updates the default dict.
                (For example for MD it updates ARMerConfig.MD_GPU_RES or
                ARMerConfig.MD_CPU_RES depending on the core_type.)
                NOTE that it is also used to config resources (num cores, core type) even if local run is specified.
                key list: [cluster, res_keywords]
            relax_cluster_job_config:
                the cluster_job_config for the relax applied to the WT before the ddG calculation.
            keep_in_file:
                whether the function will keep the input file after completion.
            work_dir:
                the working dir that contains all the temp/result files.
        Return:
            RosettaCartesianddGEngine()"""
        # init default values
        type_hint_sticker: RosettaConfig
        if num_iter == "default":
            num_iter = self.config()["DEFAULT_CART_DDG_NUM_ITER"]
        if force_iter == "default":
            force_iter = self.config()["DEFAULT_CART_DDG_FORCE_ITER"]
        if score_cutoff == "default":
            score_cutoff = self.config()["DEFAULT_CART_DDG_SCORE_CUTOFF"]
        if fa_max_dis == "default":
            fa_max_dis = self.config()["DEFAULT_CART_DDG_FA_MAX_DIS"]
        if scorefxn == "default":
            scorefxn = self.config()["DEFAULT_CART_DDG_SCOREFXN"]
        if relax_nstruct == "default":
            relax_nstruct = self.config()["DEFAULT_CART_DDG_RELAX_NSTRUCT"]

        if cluster_job_config == "default":
            cluster_job_config = self.config().get_default_cart_ddg_cluster_job_config()
        else:
            # For res_keywords, it updates the default config
            cluster_job_config = copy.deepcopy(cluster_job_config) # because we will change it in place.
            res_keywords_update = cluster_job_config["res_keywords"]
            default_res_keywords = self.config().get_default_cart_ddg_cluster_job_res_keywords()
            cluster_job_config["res_keywords"] = default_res_keywords | res_keywords_update

        if relax_cluster_job_config == "default":
            relax_cluster_job_config = self.config().get_default_cart_ddg_relax_cluster_job_config()
        else:
            # For res_keywords, it updates the default config
            relax_cluster_job_config = copy.deepcopy(relax_cluster_job_config) # because we will change it in place.
            res_keywords_update = relax_cluster_job_config["res_keywords"]
            default_res_keywords = self.config().get_default_cart_ddg_relax_cluster_job_res_keywords()
            relax_cluster_job_config["res_keywords"] = default_res_keywords | res_keywords_update

        if work_dir == "default":
            work_dir = self.config()["DEFAULT_CART_DDG_WORK_DIR"]

        return RosettaCartesianddGEngine(
            interface=self,
            num_iter = num_iter,
            force_iter = force_iter,
            score_cutoff = score_cutoff,
            fa_max_dis = fa_max_dis,
            scorefxn = scorefxn,
            relax_nstruct= relax_nstruct,
            cluster_job_config = cluster_job_config,
            relax_cluster_job_config = relax_cluster_job_config,
            save_mutant_pdb = save_mutant_pdb,
            keep_in_file = keep_in_file,
            work_dir = work_dir,

        )

    # endregion
 
