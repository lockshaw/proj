from .config_file import ProjectConfig
from typing import (
    Optional,
    BinaryIO,
    Mapping,
)
import logging
from . import subprocess_trace as subprocess

def run_doxygen(
    config: ProjectConfig,
    log_level: int,
    stdout: Optional[BinaryIO],
    stderr: Optional[BinaryIO],
    env: Mapping[str, str],
) -> bool:
    assert config.doxygen_enabled

    env = {
        **env,
        "FF_HOME": str(config.base),
    }

    config.doxygen_dir.mkdir(exist_ok=True, parents=True)

    cmd: str
    if log_level <= logging.DEBUG:
        cmd = "doxygen docs/doxygen/Doxyfile 2>&1"
    else:
        cmd = "doxygen docs/doxygen/Doxyfile 2>&1 | grep -v DOT_GRAPH_MAX_NODES"


    stdout_contents, stderr_contents = subprocess.tee_output(
        cmd,
        env=env,
        stdout=stdout,
        stderr=stderr,
        cwd=config.base,
        shell=True,
        check=False,
    )

    return len(stdout_contents.strip()) == 0 and len(stderr_contents.strip()) == 0
