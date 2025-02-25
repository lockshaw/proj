from typing import (
    Sequence,
    List,
)
from .targets import (
    RunTarget,
    TestSuiteTarget,
    RunTargetType,
    TestCaseTarget,
)
from . import subprocess_trace as subprocess
import sys
from pathlib import Path
import os
import json
import logging

_l = logging.getLogger(__name__)

def list_tests_in_targets(targets: Sequence[TestSuiteTarget], build_dir: Path) -> List[TestCaseTarget]:
    target_regex = "^(" + "|".join([t.lib_name for t in targets]) + ")$"
    output = subprocess.check_output(
        [
            "ctest",
            "-L",
            target_regex,
            "--show-only=json-v1",
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
        text=True,
    )

    loaded = json.loads(output)
    _l.debug('Loaded json: %s', output)
    for test in loaded['tests']:
        properties = test['properties']
        for property in properties:
            if property['name'] == 'LABELS':
                labels = properties[0]['value']
                assert len(labels) == 1
                label = labels[0]
                break
        else:
            raise ValueError(f'Could not find label for test {test=}')
        yield TestSuiteTarget(
            lib_name=label,
        ).get_test_case(test['name'])

def run_tests(targets: Sequence[RunTarget], build_dir: Path, debug: bool) -> None:
    target_regex = "^(" + "|".join([t.name for t in targets]) + ")$"
    subprocess.run(
        [
            "ctest",
            "--progress",
            "--output-on-failure",
            "-L",
            target_regex,
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
    )
