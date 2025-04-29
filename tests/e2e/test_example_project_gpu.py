import pytest
from ..project_utils import (
    project_instance as _project_instance,
    cmade_project_instance as _cmade_project_instance,
    loaded_cmade_project_instance as _loaded_cmade_project_instance,
    LoadedProject,
)
from .e2e_utils import (
    check_cmd_succeeds,
    check_cmd_fails,
)
from typing import (
    Iterable,
    Mapping,
    ContextManager,
)
import logging
from pathlib import Path
from proj.target_resolution import (
    fully_resolve_run_target,
)
from proj.targets import (
    GenericTestCaseTarget, 
    GenericTestSuiteTarget,
)
import multiprocessing

def project_instance() -> ContextManager[Path]:
    return _project_instance('gpu')

def cmade_project_instance() -> ContextManager[Path]:
    return _cmade_project_instance('gpu')

def loaded_cmade_project_instance() -> ContextManager[LoadedProject]:
    return _loaded_cmade_project_instance('gpu')

_l = logging.getLogger(__name__)

FAIL_KERNELS_TEST_CPU = 'PROJ_TESTS_FAIL_KERNELS_CALL_KERNELS_CPU'
FAIL_KERNELS_TEST_GPU = 'PROJ_TESTS_FAIL_KERNELS_CALL_KERNELS_GPU'
FAIL_NOT_KERNELS_TEST_CPU = 'PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS_CPU'
FAIL_NOT_KERNELS_TEST_GPU = 'PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS_GPU'
FAIL_NO_CUDA_TEST = 'PROJ_TESTS_FAIL_NO_CUDA_CALL_NO_CUDA'
FAIL_ONLY_CUDA_TEST = 'PROJ_TESTS_FAIL_ONLY_CUDA_CALL_ONLY_CUDA'

CPU_TEST_FLAGS = [
    FAIL_KERNELS_TEST_CPU,
    FAIL_NOT_KERNELS_TEST_CPU,
    FAIL_NO_CUDA_TEST,
]

CUDA_TEST_FLAGS = [
    FAIL_KERNELS_TEST_GPU,
    FAIL_NOT_KERNELS_TEST_GPU,
    FAIL_ONLY_CUDA_TEST,
]

ALL_TEST_FLAGS = CPU_TEST_FLAGS + CUDA_TEST_FLAGS

def make_fail_env(to_fail: Iterable[str]) -> Mapping[str, str]:
    return {
        t: 'y' for t in to_fail
    }

def make_pass_env(to_pass: Iterable[str]) -> Mapping[str, str]:
    _to_pass = set(to_pass)
    return make_fail_env([t for t in ALL_TEST_FLAGS if t not in _to_pass])

@pytest.mark.e2e
@pytest.mark.slow
def test_fully_resolve_run_target() -> None:
    with loaded_cmade_project_instance() as p:
        generic_test_case = GenericTestCaseTarget(
            test_suite=GenericTestSuiteTarget('not-kernels'),
            test_case_name='call_not_kernels_cpu',
        )

        resolved = fully_resolve_run_target(
            config=p.config,
            build_dir=p.config.debug_build_dir,
            unresolved_target=generic_test_case,
            jobs=multiprocessing.cpu_count(),
            verbosity=logging.INFO,
            skip_gpu=False,
        )

        assert resolved == generic_test_case.cpu_test_case.run_target

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_test() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'test',
        ], env=make_fail_env(CUDA_TEST_FLAGS))

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_test_skip_gpu_tests_does_not_run_any_cuda_tests() -> None:
    with cmade_project_instance() as d: 
        check_cmd_succeeds(d, [
            'test', '--skip-gpu-tests'
        ], env=make_fail_env(CUDA_TEST_FLAGS))


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.parametrize("flag", CPU_TEST_FLAGS)
def test_proj_test_skip_gpu_tests_runs_all_of_the_cpu_tests(flag: str) -> None:
    with cmade_project_instance() as d: 
        check_cmd_fails(d, [
            'test', '--skip-gpu-tests'
        ], env=make_fail_env([flag]))

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_test_single_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test',
            'no-cuda',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_fails(d, [
            'test', 
            'not-kernels',
        ])
        check_cmd_succeeds(d, [
            'test',
            '--skip-gpu-tests',
            'not-kernels',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

        check_cmd_fails(d, [
            'test',
            'only-cuda',
        ])
        check_cmd_fails(d, [
            'test', 
            '--skip-gpu-tests',
            'only-cuda',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_test_single_testcase() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test',
            'not-kernels:call_not_kernels_cpu',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

        check_cmd_fails(d, [
            'test',
            'not-kernels:call_not_kernels_gpu',
        ])
        check_cmd_fails(d, [
            'test',
            '--skip-gpu-tests',
            'not-kernels:call_not_kernels_gpu',
        ])

        check_cmd_succeeds(d, [
            'test',
            'no-cuda:call_no_cuda',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))
        check_cmd_succeeds(d, [
            'test',
            '--skip-gpu-tests',
            'no-cuda:call_no_cuda',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_fails(d, [
            'test',
            'only-cuda:call_only_cuda',
        ])
        check_cmd_fails(d, [
            'test',
            '--skip-gpu-tests',
            'only-cuda:call_only_cuda',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_run_test_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            'no-cuda:test',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_fails(d, [
            'run',
            'not-kernels:test',
        ])

        check_cmd_succeeds(d, [
            'run',
            '--skip-gpu',
            'not-kernels:test',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_profile_test_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            'no-cuda:test',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_fails(d, [
            'profile',
            'not-kernels:test',
        ])

        check_cmd_succeeds(d, [
            'profile',
            '--skip-gpu',
            'not-kernels:test',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_run_test_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            'no-cuda:test:call_no_cuda',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))
        check_cmd_fails(d, [
            'run',
            'no-cuda:test:call_no_cuda',
        ], env=make_fail_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_succeeds(d, [
            'run',
            'not-kernels:test:call_not_kernels_cpu',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))
        check_cmd_fails(d, [
            'run',
            'not-kernels:test:call_not_kernels_cpu',
        ], env=make_fail_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

        check_cmd_fails(d, [
            'run',
            'not-kernels:test:call_not_kernels_gpu',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_proj_profile_test_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            'no-cuda:test:call_no_cuda',
        ], env=make_pass_env([
            FAIL_NO_CUDA_TEST,
        ]))
        check_cmd_fails(d, [
            'profile',
            'no-cuda:test:call_no_cuda',
        ], env=make_fail_env([
            FAIL_NO_CUDA_TEST,
        ]))

        check_cmd_succeeds(d, [
            'profile',
            'not-kernels:test:call_not_kernels_cpu',
        ], env=make_pass_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))
        check_cmd_fails(d, [
            'profile',
            'not-kernels:test:call_not_kernels_cpu',
        ], env=make_fail_env([
            FAIL_NOT_KERNELS_TEST_CPU,
        ]))

        check_cmd_fails(d, [
            'profile',
            'not-kernels:test:call_not_kernels_gpu',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci_does_not_run_any_cuda_tests() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])

        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ], env=make_fail_env(CUDA_TEST_FLAGS))


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.parametrize('flag', CPU_TEST_FLAGS)
def test_check_cpu_ci_runs_all_of_the_cpu_testcases(flag: str) -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])

        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], env=make_fail_env([flag]))

@pytest.mark.e2e
@pytest.mark.slow
def test_check_gpu_ci_does_not_run_any_cpu_testcases() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'gpu-ci',
        ], env=make_fail_env(CPU_TEST_FLAGS))

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.parametrize("flag", CUDA_TEST_FLAGS)
def test_check_gpu_ci_runs_all_of_the_cuda_testcases(flag: str) -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'check',
            'gpu-ci',
        ], env=make_fail_env([flag]))
