"""Defines AmberConfig() which holds configuration settings for enzy_htp to interface with the 
Amber software package. In addition to holding Amber settings, AmberConfig() creates the input
files for minimization, heating, constant pressure production, and constant pressure
equilibration. File also contains default_amber_config() which creates a default version
of the AmberConfig() object.

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>

Date: 2022-06-02
"""
import os
from copy import deepcopy
from typing import Any, List, Dict

from .base_config import BaseConfig
from .system_config import SystemConfig
from .armer_config import ARMerConfig

from enzy_htp.core.clusters.accre import Accre
from enzy_htp.core.general import get_str_for_print_class_var
from enzy_htp.core.logger import _LOGGER
from enzy_htp.structure.structure_constraint import StructureConstraint

class AmberConfig(BaseConfig):
    """Class that holds default values for running Amber within enzy_htp and also creates
    input files for minimzation, heating, constant pressure production, and constant
    pressure equilibration.

    Attributes:
        parent_ : Points to parent config object. Optional and defaults to None.
        HOME : str() corresponding to Amber home directory on the system.
        CPU_ENGINE : str() corresponding to Amber cpu sander.
        GPU_ENGINE : str() corresponding to Amber gpu sander.
        DEFAULT_SOLVATE_BOX_TYPE : str() corresponding to type of water box.
        DEFAULT_SOLVATE_BOX_SIZE : float() corresponding to the size of the water box.
        CONF_MIN : dict() holding settings for Amber minimization.
        CONF_HEAT : dict() holding settings for Amber heating.
        CONF_EQUI : dict() holding settings for Amber constant pressure equilibration run.
        CONF_PROD : dict() holding settings for Amber constant pressure production run.
        RADII_MAP: dict() containing settings for Amber's implementation of the Born solvation model. 
    """

    HOME: str = "AMBERHOME"
    """Environment variable for Amber's HOME Directory"""

    # region == Default values for build_md_parameterizer() ==
    DEFAULT_FORCE_FIELDS: List[str] = [
        "leaprc.protein.ff14SB",
        "leaprc.gaff2",
        "leaprc.water.tip3p",
    ]
    """build_md_parameterizer: default force fields used for parameterization. Used in tleap.in, conform the tleap format"""

    DEFAULT_CHARGE_METHOD: str = "AM1BCC"
    """build_md_parameterizer: default method used for determine the atomic charge."""

    DEFAULT_RESP_ENGINE: str = "g16"
    """build_md_parameterizer: default engine for calculating the RESP charge."""

    DEFAULT_RESP_LVL_OF_THEORY: str = "b3lyp/def2svp em=d3"
    """build_md_parameterizer: default level of theory for calculating the RESP charge."""

    DEFAULT_NCAA_PARAM_LIB_PATH: str = SystemConfig.NCAA_LIB_PATH
    """build_md_parameterizer: default path of the non-CAA parameter library."""

    DEFAULT_FORCE_RENEW_NCAA_PARAMETER: bool = False
    """build_md_parameterizer: default value for whether force renew the parameter files """

    DEFAULT_NCAA_NET_CHARGE_ENGINE: str = "PYBEL"
    """build_md_parameterizer: default engine the determines the net charge of NCAA if none is assigned in NCAA objects"""

    DEFAULT_NCAA_NET_CHARGE_PH: float = 7.0
    """build_md_parameterizer: default pH value used in determining the net charge of NCAA."""

    DEFAULT_SOLVATE_BOX_TYPE: str = "oct"
    """Solvation Box type. Allowed values are 'box' and 'oct'"""

    DEFAULT_SOLVATE_BOX_SIZE: float = 10.0
    """Solvation Box size."""

    DEFAULT_PARAMETERIZER_TEMP_DIR: str = f"{SystemConfig.SCRATCH_DIR}/amber_parameterizer"
    """The default temporary working directory that contains all the files generated by the AmberParameterizer"""
    # endregion

    # region == Default values for build_md_step() ==
    DEFAULT_MD_NAME: bool = "amber_md_step"
    """The default value for the name tag of the md step"""

    DEFAULT_MD_TIMESTEP: float = 0.000002 # ns
    """The default value for the timestep the md step"""

    DEFAULT_MD_MINIMIZE: bool = False
    """The default value for whether md step is a minimization"""

    DEFAULT_MD_TEMPERATURE: float = 300.0
    """The default value for the temperature of the simulation."""

    DEFAULT_MD_THERMOSTAT: str = "langevin"
    """default value for the algorithm of the thermostat."""

    DEFAULT_MD_PRESSURE_SCALING: str = "isotropic"
    """default value for the pressure scaling of the md step"""

    DEFAULT_MD_CONSTRAIN: StructureConstraint = []
    """The default value for the constraint applied in the md step"""

    DEFAULT_MD_RESTART: bool = False
    """The default value for whether restart using v from another md step"""

    DEFAULT_MD_CLUSTER_JOB_RES_KEYWORDS = {
        "gpu" :  ARMerConfig.MD_GPU_RES,
        "cpu" : ARMerConfig.MD_CPU_RES,
    }
    """The default res_keywords for Amber MD jobs. This is used 1. when default
    cluster_job_config is used/ or 2. when res_keywords in cluster_job_config is
    specificed."""

    def get_default_md_cluster_job_res_keywords(self, key: str) -> Dict:
        """func used for lazy determination"""
        return self.DEFAULT_MD_CLUSTER_JOB_RES_KEYWORDS[key]

    def get_default_md_cluster_job(self, key: str) -> Dict:
        """The default value for dictionary that assign arguments to
        ClusterJob.config_job and ClusterJob.wait_to_end during the MD step"""
        return {
            "gpu": {
                "cluster" : Accre(),
                "res_keywords" : self.get_default_md_cluster_job_res_keywords("gpu"),
            },
            "cpu": {
                "cluster" : Accre(),
                "res_keywords" : self.get_default_md_cluster_job_res_keywords("cpu"),
            }
        }[key]

    DEFAULT_MD_CORE_TYPE: str = "gpu"
    """The default value for the type of computing core that runs the MD."""

    DEFAULT_MD_RECORD_PERIOD_FACTOR: str = 0.001
    """The default factor for determining the record period.
    The actually period = length * factor
    The number of snapshots = 1/factor"""

    DEFAULT_MD_WORK_DIR: str = "./MD"
    """The default value for the MD working dir that contains all the temp/result
    files. """
    # endregion

    # region == hard coded MD options (only changable here) ==
    HARDCODE_CUT = 10.0
    """hard coded `cut` value"""

    HARDCODE_NTPR_RATIO = 0.01
    """hard coded `ntpr` ratio. nstlim * ratio = ntpr"""

    HARDCODE_GAMMA_LN = 5.0
    """hard coded `gamma_ln` value used when ntt=3"""

    HARDCODE_IWRAP = 1
    """hard coded `iwrap` value"""

    HARDCODE_IG = -1
    """hard coded `ig` value"""

    HARDCODE_MD_ENGINE = {
        "gpu" : "pmemd.cuda",
        "cpu" : "sander.MPI",
    }
    """hard coded names of md engines of different core types. 
    only changable by editing values here"""
    # endregion

    CONF_HEAT: Dict = {
        "ntc": 2,
        "ntf": 2,
        "cut": 10.0,
        "nstlim": 20000,
        "dt": 0.002,
        "tempi": 0.0,
        "temp0": 300.0,
        "ntpr": 0.01,
        "ntwx": 1,
        "ntt": 3,
        "gamma_ln": 5.0,
        "iwrap": 1,
        "ntr": 1,
        "restraintmask": "'@C,CA,N'",
        "restraint_wt": "2.0",
        "A_istep2": 0.9,
        "B_istep1": "A_istep2+1",
    }
    """dict() holding the settings for an Amber heating."""

    CONF_EQUI: Dict = {
        "ntx": 5,
        "irest": 1,
        "ntc": 2,
        "ntf": 2,
        "cut": 10.0,
        "nstlim": 500000,
        "dt": 0.002,
        "temp0": 300.0,
        "ntpr": 0.002,
        "ntwx": 5000,  # default 10ps (TODO support different power numbers)
        "ntt": 3,
        "gamma_ln": 5.0,
        "iwrap": 1,
        "ntr": 1,
        "restraintmask": "'@C,CA,N'",
        "restraint_wt": 2.0,  # the later two are only used when ntr = 1
    }
    """dict() holding the settings for an Amber constant pressure equilibration run."""

    CONF_PROD: Dict = {
        "ntx": 5,
        "irest": 1,
        "ntc": 2,
        "ntf": 2,
        "cut": 10.0,
        "nstlim": 50000000,
        "dt": 0.002,
        "temp0": 300.0,
        "ntpr": 0.001,
        "ntwx": 5000,  # default 10ps
        "ntt": 3,
        "gamma_ln": 5.0,
        "iwrap": 1,
        "ntr": 0,
        "restraintmask": None,
        "restraint_wt": 2.0,  # the later two are only used when ntr = 1
    }
    """dict() holding the settings for an Amber constant pressure production run."""

    RADII_MAP: Dict = {'1': 'mbondi', '2': 'mbondi2', '5': 'mbondi2', '7': 'bondi', '8': 'mbondi3'}
    """dict() holding the radii mapping for the IGB solvation model."""

    def __init__(self, parent=None):
        """Trivial constructor that optionally sets parent_ dependency. parent_ is None by default."""
        self.parent_ = parent

    def valid_box_type(self) -> bool:
        """Checks if the BOX_TYPE attribute is an acceptable value. Current allowed values are "box" and "oct"."""
        return self.BOX_TYPE in set("box oct".split())

    def required_executables(self) -> List[str]:
        """A hardcoded list of required executables for Amber."""
        return [
            self.HARDCODE_MD_ENGINE["cpu"],
            self.HARDCODE_MD_ENGINE["gpu"],
            "tleap",
            "ambpdb",
            "parmchk2",
            "antechamber",
            "cpptraj",
        ]

    def required_env_vars(self) -> List[str]:
        """A hardcoded list of required enviornment variables for Amber."""
        return [self.HOME]

    def required_py_modules(self) -> List[str]:
        """ """
        return list()

    @classmethod
    def display(cls) -> None:
        """Method that prints out all settings for the AmberConfig class to the stdout."""
        dash_line: str = "-" * 40
        dis_info = f"AmberConfig settings:{os.linesep}{dash_line}{get_str_for_print_class_var(cls)}"
        _LOGGER.info(dis_info)

    def __getitem__(self, key: str) -> Any:
        """Getter that enables [] accession of AmberConfig() attributes."""
        if key.count("."):
            key1, key2 = key.split(".", 1)
            return getattr(self, key1)[key2]
        else:
            return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Setter that enables [] accession of AmberConfig() attributes with value validation."""
        if key.count("."):
            key1, key2 = key.split(".")
            AmberConfig.__dict__[key1][key2] = value
        else:
            setattr(self, key, value)

        if not self.valid_box_type():
            # TODO(CJ): make a custom error for this part
            raise TypeError()

    def get_engine(self, mode: str) -> str:
        """Getter that returns the path to either the CPU or GPU engine configured for Amber.

        Args:
                mode: The mode that amber will be run in. Allowed values are "CPU" and "GPU".

        Returns:
                Path to the specified engine.

        Raises:
                TypeError if an invalid engine type is supplied.
        """
        if mode == "CPU":
            return self.CPU_ENGINE
        elif mode == "GPU":
            return self.GPU_ENGINE
        else:
            # TODO(CJ): add a custom error for this part
            raise TypeError()


def default_amber_config() -> AmberConfig:
    """Creates a deep-copied default version of the AmberConfig() class."""
    return deepcopy(AmberConfig())
