"""Defines an EnvironmentManager class that checks for applications and environment variables that enzy_htp needs. Also stores values for these variables 
and serves as interface for running external applications.

Author: Chris Jurich, <chris.jurich@vanderbilt.edu>
Date: 2022-02-12
"""
import os
import time
import shutil
import importlib
import logging
from pathlib import Path
from typing import List, Union
from subprocess import CompletedProcess, SubprocessError, run

from enzy_htp.core.general import get_localtime

from .logger import _LOGGER
from .exception import MissingEnvironmentElement


class EnvironmentManager:
    """Serves as general interface between module and the current computer environment (shell).
    Checks whether given applications and environment variables are set in the current environment.
    After check, stores names of executables.
    Serves as interface for running commands on system.


    Attributes:
            env_vars_: A list of strings containing environment variables to check for.
            py_modules_: A list of strings correspond to python modules to check for.
            executables_: a list of strings containing executables to check for.
            missing_env_vars_: A list of strings corresponding to environment variables that are missing.
            missing_py_modules_: A list of strings corresponding to python modules that are missing.
            missing_executables_: A list of strings corresponding to executables that are missing.
    """

    def __init__(self, **kwargs):
        """Initializes object, optionally with starting environment variables and executables."""
        self.env_vars_ = kwargs.get("env_vars", [])
        self.executables_ = kwargs.get("executables", [])
        self.py_modules_ = kwargs.get("py_modules", [])
        self.mapper = dict()
        self.missing_env_vars_ = []
        self.missing_py_modules_ = []
        self.missing_executables_ = []

    #region ==environment related==
    def add_executable(self, exe_name: str) -> None:
        """Adds the name of an executable to check for."""
        self.executables_.append(exe_name)

    def add_env_var(self, env_var: str) -> None:
        """Adds the name of an environment variable to check for."""
        self.env_vars_.append(env_var)

    def check_env_vars(self) -> None:
        """Checks which environment variables are defined, storing those which are not defined."""
        for env_var in self.env_vars_:
            if os.getenv(env_var) is None:
                self.missing_env_vars_.append(env_var)

    def __exe_exists(self, exe_name: str) -> bool:
        """Helper method that checks if executable exists in current environment."""
        full_path = os.path.expandvars(exe_name)
        if Path(full_path).exists():
            return True
        return shutil.which(exe_name) is not None

    def check_executables(self) -> None:
        """Checks which executables are available in the system, storing paths to those which exist or noting if they are not found."""
        for exe in self.executables_:
            if not self.__exe_exists(exe):
                self.missing_executables_.append(exe)
                continue

            fpath = os.path.expandvars(exe)
            if Path(fpath).exists():
                self.mapper[exe] = fpath
            else:
                self.mapper[exe] = shutil.which(exe)

    def check_python_modules(self) -> None:
        """Checks which python modules are availabe in the system, storing those that are missing."""
        for pm in self.py_modules_:
            try:
                _ = importlib.import_module(pm)
            except ModuleNotFoundError:
                self.missing_py_modules_.append(pm)

    def display_missing(self) -> None:
        """Displays a list of missing environment variables and exectuables to the logger. Should be called after .check_environment() and .check_env_vars()."""
        if not self.is_missing():
            _LOGGER.info("Environment has all required elements!")
            return
        _LOGGER.warning("Environment is missing some required elements...")

        if len(self.missing_executables_):
            _LOGGER.warning("\tMissing excecutables:")
            for me in self.missing_executables_:
                _LOGGER.warning(f"\t\t{me}")

        if len(self.missing_env_vars_):
            _LOGGER.warning("\tMissing environment variables:")
            for mev in self.missing_env_vars_:
                _LOGGER.warning(f"\t\t{mev}")

    def check_environment(self) -> None:
        """Preferred client method for validating environment. Performs checks and logs output."""

        self.check_env_vars()
        self.check_executables()
        self.check_python_modules()

    def reset(self) -> None:
        """Resets internal lists of env vars and executables."""
        self.executables_ = []
        self.missing_executables_ = []
        self.env_vars_ = []
        self.missing_env_vars_ = []

    def is_missing(self) -> bool:
        """Checks if any executables or environment variables are missing."""
        return len(self.missing_executables_) or len(self.missing_env_vars_) or len(self.missing_py_modules_)

    def missing_executables(self) -> List[str]:
        """Getter for the missing executables in the environment."""
        return self.missing_executables_

    def missing_env_vars(self) -> List[str]:
        """Getter for the missing environment variables in the environment."""
        return self.missing_env_vars_

    def missing_py_modules(self) -> List[str]:
        """ """
        return self.missing_py_modules_
    #endregion

    #region ==shell command==
    def run_command(self,
                    exe: str,
                    args: Union[str, List[str]],
                    try_time: int = 1,
                    wait_time: float = 3.0,
                    timeout: Union[None, float] = None,
                    stdout_return_only: bool = False,
                    quiet_fail:bool = False,
                    log_level: str = "info",) -> Union[CompletedProcess, str]:
        """Interface to run a command with the exectuables specified by exe as well as a list of arguments.
        Args:
            exe:
                the target exectuables of runnnig.
                !NOTE! Need to register in the corresponding config.required_executables() first.
            args:
                the arguments used for the command. str or list of str
            try_time:
                how many time this command will try if fail with SubprocessExceptions.
                This is useful when the command is run on a HPC which have time-dependent unrepeatable error.
            wait_time:
                the time interval between each retry (used when retry_num > 1)
                (Unit: s)
            timeout:
                how long the command is allowed to run.
                (do not set this if the command is supposed to take long like "pmemd",
                use this when the command is supposed to be fast like "squeue" but may take long time if there
                are some unrepeatable error thus allow taking next retry earlier.)
                (Unit: s)
            quiet_fail:
                #TODO(CJ)
            log_level: the logging level that non-error/warning loggings in this function goes to.

        Returns:
            return the CompletedProcess object

        Raises:
            MissingEnvironmentElement
            SystemExit
            """
        # init
        log_level = getattr(logging, log_level.upper(), None)
        if not log_level:
            _LOGGER.error(f"log_level ({log_level}) not supported")

        if isinstance(args, list):
            args = " ".join(args)
        cmd = f"{self.mapper.get(exe,exe)} {args}"

        # handle missing exe
        if exe in self.missing_executables_ or not self.__exe_exists(exe):
            _LOGGER.error(f"This environment is missing '{exe}' and cannot run the command '{cmd}'")
            raise MissingEnvironmentElement
        if exe not in self.mapper:
            _LOGGER.warning(f"(dev-only) Using unregistered executable: '{exe}'")
            _LOGGER.warning(f"    Please add it to corresponding config.required_executables if this is a long-term use")

        # run the command
        _LOGGER.log(log_level, f"Running command: `{cmd}`...") # TODO may provide an option for higher level
        for i in range(try_time):
            try:
                this_run = run(cmd, timeout=timeout, check=True, text=True, shell=True, capture_output=True)
                _LOGGER.debug("Command finished!")
            except SubprocessError as e:
                this_error = e
                _LOGGER.warning(f"Error running {cmd}: {repr(e)}")
                if not quiet_fail:
                    _LOGGER.warning(f"    stderr: {str(e.stderr).strip()}")
                    _LOGGER.warning(f"    stdout: {str(e.stdout).strip()}")
                if try_time > 1:
                    _LOGGER.warning(f"trying again... ({i+1}/{try_time})")
            else:  # untill there's no error
                _LOGGER.log(log_level, f"finished `{cmd}` after {i+1} tries @{get_localtime()}")
                if stdout_return_only:
                    return str(this_run.stdout).strip()
                else:
                    return this_run
            # wait before next try
            time.sleep(wait_time)

        # exceed the try time
        _LOGGER.error(f"Failed running `{cmd}` after {try_time} tries @{get_localtime()}")
        raise this_error

    #endregion

    def __getattr__(self, key: str) -> str:
        """Allows accession into acquired executables."""
        if key.startswith('__') and key.endswith('__'): # this is critical for pickle to work (https://stackoverflow.com/questions/50888391/pickle-of-object-with-getattr-method-in-python-returns-typeerror-object-no)
            raise AttributeError
        if key not in self.mapper and key in self.executables_:
            _LOGGER.error(
                f"Executable '{key}' is in list of executables to check but has not been searched for yet. Call .check_environment() first. Exiting..."
            )
            raise AttributeError(key)

        try:
            return self.mapper[key]
        except KeyError:
            raise AttributeError(key)
