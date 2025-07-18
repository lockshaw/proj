from . import subprocess_trace as subprocess
import sys
import os
import logging
from .config_file import ProjectConfig
from .browser import open_in_browser

_l = logging.getLogger(__name__)


def postprocess_coverage_data(config: ProjectConfig) -> None:
    cwd = config.coverage_build_dir

    subprocess.run(
        [
            "lcov",
            "--capture",
            "--directory",
            ".",
            "--output-file",
            "main_coverage.info",
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
    )

    # only keep the coverage info of the lib directory
    subprocess.run(
        [
            "lcov",
            "--extract",
            "main_coverage.info",
            f"{config.base}/lib/*",
            "--output-file",
            "main_coverage.info",
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
    )

    # filter out .dtg.h, .dtg.cc, and test code
    subprocess.run(
        [
            "lcov",
            "--remove",
            "main_coverage.info",
            f"{config.base}/lib/*.dtg.h",
            f"{config.base}/lib/*.dtg.cc",
            f"{config.base}/lib/*/test/**",
            "--output-file",
            "main_coverage.info",
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
    )


def view_coverage_data(config: ProjectConfig, browser: bool) -> None:
    cwd = config.coverage_build_dir

    if browser:
        _l.info("opening coverage info in browser")
        subprocess.run(
            [
                "genhtml",
                "main_coverage.info",
                "--output-directory",
                "code_coverage",
            ],
            stderr=sys.stdout,
            cwd=cwd,
            env=os.environ,
        )

        open_in_browser("code_coverage/index.html", cwd=cwd)
    else:
        subprocess.run(
            [
                "lcov",
                "--list",
                "main_coverage.info",
            ],
            stderr=sys.stdout,
            cwd=cwd,
            env=os.environ,
        )
