from typing import (
    Mapping,
    List,
    Iterable,
)
import os
import shlex
from . import subprocess_trace as subprocess
from pathlib import Path
from enum import StrEnum
import sys
import shutil
from .config_file import ProjectConfig
from . import fix_compile_commands

def run_cmake(cmake_args: Iterable[str], require_shell: bool, cwd: Path) -> None:
    subprocess.check_call(
        [
            "cmake",
            *cmake_args,
            "../..",
        ],
        stderr=sys.stderr,
        cwd=cwd,
        env=os.environ,
        shell=require_shell,
    )

def render_args(arg_map: Mapping[str, str], trace: bool) -> List[str]:
    cmake_args = [f"-D{k}={v}" for k, v in arg_map.items()]
    cmake_args += shlex.split(os.environ.get("CMAKE_FLAGS", ""))
    if trace:
        cmake_args += ["--trace", "--trace-expand", "--trace-redirect=trace.log"]
    return cmake_args

class BuildMode(StrEnum):
    RELEASE = 'release'
    DEBUG = 'debug'
    BENCHMARK = 'benchmark'
    COVERAGE = 'coverage'

def get_arg_map(config: ProjectConfig, mode: BuildMode) -> Mapping[str, str]:
    if mode == BuildMode.RELEASE:
        return config.release_cmake_flags
    elif mode == BuildMode.DEBUG:
        return config.debug_cmake_flags
    elif mode == BuildMode.BENCHMARK:
        return config.benchmark_cmake_flags
    else:
        assert mode == BuildMode.COVERAGE
        return config.coverage_cmake_flags

def get_build_dir(config: ProjectConfig, mode: BuildMode) -> Path:
    if mode == BuildMode.RELEASE:
        return config.release_build_dir
    elif mode == BuildMode.DEBUG:
        return config.debug_build_dir
    elif mode == BuildMode.BENCHMARK:
        return config.benchmark_build_dir
    else:
        assert mode == BuildMode.COVERAGE
        return config.coverage_build_dir

def cmake(config: ProjectConfig, mode: BuildMode, fast: bool, trace: bool) -> None:
    arg_map = get_arg_map(config, mode)
    build_dir = get_build_dir(config, mode)

    if not fast and build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(exist_ok=True, parents=True)

    rendered_args = render_args(arg_map, trace=trace)

    run_cmake(rendered_args, require_shell=config.cmake_require_shell, cwd=build_dir)

    if mode == BuildMode.DEBUG:
        COMPILE_COMMANDS_FNAME = "compile_commands.json"
        if config.fix_compile_commands:
            fix_compile_commands.fix_file(
                compile_commands=config.debug_build_dir / COMPILE_COMMANDS_FNAME,
                base_dir=config.base,
            )

        with (config.base / COMPILE_COMMANDS_FNAME).open("w") as f:
            subprocess.check_call(
                [
                    "compdb",
                    "-p",
                    ".",
                    "list",
                ],
                stdout=f,
                cwd=config.debug_build_dir,
                env=os.environ,
            )

def cmake_all(config: ProjectConfig, fast: bool, trace: bool) -> None:
    for mode in BuildMode:
        cmake(config=config, mode=mode, fast=fast, trace=trace)
