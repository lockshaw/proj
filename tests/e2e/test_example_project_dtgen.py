import pytest
from ..project_utils import (
    cmade_project_instance,
)
from .e2e_utils import (
    check_cmd_succeeds,
)
from enum import (
    StrEnum,
)

class Project(StrEnum):
    DTGEN = 'dtgen'
    DTGEN_2 = 'dtgen-2'

@pytest.mark.slow
@pytest.mark.e2e
def test_proj_dtgen_at_least_does_not_crash() -> None:
    with cmade_project_instance(Project.DTGEN) as d:
        check_cmd_succeeds(d, [
            'dtgen',
        ])

@pytest.mark.slow
@pytest.mark.e2e
def test_dtgen_1() -> None:
    with cmade_project_instance(Project.DTGEN) as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
        ])

@pytest.mark.slow
def test_dtgen_2() -> None:
    with cmade_project_instance(Project.DTGEN_2) as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
        ])


