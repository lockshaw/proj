from typing import (
    Sequence,
    Iterator,
    Union,
    Iterable,
    Tuple,
    List,
    Dict,
    Optional,
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
    default_to,
)
import itertools
from dataclasses import (
    dataclass,
)
from .terminal_colors import (
    TermColor,
)
from .failure import fail_with_error
from .executor import (
    execute_tasks,
    Task,
    TerminationType,
    execute_task,
    TaskResult,
)

_l = logging.getLogger(__name__)

CPU_LABEL_RE = re.compile("cpu-(?P<libname>.*)-tests")
CUDA_LABEL_RE = re.compile("cuda-(?P<libname>.*)-tests")


def get_regex_for_test_suites(
    test_suites: Iterable[
        Union[
            GenericTestSuiteTarget,
            MixedTestSuiteTarget,
            CudaTestSuiteTarget,
            CpuTestSuiteTarget,
        ]
    ],
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
            "--list-test-cases",
            f"--test-suite={suite.test_suite_name}",
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
        text=True,
    ).splitlines()[2:-2]

    for line in output:
        yield suite.get_test_case(line)


def list_test_cases_in_suite(
    suite: Union[
        GenericTestSuiteTarget,
        CpuTestSuiteTarget,
        CudaTestSuiteTarget,
        MixedTestSuiteTarget,
    ],
    build_dir: Path,
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    if isinstance(suite, (CpuTestSuiteTarget, CudaTestSuiteTarget)):
        yield from list_test_cases_in_single_suite(suite, build_dir)
    else:
        assert isinstance(suite, (MixedTestSuiteTarget, GenericTestSuiteTarget))
        yield from list_test_cases_in_single_suite(
            suite.cpu_test_suite_target, build_dir
        )
        yield from list_test_cases_in_single_suite(
            suite.cuda_test_suite_target, build_dir
        )


def list_test_cases_in_test_suites(
    test_suites: Iterable[
        Union[
            GenericTestSuiteTarget,
            CpuTestSuiteTarget,
            CudaTestSuiteTarget,
            MixedTestSuiteTarget,
        ]
    ],
    build_dir: Path,
) -> Iterator[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    _l.debug(
        'Listing all test cases in test suites %s using build_dir %s',
        test_suites, build_dir,
    )
    yield from itertools.chain.from_iterable(
        [list_test_cases_in_suite(suite, build_dir) for suite in test_suites]
    )


def resolve_test_case_target_using_build(
    config: ProjectConfig,
    test_case: GenericTestCaseTarget,
    build_dir: Path,
) -> Union[CpuTestCaseTarget, CudaTestCaseTarget]:
    _l.debug("Resolving test case %s using build", test_case)

    result_without_build = resolve_test_case_type_without_build(config, test_case)
    if result_without_build is not None:
        _l.debug("Was able to resolve type of test case %s to be %s without build. Returning...", test_case, result_without_build)
        return result_without_build
    else:
        all_test_cases_in_suite = tuple(list_test_cases_in_suite(
            test_case.test_suite, build_dir
        ))
        cpu_test_case_names = [
            t.test_case_name
            for t in all_test_cases_in_suite
            if isinstance(t, CpuTestCaseTarget)
        ]
        cuda_test_case_names = [
            t.test_case_name
            for t in all_test_cases_in_suite
            if isinstance(t, CudaTestCaseTarget)
        ]
        has_cpu_test_with_matching_name = (
            test_case.test_case_name in cpu_test_case_names
        )
        has_cuda_test_with_matching_name = (
            test_case.test_case_name in cuda_test_case_names
        )
        assert has_cpu_test_with_matching_name or has_cuda_test_with_matching_name
        assert not (
            has_cpu_test_with_matching_name and has_cuda_test_with_matching_name
        )
        if has_cpu_test_with_matching_name:
            _l.debug("Test case %s found to be a CPU test. Returning...", test_case)
            return test_case.cpu_test_case
        else:
            assert has_cuda_test_with_matching_name
            _l.debug("Test case %s found to be a CUDA test. Returning...", test_case)
            return test_case.cuda_test_case

_DOCTEST_TEST_OUTPUT_SUFFIX_RE = re.compile(
    (
        br'^\[doctest\] test cases:\s+(?P<test_cases_executed>\d+) '
        br'\|\s+(?P<test_cases_passed>\d+) passed '
        br'\|\s+(?P<test_cases_failed>\d+) failed '
        br'\|\s+(?P<test_cases_skipped>\d+) skipped\n'
        br'^\[doctest\] assertions:\s+(?P<assertions_total>\d+) '
        br'\|\s+(?P<assertions_passed>\d+) passed '
        br'\|\s+(?P<assertions_failed>\d+) failed \|\n'
        br'^\[doctest\] Status: (?P<status>SUCCESS|FAILURE)!'
    ),
    re.MULTILINE,
)

@dataclass(frozen=True, eq=True)
class DoctestTestCaseExecutionSuffix:
    test_cases_passed: int
    test_cases_failed: int
    test_cases_skipped: int
    assertions_passed: int
    assertions_failed: int
    succeeded: bool

def strip_terminal_escapes(b: bytes) -> bytes:
    return re.sub(b'\x1b[^m]+m', b'', b)

def parse_test_case_output(output: bytes) -> Optional[DoctestTestCaseExecutionSuffix]:
    doctest_lines = strip_terminal_escapes(
        b'\n'.join(output.strip().splitlines()[-3:])
    )

    m = _DOCTEST_TEST_OUTPUT_SUFFIX_RE.fullmatch(doctest_lines)
    if m is None:
        return None

    test_cases_executed = int(m.group('test_cases_executed'))
    test_cases_passed = int(m.group('test_cases_passed'))
    test_cases_failed = int(m.group('test_cases_failed'))
    test_cases_skipped = int(m.group('test_cases_skipped'))

    assert test_cases_executed == (test_cases_passed + test_cases_failed)

    assertions_total = int(m.group('assertions_total'))
    assertions_passed = int(m.group('assertions_passed'))
    assertions_failed = int(m.group('assertions_failed'))

    assert assertions_total == (assertions_passed + assertions_failed)

    STATUS_MAP = {
        b'SUCCESS': True,
        b'FAILURE': False,
    }
    succeeded = STATUS_MAP[m.group('status')]

    return DoctestTestCaseExecutionSuffix(
        test_cases_passed=test_cases_passed,
        test_cases_failed=test_cases_failed,
        test_cases_skipped=test_cases_skipped,
        assertions_passed=assertions_passed,
        assertions_failed=assertions_failed,
        succeeded=succeeded,
    )

def test_case_to_task(
    config: ProjectConfig,
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget],
    build_dir: Path,
) -> Task:
    return Task(
        cmd=list(config.cmd_for_run_target(test_case.run_target)),
        cwd=build_dir / test_case.run_target.executable_path.parent,
        env=dict(os.environ),
        timeout_seconds=config.test_case_timeout_seconds,
    )

def run_test_case(
    config: ProjectConfig,
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget],
    build_dir: Path,
    debug: bool,
) -> TaskResult:
    cmd = config.cmd_for_run_target(test_case.run_target)
    cwd = build_dir / test_case.run_target.executable_path.parent
    env = os.environ

    if debug:
        subprocess.check_call(
            command=[
                "gdb",
                "--args",
                *cmd,
            ],
            cwd=cwd,
            env=env,
        )
        sys.exit(0)
    else:
        return execute_task(
            test_case_to_task(config, test_case, build_dir),
        )

@dataclass(frozen=True, eq=True)
class TestStatistics:
    passed: Tuple[Union[CpuTestCaseTarget, CudaTestCaseTarget], ...]
    failed: Tuple[Union[CpuTestCaseTarget, CudaTestCaseTarget], ...]
    timed_out: Tuple[Union[CpuTestCaseTarget, CudaTestCaseTarget], ...]


def report_test_success(
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget],
    test_case_result: TaskResult,
) -> None:
    assert test_case_result.termination == TerminationType.SUCCESS
    test_name_pretty = f"{test_case.test_suite.lib_name}:{test_case.test_case_name}"
    print("".join(
        [
            TermColor.GREEN,
            f"----PASSED {test_name_pretty}",
            TermColor.END,
        ]
    ))

def report_test_timeout(
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget],
    test_case_result: TaskResult,
) -> None:
    assert test_case_result.termination == TerminationType.TIMEOUT
    test_name_pretty = f"{test_case.test_suite.lib_name}:{test_case.test_case_name}"
    print("".join(
        [
            TermColor.BLUE,
            f"----TIMED OUT {test_name_pretty}",
            TermColor.END,
        ]
    ))

def report_test_failure(
    test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget],
    test_case_result: TaskResult,
) -> None:
    assert test_case_result.termination == TerminationType.FAILURE

    test_name_pretty = f"{test_case.test_suite.lib_name}:{test_case.test_case_name}"
    header_line = "".join(
        [
            TermColor.RED,
            f"----FAILED {test_name_pretty}".ljust(80, "-"),
            TermColor.END,
        ]
    )
    debug_line = f"----To debug, run: proj test --debug '{test_name_pretty}' ".ljust(
        80, "-"
    )

    def msg(s: Union[str, bytes]) -> None:
        if isinstance(s, str):
            sys.stdout.write(s)
        else:
            assert isinstance(s, bytes)
            sys.stdout.buffer.write(s)
        sys.stdout.flush()

    msg(header_line + "\n")
    msg(debug_line + "\n")
    msg("STDOUT:\n")
    msg(test_case_result.stdout)
    msg("STDERR:\n")
    msg(test_case_result.stderr)


def run_test_suites(
    config: ProjectConfig,
    test_suites: Sequence[
        Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]
    ],
    build_dir: Path,
    num_jobs: int,
) -> TestStatistics:
    _l.info("Running test suites %s", test_suites)

    test_cases = tuple(
        list_test_cases_in_test_suites(
            test_suites=test_suites,
            build_dir=build_dir,
        )
    )

    passed = []
    timed_out = []
    failed = []

    def _test_case_to_task(test_case: Union[CpuTestCaseTarget, CudaTestCaseTarget]) -> Task:
        return test_case_to_task(config, test_case, build_dir)

    for test_case, test_case_result in execute_tasks(
        'testcases',
        _test_case_to_task,
        test_cases,
        num_jobs,
    ):
        if test_case_result.termination == TerminationType.TIMEOUT:
            timed_out.append(test_case)
            report_test_timeout(test_case, test_case_result)
        else:
            parsed_suffix = parse_test_case_output(test_case_result.stdout)
            if parsed_suffix is None:
                fail_with_error('\n'.join([
                    f'Failed to parse doctest output of testcase {test_case}.',
                    'stdout:',
                    test_case_result.stdout.decode('utf8'),
                    'stderr:',
                    test_case_result.stderr.decode('utf8'),
                ]))
            assert parsed_suffix.succeeded == (test_case_result.termination == TerminationType.SUCCESS)

            if test_case_result.termination == TerminationType.SUCCESS:
                if parsed_suffix.test_cases_passed != 1:
                    fail_with_error(
                        f'Test case {test_case} had unexpected test_cases_passed count '
                        f'in the doctest output: expected 1, but found {parsed_suffix.test_cases_passed}'
                    )
                elif parsed_suffix.test_cases_failed != 0:
                    fail_with_error(
                        f'Test case {test_case} had unexpected test_cases_failed count '
                        f'in the doctest output: expected 0, but found {parsed_suffix.test_cases_failed}'
                    )
                else:
                    passed.append(test_case)
            else:
                assert test_case_result.termination == TerminationType.FAILURE

                if parsed_suffix.test_cases_passed != 0:
                    fail_with_error(
                        f'Test case {test_case} had unexpected test_cases_passed count '
                        f'in the doctest output: expected 0, but found {parsed_suffix.test_cases_passed}'
                    )
                elif parsed_suffix.test_cases_failed != 1:
                    fail_with_error(
                        f'Test case {test_case} had unexpected test_cases_failed count '
                        f'in the doctest output: expected 1, but found {parsed_suffix.test_cases_failed}'
                    )
                else:
                    failed.append(test_case)

                    report_test_failure(test_case, test_case_result)

    return TestStatistics(
        passed=tuple(passed),
        failed=tuple(failed),
        timed_out=tuple(timed_out),
    )
