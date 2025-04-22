import pytest
from ..project_utils import (
    project_instance as _project_instance,
    cmade_project_instance as _cmade_project_instance,
    MAX_VERBOSITY,
)
from .e2e_utils import (
    require_successful,
    run,
    check_cmd_succeeds,
    check_cmd_fails,
)

def project_instance():
    return _project_instance('gpu')

def cmade_project_instance():
    return _cmade_project_instance('gpu')

FAIL_KERNELS_TEST = 'PROJ_TESTS_FAIL_KERNELS_CALL_KERNELS'
FAIL_NOT_KERNELS_TEST = 'PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS'

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_tests() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'cpu-tests',
        ], env={FAIL_KERNELS_TEST: 'y'})

        check_cmd_fails(d, [
            'check',
            'cpu-tests',
        ], env={FAIL_NOT_KERNELS_TEST: 'y'})

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])

        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ], env={FAIL_KERNELS_TEST: 'y'})

        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], env={FAIL_NOT_KERNELS_TEST: 'y'})

@pytest.mark.e2e
@pytest.mark.slow
def test_check_gpu_tests() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'check',
            'gpu-tests',
        ], env={FAIL_KERNELS_TEST: 'y'})

        check_cmd_succeeds(d, [
            'check',
            'gpu-tests',
        ], env={FAIL_NOT_KERNELS_TEST: 'y'})

@pytest.mark.e2e
@pytest.mark.slow
def test_check_gpu_ci() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'check',
            'gpu-ci',
        ], env={FAIL_KERNELS_TEST: 'y'})

        check_cmd_succeeds(d, [
            'check',
            'gpu-ci',
        ], env={FAIL_NOT_KERNELS_TEST: 'y'})
