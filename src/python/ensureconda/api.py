import subprocess
from functools import partial
from typing import TYPE_CHECKING, Callable, Optional

from packaging.version import Version

from ensureconda.installer import install_conda_exe, install_micromamba
from ensureconda.resolve import (
    conda_executables,
    conda_standalone_executables,
    mamba_executables,
    micromamba_executables,
)

if TYPE_CHECKING:
    from _typeshed import StrPath


def determine_mamba_version(exe: "StrPath") -> Version:
    """Determine the version of mamba on the given executable.

    Typical output of `mamba --version` for v1 is:
    ```
    mamba 1.4.7
    conda 23.5.0
    ```

    Typical output of `mamba --version` for v2 is identical to micromamba:
    ```
    2.0.8
    ```
    """
    print(f"Determining mamba version for {exe}")
    out = subprocess.check_output([exe, "--version"], encoding="utf-8").strip()
    for line in out.splitlines(keepends=False):
        if line.startswith("mamba"):
            print(f"Determined mamba version for {exe}: {line.split()[-1]}")
            return Version(line.split()[-1])
    # Not v1 style output, so fall back to micromamba version detection
    print(f"Falling back to micromamba version detection for {exe}")
    return determine_micromamba_version(exe)


def determine_micromamba_version(exe: "StrPath") -> Version:
    print(f"Determining micromamba version for {exe}")
    out = subprocess.check_output([exe, "--version"], encoding="utf-8").strip()
    for line in out.splitlines(keepends=False):
        print(f"Determined micromamba version for {exe}: {line.split()[-1]}")
        return Version(line.split()[-1])
    print(f"Failed to determine micromamba version for {exe}")
    return Version("0.0.0")


def determine_conda_version(exe: "StrPath") -> Version:
    print(f"Determining conda version for {exe}")
    out = subprocess.check_output([exe, "--version"], encoding="utf-8").strip()
    for line in out.splitlines(keepends=False):
        if line.startswith("conda"):
            print(f"Determined conda version for {exe}: {line.split()[-1]}")
            return Version(line.split()[-1])
    print(f"Failed to determine conda version for {exe}")
    return Version("0.0.0")


def ensureconda(
    *,
    mamba: bool = True,
    micromamba: bool = True,
    conda: bool = True,
    conda_exe: bool = True,
    no_install: bool = False,
    min_conda_version: Optional[Version] = None,
    min_mamba_version: Optional[Version] = None,
) -> "Optional[StrPath]":
    """Ensures that conda is installed

    Parameters
    ----------
    mamba:
        Allow resolving mamba
    micromamba:
        Allow resolving micromamba.  Micromamba implements a subset of features of conda su
        it may not be the correct choice in all cases.
    conda:
        Allow resolving conda.
    conda_exe
        Allow resolving conda-standalong
    min_conda_version:
        Minimum version of conda required
    min_mamba_version:
        Minimum version of mamba required

    Returns the path to a conda executable.
    """

    def version_constraint_met(
        executable: "StrPath",
        min_version: Optional[Version],
        version_fn: Callable[["StrPath"], Version],
    ) -> bool:
        if min_version is None:
            return True
        version = version_fn(executable)
        result: bool = version >= min_version
        if result:
            print(
                f"Version constraint satisfied: "
                f"{executable} >= {min_version=} by {version}"
            )
        else:
            print(
                f"Version constraint not satisfied: "
                f"{executable} >= {min_version=} by {version}"
            )
        return result

    conda_constraints_met = partial(
        version_constraint_met,
        min_version=min_conda_version,
        version_fn=determine_conda_version,
    )
    mamba_constraints_met = partial(
        version_constraint_met,
        min_version=min_mamba_version,
        version_fn=determine_mamba_version,
    )
    micromamba_constraints_met = partial(
        version_constraint_met,
        min_version=min_mamba_version,
        version_fn=determine_micromamba_version,
    )

    if mamba:
        print("Checking mamba executables")
        for exe in mamba_executables():
            if exe and mamba_constraints_met(exe):
                print(f"Found mamba executable: {exe}")
                return exe
    if micromamba:
        print("Checking micromamba executables")
        for exe in micromamba_executables():
            if exe and micromamba_constraints_met(exe):
                print(f"Found micromamba executable: {exe}")
                return exe
        if not no_install:
            print("Installing micromamba")
            maybe_exe = install_micromamba()
            if maybe_exe is not None and micromamba_constraints_met(maybe_exe):
                print(f"Installed micromamba executable: {maybe_exe}")
                return maybe_exe
    if conda:
        print("Checking conda executables")
        for exe in conda_executables():
            if exe and conda_constraints_met(exe):
                print(f"Found conda executable: {exe}")
                return exe
    if conda_exe:
        print("Checking conda-standalone executables")
        for exe in conda_standalone_executables():
            if exe and conda_constraints_met(exe):
                print(f"Found conda-standalone executable: {exe}")
                return exe
        if not no_install:
            print("Installing conda-standalone")
            maybe_exe = install_conda_exe()
            if maybe_exe is not None and conda_constraints_met(maybe_exe):
                print(f"Installed conda-standalone executable: {maybe_exe}")
                return maybe_exe
    return None
