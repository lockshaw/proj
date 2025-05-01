import pytest
from .e2e_utils import (
    check_cmd_succeeds,
    check_cmd_fails,
)
from ..project_utils import (
    project_instance as _project_instance,
    cmade_project_instance as _cmade_project_instance,
)
from typing import (
    ContextManager,
)
from pathlib import Path

def project_instance() -> ContextManager[Path]:
    return _project_instance('test-env')

def cmade_project_instance() -> ContextManager[Path]:
    return _cmade_project_instance('test-env')

FAIL_TEST = 'PROJ_TESTS_FAIL_TEST_ENV_EXAMPLE_FUNCTION'

@pytest.mark.e2e
@pytest.mark.slow
def test_that_proj_test_runs_all_test_cases() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'test'
        ], env={FAIL_TEST: 'y'})

@pytest.mark.e2e
@pytest.mark.slow
def test_that_proj_test_runs_test_cases_in_the_directory_of_their_binary() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test'
        ])
