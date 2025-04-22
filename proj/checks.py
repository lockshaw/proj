from enum import (
    StrEnum,
)
from .config_file import (
    ProjectConfig,
)
from .format import (
    run_formatter_check,
)
from .dtgen import (
    run_dtgen,
)
from .cmake import (
    cmake_all,
)
import multiprocessing
from .build import (
    build_targets,
)
from .testing import (
    run_tests,
)
from .targets import (
    LibTarget,
)
import logging

_l = logging.getLogger(__name__)

KERNELS_TESTS = LibTarget.from_str('kernels').test_target

class Check(StrEnum):
    FORMAT = 'format'
    BUILD = 'build'
    CPU_TESTS = 'cpu-tests'
    GPU_TESTS = 'gpu-tests'
    CPU_CI = 'cpu-ci'
    GPU_CI = 'gpu-ci'

def run_check(config: ProjectConfig, check: Check, verbosity: int) -> None:
    if check == Check.FORMAT:
        run_formatter_check(config)
    elif check == Check.BUILD:
        run_build_check(config, verbosity=verbosity)
    elif check == Check.CPU_TESTS:
        run_cpu_tests(config, verbosity=verbosity)
    elif check == Check.GPU_TESTS:
        run_gpu_tests(config, verbosity=verbosity)
    elif check == Check.CPU_CI:
        run_cpu_ci(config, verbosity=verbosity)
    else:
        assert check == Check.GPU_CI
        run_gpu_ci(config, verbosity=verbosity)

def run_build_check(config: ProjectConfig, verbosity: int) -> None:
    run_dtgen(
        root=config.base,
        config=config,
        force=True,
    )
    cmake_all(config, fast=False, trace=False)

    build_targets(
        config=config,
        targets=config.all_build_targets,
        dtgen_skip=True,
        jobs=multiprocessing.cpu_count(),
        verbosity=verbosity,
        build_dir=config.debug_build_dir,
    )

def run_cpu_tests(config: ProjectConfig, verbosity: int) -> None:
    run_dtgen(
        root=config.base,
        config=config,
        force=True,
    )
    cmake_all(config, fast=False, trace=False)

    cpu_test_targets = [t for t in config.all_test_targets if t != KERNELS_TESTS]
    build_targets(
        config=config,
        targets=[target.build_target for target in cpu_test_targets],
        dtgen_skip=True,
        jobs=multiprocessing.cpu_count(),
        verbosity=verbosity,
        build_dir=config.debug_build_dir,
    )

    _l.info('Running tests %s', cpu_test_targets)
    run_tests(cpu_test_targets, config.debug_build_dir, debug=False)

def run_cpu_ci(config: ProjectConfig, verbosity: int) -> None:
    _l.info('Running formatter check...')
    run_formatter_check(config)

    _l.info('Running dtgen --force...')
    run_dtgen(
        root=config.base,
        config=config,
        force=True,
    )
    _l.info('Running cmake...')
    cmake_all(config, fast=False, trace=False)

    test_targets = list(config.all_test_targets)
    all_build_targets = [target.build_target for target in test_targets] + list(config.all_build_targets)
    _l.info('Building %s', all_build_targets)
    build_targets(
        config=config,
        targets=all_build_targets,
        dtgen_skip=True,
        jobs=multiprocessing.cpu_count(),
        verbosity=verbosity,
        build_dir=config.coverage_build_dir,
    )

    cpu_test_targets = [t for t in test_targets if t != KERNELS_TESTS]
    _l.info('Running tests %s', cpu_test_targets)
    run_tests(cpu_test_targets, config.coverage_build_dir, debug=False)

def run_gpu_tests(config: ProjectConfig, verbosity: int) -> None:
    run_dtgen(
        root=config.base,
        config=config,
        force=True,
    )
    cmake_all(config, fast=False, trace=False)

    test_targets = [KERNELS_TESTS]
    build_targets(
        config=config,
        targets=[target.build_target for target in test_targets],
        dtgen_skip=True,
        jobs=multiprocessing.cpu_count(),
        verbosity=verbosity,
        build_dir=config.debug_build_dir,
    )

    run_tests(test_targets, config.debug_build_dir, debug=False)

def run_gpu_ci(config: ProjectConfig, verbosity:int) -> None:
    run_gpu_tests(config, verbosity) 
