"""Defines AmberConfig() which holds configuration settings for enzy_htp to interface with the 
Amber software package. In addition to holding Amber settings, AmberConfig() creates the input
files for minimization, heating, constant pressure production, and constant pressure
equilibration. File also contains default_amber_config() which creates a default version
of the AmberConfig() object.

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>

Date: 2022-06-02
"""
from copy import deepcopy
from typing import Any, List, Dict

from .base_config import BaseConfig
from .system_config import SystemConfig
from .armer_config import ARMerConfig

from enzy_htp.core.clusters.accre import Accre
from enzy_htp.core.general import get_str_for_print_class_var
from enzy_htp.core.logger import _LOGGER

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
    """build_md_parameterizer: Solvation Box type. Allowed values are 'box' and 'oct'"""

    DEFAULT_SOLVATE_BOX_SIZE: float = 10.0
    """build_md_parameterizer: Solvation Box size."""

    DEFAULT_PARAMETERIZER_TEMP_DIR: str = f"{SystemConfig.SCRATCH_DIR}/amber_parameterizer"
    """build_md_parameterizer: The default temporary working directory that contains all the files generated by the AmberParameterizer"""
    
    DEFAULT_KEEP_TLEAP_IN: bool = False
    """build_md_parameterizer: The default behavior of whether keeping tleap.in file generated during the parameterization."""
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
    """default value for the algorithm of the thermostat.
    Change HARDCODE_GAMMA_LN for non-default gamma_ln value"""

    DEFAULT_MD_PRESSURE_SCALING: str = "isotropic"
    """default value for the pressure scaling of the md step"""

    DEFAULT_MD_CONSTRAIN = []
    """The default value for the constraint applied in the md step.
    Has to be empty in the source code otherwise causes a circular import"""

    DEFAULT_MD_RESTART: bool = False
    """The default value for whether restart using v from another md step"""

    DEFAULT_MD_CLUSTER_JOB_RES_KEYWORDS = {
        "gpu" :  deepcopy(ARMerConfig.MD_GPU_RES),
        "cpu" : deepcopy(ARMerConfig.MD_CPU_RES),
    }
    """The default res_keywords for Amber MD jobs. This is used 1. when default
    cluster_job_config is used/ or 2. when res_keywords in cluster_job_config is
    specificed."""

    def get_default_md_cluster_job_res_keywords(self, key: str) -> Dict:
        """func used for lazy determination"""
        return deepcopy(self.DEFAULT_MD_CLUSTER_JOB_RES_KEYWORDS[key])

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

    # region == Default values for StructureConstrain ==
    SUPPORTED_CONSTRAINT_TYPE = ["cartesian_freeze", "backbone_freeze", "distance_constraint",
                                 "angle_constraint", "dihedral_constraint", "residue_pair_constraint"]

    DEFAULT_CARTESIAN_FREEZE_WEIGHT = 2.0
    """the default value for restraint_wt that used in CartesianFreeze.
    (unit: kcal*mol^-1*A^-2) (form: k(dx)^2 dx is the cartesian coord difference)"""

    DEFAULT_DISANG_FILEPATH = "{mdstep_dir}/0.rs"
    """the default path for DISANG file in geometry(nmropt) constraint.
    {mdstep_dir} means it will be replaced my the actually mdstep_dir when 
    used in a real step"""
    
    DEFAULT_DISTANCE_CONSTRAINT_SETTING = {
        "ialtd" : 0,
        "r1" : "x-0.25",
        "r2" : "x-0.05",
        "r3" : "x+0.05",
        "r4" : "x+0.25",
        "rk2": 200.0, "rk3": 200.0,
    }
    """the default settings for distance constraint in Amber. (Amber20 manual 27.1)
    Default using flat-welled linear-edge parabola with flat region span +-0.05A the target distance.

    Supported constraint energy functions (pmemd):
        (ialtd = 0)
        >  r1, r2, r3, r4 define a flat-welled parabola which becomes linear beyond a specified distance. i.e.
        >
        >     \                       /
        >      \                     /
        >       \                   /
        >        .                 .
        >          .             .
        >             ._______.
        >
        >       r1    r2      r3   r4
        >
        >  "\" = lower bound linear response region 
        >  "/" = lower bound linear response region 
        >  "." = parobola (left: rk2(r-r2)^2, rk3(r-r3)^2)
        >  "_" = flat region
        >  (from https://ambermd.org/Questions/constraints.html)

        In EnzyHTP, when 'x-###' format is used. The r value is calulated from the target distance d.
        Otherwise the absolute value is applied.

        TODO add more when used"""

    DEFAULT_ANGLE_CONSTRAINT_SETTING = {
        "ialtd" : 0,
        "r1" : "x-30.0",
        "r2" : "x-10.0",
        "r3" : "x+10.0",
        "r4" : "x+30.0",
        "rk2": 200.0, "rk3": 200.0,
    }
    """the default settings for angle constraint in Amber.
    (see DEFAULT_DISTANCE_CONSTRAINT_SETTING for more details)"""

    DEFAULT_DIHEDRAL_CONSTRAINT_SETTING = {
        "ialtd" : 0,
        "r1" : "x-30.0",
        "r2" : "x-10.0",
        "r3" : "x+10.0",
        "r4" : "x+30.0",
        "rk2": 200.0, "rk3": 200.0,
    }
    """the default settings for dihedral constraint in Amber.
    (see DEFAULT_DISTANCE_CONSTRAINT_SETTING for more details)"""
    # endregion

    # region == hard coded MD options (only changable here) ==
    HARDCODE_CUT = 10.0
    """hard coded `cut` value"""

    HARDCODE_NCYC_RATIO = 0.5
    """hard coded `ncyc` ratio. ncyc = ratio * maxcyc"""

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

    # region == hard coded MMPBSA options ==
    HARDCODE_MMMPBSA_MPI_ENGINE = "MMPBSA.py.MPI"
    """hard coded names of MMPBSA.py.MPI engines in case user compiled into
    a different name"""

    DEFAULT_MMPBSA_RES_KEYWORDS: Dict = {
        'core_type' : 'cpu',
        'nodes':'1',
        'node_cores' : '24',
        'job_name' : 'mmpbsa_EnzyHTP',
        'partition' : '<fillthis>',
        'mem_per_core' : '2G', # in GB.
        'walltime' : '24:00:00',
        'account' : '<fillthis>',
        }
    """The default value for the resource configuration of mmpbsa calculation."""

    def get_default_mmpbsa_job_res_keywords(self) -> Dict:
        """function for lazy resolution."""
        return deepcopy(self.DEFAULT_MMPBSA_RES_KEYWORDS)

    def get_default_mmpbsa_cluster_job_config(self):
        """The default value for dictionary that assign arguments to
        ClusterJob.config_job during MMPBSA"""
        return {
            "cluster" : Accre(),
            "res_keywords" : self.get_default_mmpbsa_job_res_keywords(),
        }
    # endregion

    RADII_MAP: Dict = {'1': 'mbondi', '2': 'mbondi2', '5': 'mbondi2', '7': 'bondi', '8': 'mbondi3'}
    """dict() holding the radii mapping for the IGB solvation model."""

    def __init__(self, parent=None):
        """Trivial constructor that optionally sets parent_ dependency. parent_ is None by default."""
        self.parent_ = parent

    def valid_box_type(self) -> bool:
        """Checks if the BOX_TYPE attribute is an acceptable value. Current allowed values are "box" and "oct"."""
        return self.DEFAULT_SOLVATE_BOX_TYPE in set("box oct".split())

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
            "add_pdb",
            "ante-MMPBSA.py",
            "parmed",
            self.HARDCODE_MMMPBSA_MPI_ENGINE,
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

def default_amber_config() -> AmberConfig:
    """Creates a deep-copied default version of the AmberConfig() class."""
    return deepcopy(AmberConfig())
