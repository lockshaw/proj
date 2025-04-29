from typing import (
    Sequence,
    Iterator,
    Union,
    Iterable,
)
from .targets import (
    CpuTestSuiteTarget,
    CpuTestCaseTarget,
    CudaTestSuiteTarget,
    CudaTestCaseTarget,
    GenericTestSuiteTarget,
    GenericTestCaseTarget,
    MixedTestSuiteTarget,
)
from . import subprocess_trace as subprocess
import sys
from pathlib import Path
import os
import json
import logging
import re
from .config_file import (
    ProjectConfig,
    resolve_test_case_type_without_build,
)
from .utils import (
    concatmap,
)

_l = logging.getLogger(__name__)

CPU_LABEL_RE = re.compile('cpu-(?P<libname>.*)-tests')
CUDA_LABEL_RE = re.compile('cuda-(?P<libname>.*)-tests')

def get_regex_for_test_suites(
    test_suites: Iterable[Union[
        GenericTestSuiteTarget, 
        MixedTestSuiteTarget, 
        CudaTestSuiteTarget, 
        CpuTestSuiteTarget
    ]],
) -> str:
    test_suite_names = concatmap(test_suites, lambda t: t.test_suite_names)
    return "^(" + "|".join(test_suite_names) + ")$"

def list_test_cases_in_targets(
    targets: Sequence[GenericTestSuiteTarget], 
    build_dir: Path
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    target_regex = get_regex_for_test_suites(targets)
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
        
        cuda_match = CUDA_LABEL_RE.fullmatch(label)
        if cuda_match is not None:
            yield CudaTestSuiteTarget(
                lib_name=cuda_match.group('libname'),
            ).get_test_case(test['name'])
        else:
            cpu_match = CPU_LABEL_RE.fullmatch(label)
            assert cpu_match is not None
            yield CpuTestSuiteTarget(
                lib_name=cpu_match.group('libname'),
            ).get_test_case(test['name'])

def resolve_test_case_target_using_build(
    config: ProjectConfig, 
    test_case: GenericTestCaseTarget, 
    build_dir: Path,
) -> Union[CpuTestCaseTarget, CudaTestCaseTarget]:
    result_without_build = resolve_test_case_type_without_build(config, test_case)
    if result_without_build is not None:
        return result_without_build
    else:
        all_test_cases_in_suite = list_test_cases_in_targets([test_case.test_suite], build_dir)
        cpu_test_case_names = [
            t.test_case_name for t in 
            all_test_cases_in_suite
            if isinstance(t, CpuTestCaseTarget)
        ]
        cuda_test_case_names = [
            t.test_case_name for t in 
            all_test_cases_in_suite
            if isinstance(t, CudaTestCaseTarget)
        ]
        print(cpu_test_case_names, cuda_test_case_names)
        has_cpu_test_with_matching_name = test_case.test_case_name in cpu_test_case_names
        has_cuda_test_with_matching_name = test_case.test_case_name in cuda_test_case_names
        assert has_cpu_test_with_matching_name or has_cuda_test_with_matching_name
        assert not (has_cpu_test_with_matching_name and has_cuda_test_with_matching_name)
        if has_cpu_test_with_matching_name:
            return test_case.cpu_test_case
        else:
            assert has_cuda_test_with_matching_name
            return test_case.cuda_test_case

def run_test_case(target: Union[CpuTestCaseTarget, CudaTestCaseTarget], build_dir: Path, debug: bool) -> None:
    _l.info('Running test target %s', target)
    label_regex = f"^{target.test_suite.test_suite_name}$"
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

def run_tests(targets: Sequence[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]], build_dir: Path, debug: bool) -> None:
    _l.info('Running test targets %s', targets)
    target_regex = get_regex_for_test_suites(targets)
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
