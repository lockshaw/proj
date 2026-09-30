from dataclasses import dataclass
from typing import (
    Tuple,
    Union,
    Sequence,
    Iterator,
)
from .terminal_colors import (
    TermColor,
)
import math
from pathlib import Path
from .json import (
    Json,
    require_int,
)
from .config_file import ProjectConfig
import os
from .executor import (
    execute_tasks,
    Task,
    TaskResult,
    TerminationType,
)
from .targets import (
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
)
import re
import sys
import logging
from . import subprocess_trace as subprocess
import itertools

_l = logging.getLogger(__name__)

def list_benchmark_cases_in_suite(
    suite: BenchmarkSuiteTarget,
    build_dir: Path,
) -> Iterator[BenchmarkCaseTarget]:
    output = subprocess.check_output(
        [
            str(suite.run_target.executable_path),
            "--list",
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
        text=True,
    ).splitlines()

    for line in output:
        yield suite.get_benchmark_case(line)

@dataclass(frozen=True, kw_only=True)
class BenchmarkResult:
    num_instructions_executed: int

    @staticmethod
    def from_json(j: Json) -> "BenchmarkResult":
        assert isinstance(j, dict)

        ALLOWED_KEYS = {'num_instructions_executed'}
        assert set(j.keys()) == ALLOWED_KEYS

        return BenchmarkResult(
            num_instructions_executed=require_int(j['num_instructions_executed']),
        )

    def to_json(self) -> Json:
        return {
            'num_instructions_executed': self.num_instructions_executed,
        }

def benchmark_to_task(
    config: ProjectConfig,
    benchmark: BenchmarkCaseTarget,
    build_dir: Path,
) -> Task:
    return Task(
        cmd=[
            'valgrind',
            '--tool=cachegrind',
            f'./{benchmark.run_target.executable_path.name}',
            *benchmark.run_target.args,
        ],
        cwd=build_dir / benchmark.run_target.executable_path.parent,
        env=dict(os.environ),
        timeout_seconds=config.benchmark_timeout_seconds,
    )

_NUM_INSTRUCTIONS_RE = re.compile(br'\bI refs:\s+([0-9,]+)')

def parse_benchmark_output(output: bytes) -> BenchmarkResult:
    m = _NUM_INSTRUCTIONS_RE.search(output)
    assert m is not None, output

    num_instructions = int(m.group(1).replace(b',', b''))

    return BenchmarkResult(
        num_instructions_executed=num_instructions,
    )

def pretty_name_for_benchmark_case(benchmark_case: BenchmarkCaseTarget) -> str:
    return f'{benchmark_case.benchmark_suite.lib_name}:{benchmark_case.case_name}'

def report_benchmark_timeout(
    benchmark: BenchmarkCaseTarget,
) -> None:
    print("".join(
        [
            TermColor.YELLOW,
            f"----TIMED OUT {pretty_name_for_benchmark_case(benchmark)}",
            TermColor.END,
        ]
    ))

def report_benchmark_success(
    benchmark: BenchmarkCaseTarget,
    result: BenchmarkResult,
    instruction_budget: int,
) -> None:
    percentage_budget_used = math.ceil(100 * result.num_instructions_executed / instruction_budget)
    print("".join(
        [
            TermColor.GREEN,
            f"----PASSED {pretty_name_for_benchmark_case(benchmark)} ({percentage_budget_used}% = {result.num_instructions_executed:0>12} / {instruction_budget:0>12})",
            TermColor.END,
        ]
    ))

def report_benchmark_error(
    benchmark: BenchmarkCaseTarget,
    task_result: TaskResult,
) -> None:
    header_line = "".join(
        [
            TermColor.BLUE,
            f"----ERROR IN {pretty_name_for_benchmark_case(benchmark)}".ljust(80, "-"),
            TermColor.END,
        ]
    )

    def msg(s: Union[str, bytes]) -> None:
        if isinstance(s, str):
            sys.stdout.write(s)
        else:
            assert isinstance(s, bytes)
            sys.stdout.buffer.write(s)
        sys.stdout.flush()

    msg(header_line + "\n")
    msg("STDOUT:\n")
    msg(task_result.stdout)
    msg("STDERR:\n")
    msg(task_result.stderr)

def report_benchmark_failure(
    benchmark: BenchmarkCaseTarget,
    result: BenchmarkResult,
    instruction_budget: int,
) -> None:
    percentage_budget_used = math.ceil(100 * result.num_instructions_executed / instruction_budget)
    print("".join(
        [
            TermColor.RED,
            f"----FAILED {pretty_name_for_benchmark_case(benchmark)} ({percentage_budget_used}% = {result.num_instructions_executed:0>10} / {instruction_budget:0>10})",
            TermColor.END,
        ]
    ))

@dataclass(frozen=True, eq=True)
class BenchmarkExecutionSummary:
    passed: Tuple[BenchmarkCaseTarget, ...]
    failed: Tuple[BenchmarkCaseTarget, ...]
    timed_out: Tuple[BenchmarkCaseTarget, ...]
    errored: Tuple[BenchmarkCaseTarget, ...]

def call_benchmarks(
    config: ProjectConfig,
    benchmarks: Sequence[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]],
    build_dir: Path,
    num_jobs: int,
) -> BenchmarkExecutionSummary:
    _l.debug("Calling benchmarks %s", benchmarks)

    def _list_benchmark_cases(b: Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]) -> Iterator[BenchmarkCaseTarget]:
        if isinstance(b, BenchmarkCaseTarget):
            yield b
        else:
            yield from list_benchmark_cases_in_suite(b, build_dir)

    benchmark_case_targets = list(
        itertools.chain.from_iterable(
            _list_benchmark_cases(b) for b in benchmarks
        )
    )

    instruction_budgets = {
        b: config.lookup_instruction_budget_for_benchmark(b)
        for b in benchmark_case_targets
    }

    passed = []
    failed = []
    timed_out = []
    errored = []

    def _benchmark_to_task(benchmark: BenchmarkCaseTarget) -> Task:
        return benchmark_to_task(config, benchmark, build_dir)

    for benchmark, task_result in execute_tasks(
        'benchmarks',
        _benchmark_to_task,
        benchmark_case_targets,
        num_jobs,
    ):
        if task_result.termination == TerminationType.TIMEOUT:
            report_benchmark_timeout(benchmark)
            timed_out.append(benchmark)
            continue

        if task_result.termination == TerminationType.FAILURE:
            report_benchmark_error(benchmark, task_result)
            errored.append(benchmark)
            continue

        assert task_result.termination == TerminationType.SUCCESS
        benchmark_result = parse_benchmark_output(output=task_result.stderr)
        instruction_budget = instruction_budgets[benchmark]
        if benchmark_result.num_instructions_executed <= instruction_budget:
            report_benchmark_success(benchmark, benchmark_result, instruction_budget)
            passed.append(benchmark)
        else:
            report_benchmark_failure(benchmark, benchmark_result, instruction_budget)
            failed.append(benchmark)

    return BenchmarkExecutionSummary(
        passed=tuple(passed),
        failed=tuple(failed),
        timed_out=tuple(timed_out),
        errored=tuple(errored),
    )
