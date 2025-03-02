import pytest
from ..project_utils import (
    cmade_project_instance,
)
from .e2e_utils import (
    check_cmd_succeeds,
)

@pytest.mark.slow
@pytest.mark.e2e
def test_dtgen_1():
    with cmade_project_instance('dtgen') as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
        ])

@pytest.mark.slow
def test_dtgen_2():
    with cmade_project_instance('dtgen-2') as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
        ])


