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
from tempfile import TemporaryDirectory

MAX_VERBOSITY = 100

TEST_PROJECTS_DIR = Path(__file__).parent / 'example-projects'

@contextmanager
def project_instance(project_name: str) -> Iterator[Path]:
    with TemporaryDirectory() as d:
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

