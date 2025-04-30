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
    get_test_suite_names,
)
from . import subprocess_trace as subprocess
import sys
from pathlib import Path
import os
import logging
import re
from .config_file import (
    ProjectConfig,
    resolve_test_case_type_without_build,
)
from .utils import (
    concatmap,
)
import itertools

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
    test_suite_names = concatmap(test_suites, get_test_suite_names)
    return "^(" + "|".join(test_suite_names) + ")$"

def list_test_cases_in_single_suite(
    suite: Union[CpuTestSuiteTarget, CudaTestSuiteTarget],
    build_dir: Path,
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:

    output = subprocess.check_output(
        [
            str(suite.run_target.executable_path),
            '--list-test-cases',
            f'--test-suite={suite.test_suite_name}',
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
        text=True,
    ).splitlines()[2:-2]

    for line in output:
        yield suite.get_test_case(line)
    

def list_test_cases_in_suite(
    suite: Union[GenericTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget, MixedTestSuiteTarget],
    build_dir: Path,
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    if isinstance(suite, (CpuTestSuiteTarget, CudaTestSuiteTarget)):
        yield from list_test_cases_in_single_suite(suite, build_dir)
    else:
        assert isinstance(suite, (MixedTestSuiteTarget, GenericTestSuiteTarget))
        yield from list_test_cases_in_single_suite(suite.cpu_test_suite_target, build_dir)
        yield from list_test_cases_in_single_suite(suite.cuda_test_suite_target, build_dir)

def list_test_cases_in_test_suites(
    test_suites: Iterable[Union[GenericTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget, MixedTestSuiteTarget]],
    build_dir: Path
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    yield from itertools.chain.from_iterable([
        list_test_cases_in_suite(suite, build_dir) for suite in test_suites
    ])

def resolve_test_case_target_using_build(
    config: ProjectConfig, 
    test_case: GenericTestCaseTarget, 
    build_dir: Path,
) -> Union[CpuTestCaseTarget, CudaTestCaseTarget]:
    result_without_build = resolve_test_case_type_without_build(config, test_case)
    if result_without_build is not None:
        return result_without_build
    else:
        all_test_cases_in_suite = list_test_cases_in_suite(test_case.test_suite, build_dir)
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

def run_test_case(
    config: ProjectConfig, 
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget], 
    build_dir: Path, 
    debug: bool,
) -> None:
    _l.info('Running test case %s', test_case)

    subprocess.check_call(
        config.cmd_for_run_target(test_case.run_target),
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
    )

def run_test_suites(
    config: ProjectConfig,
    test_suites: Sequence[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]], 
    build_dir: Path, 
    debug: bool,
) -> None:
    _l.info('Running test suites %s', test_suites)

    test_cases = list_test_cases_in_test_suites(
        test_suites=test_suites,
        build_dir=build_dir,
    )

    for test_case in test_cases:
        run_test_case(
            config=config,
            test_case=test_case,
            build_dir=build_dir,
            debug=debug,
        )
