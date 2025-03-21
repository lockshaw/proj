from typing import (
    Sequence,
    Iterator,
    Union,
)
from .targets import (
    TestSuiteTarget,
    TestCaseTarget,
)
from . import subprocess_trace as subprocess
import sys
from pathlib import Path
import os
import json
import logging

_l = logging.getLogger(__name__)

def list_tests_in_targets(targets: Sequence[TestSuiteTarget], build_dir: Path) -> Iterator[TestCaseTarget]:
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

def run_test_case(target: TestCaseTarget, build_dir: Path, debug: bool) -> None:
    _l.info('Running test target %s', target)
    label_regex = f"^{target.test_suite.test_binary_name}$"
    case_regex = f"^{target.test_case_name}$"
    subprocess.check_call(
        [
            "ctest",
            "--progress",
            "--output-on-failure",
            "-L",
            label_regex,
            "-R",
            case_regex,
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
    )

def run_tests(targets: Sequence[TestSuiteTarget], build_dir: Path, debug: bool) -> None:
    _l.info('Running test targets %s', targets)
    target_regex = "^(" + "|".join([t.test_binary_name for t in targets]) + ")$"
    subprocess.check_call(
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
