from contextlib import contextmanager
from pathlib import Path
import shutil
from typing import (
    Iterator,
)
from proj.__main__ import (
    MainCmakeArgs,
    main_cmake,
)
import tempfile
from dataclasses import dataclass
from proj.config_file import (
    ProjectConfig,
    load_config,
)

MAX_VERBOSITY = 100

TEST_PROJECTS_DIR = Path(__file__).parent / 'example-projects'

@contextmanager
def TemporaryDirectory(delete: bool = True) -> Iterator[str]:
    if delete:
        with tempfile.TemporaryDirectory() as d:
            yield d
    else:
        d = tempfile.mkdtemp()
        yield d

@contextmanager
def project_instance(project_name: str) -> Iterator[Path]:
    with TemporaryDirectory(delete=False) as d:
        dst = Path(d) / project_name
        shutil.copytree(src=TEST_PROJECTS_DIR / project_name, dst=dst)
        yield dst

@contextmanager
def cmade_project_instance(project_name: str) -> Iterator[Path]:
    with project_instance(project_name) as d:
        cmake_args = MainCmakeArgs(
            path=d,
            fast=False,
            trace=False,
            dtgen_skip=False,
            verbosity=MAX_VERBOSITY,
        )
        main_cmake(cmake_args)

        yield d

@dataclass(frozen=True, eq=True)
class LoadedProject:
    path: Path
    config: ProjectConfig

@contextmanager
def loaded_cmade_project_instance(project_name: str) -> Iterator[LoadedProject]:
    with cmade_project_instance(project_name) as d:
        yield LoadedProject(
            path=d,
            config=load_config(d),
        )
