from .config_file import ProjectConfig
from typing import Iterable
from . import subprocess_trace as subprocess
import logging
import sys
import os
from pathlib import Path
from .failure import fail_with_error
from .dtgen import run_dtgen

def build_targets(
    config: ProjectConfig,
    targets: Iterable[str],
    dtgen_skip: bool,
    jobs: int,
    verbosity: int,
    cwd: Path,
) -> None:
    _targets = list(sorted(set(targets)))
    if len(_targets) == 0:
        fail_with_error('No build targets selected')

    if not dtgen_skip:
        run_dtgen(
            root=config.base,
            config=config,
            force=False,
        )

    subprocess.check_call(
        [
            "make",
            "-j",
            str(jobs),
            *_targets,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": config.base,
            **({"VERBOSE": "1"} if verbosity <= logging.DEBUG else {}),
        },
        stderr=sys.stdout,
        cwd=cwd,
    )
