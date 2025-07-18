from . import subprocess_trace as subprocess
import json
from .json import Json
from typing import (
    Sequence,
    Tuple,
    Dict,
    Any,
    IO,
    Optional,
    List,
    Union,
    TypeVar,
)
from dataclasses import dataclass
from datetime import datetime
import statistics
from tempfile import NamedTemporaryFile
import logging
import re
from .browser import open_in_browser
from .config_file import ProjectConfig
from .targets import (
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
)
from pathlib import Path
from .progressbar import (
    get_progress_manager,
    ProgressBar,
)

_l = logging.getLogger(__name__)


def require_float(x: Any) -> float:
    assert isinstance(x, (int, float)), x
    return x


@dataclass(frozen=True)
class BenchmarkCache:
    type_: str
    level: int
    size: int
    num_sharing: int

    @staticmethod
    def from_json(json: Json) -> "BenchmarkCache":
        assert isinstance(json, dict)
        assert isinstance(json["type"], str)
        assert isinstance(json["level"], int)
        assert isinstance(json["size"], int)
        assert isinstance(json["num_sharing"], int)
        return BenchmarkCache(
            type_=json["type"],
            level=json["level"],
            size=json["size"],
            num_sharing=json["num_sharing"],
        )

    def to_json(self) -> Dict[str, Json]:
        return {
            "type": self.type_,
            "level": self.level,
            "size": self.size,
            "num_sharing": self.num_sharing,
        }


@dataclass(frozen=True)
class BenchmarkContext:
    date: datetime
    mhz_per_cpu: int
    load_avg: Tuple[float, float, float]
    num_cpus: int
    caches: Tuple[BenchmarkCache, ...]
    executable: str
    rest: Dict[str, Json]

    @staticmethod
    def from_json(json: Json) -> "BenchmarkContext":
        assert isinstance(json, dict)
        assert isinstance(json["date"], str)
        assert isinstance(json["mhz_per_cpu"], int)
        assert isinstance(json["load_avg"], list)
        assert isinstance(json["num_cpus"], int)
        assert isinstance(json["caches"], list)
        assert isinstance(json["executable"], str)
        assert len(json["load_avg"]) == 3
        load_avg = json["load_avg"]

        removed = [
            "date",
            "mhz_per_cpu",
            "load_avg",
            "num_cpus",
            "caches",
            "executable",
        ]
        rest = {k: v for k, v in json.items() if k not in removed}
        return BenchmarkContext(
            date=datetime.fromisoformat(json["date"]),
            mhz_per_cpu=json["mhz_per_cpu"],
            load_avg=(
                require_float(load_avg[0]),
                require_float(load_avg[1]),
                require_float(load_avg[2]),
            ),
            num_cpus=json["num_cpus"],
            caches=tuple([BenchmarkCache.from_json(j) for j in json["caches"]]),
            executable=json["executable"],
            rest=rest,
        )

    def to_json(self) -> Json:
        return {
            "date": self.date.isoformat(),
            "mhz_per_cpu": self.mhz_per_cpu,
            "load_avg": list(self.load_avg),
            "num_cpus": self.num_cpus,
            "caches": [c.to_json() for c in self.caches],
            "executable": self.executable,
            **self.rest,
        }


@dataclass(frozen=True)
class IndividualBenchmark:
    name: str
    real_time: float
    cpu_time: float
    iterations: int
    time_unit: str
    rest: Dict[str, Json]

    @staticmethod
    def from_json(j: Json) -> "IndividualBenchmark":
        assert isinstance(j, dict)
        assert isinstance(j["name"], str)
        assert isinstance(j["real_time"], float)
        assert isinstance(j["cpu_time"], float)
        assert isinstance(j["iterations"], int)
        assert isinstance(j["time_unit"], str)

        removed = ["name", "real_time", "cpu_time", "iterations", "time_unit"]
        rest = {k: v for k, v in j.items() if k not in removed}
        return IndividualBenchmark(
            name=j["name"],
            real_time=j["real_time"],
            cpu_time=j["cpu_time"],
            iterations=j["iterations"],
            time_unit=j["time_unit"],
            rest=rest,
        )

    def to_json(self) -> Json:
        return {
            "name": self.name,
            "real_time": self.real_time,
            "cpu_time": self.cpu_time,
            "iterations": self.iterations,
            "time_unit": self.time_unit,
            **self.rest,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    context: BenchmarkContext
    benchmarks: Tuple[IndividualBenchmark, ...]

    @staticmethod
    def from_json(json: Json) -> "BenchmarkResult":
        assert isinstance(json, dict)
        return BenchmarkResult(
            context=BenchmarkContext.from_json(json["context"]),
            benchmarks=tuple(
                [IndividualBenchmark.from_json(ib) for ib in json["benchmarks"]]
            ),
        )

    def to_json(self) -> Json:
        return {
            "context": self.context.to_json(),
            "benchmarks": [b.to_json() for b in self.benchmarks],
        }


def render_table(
    columns: Sequence[str],
    data: Sequence[Sequence[str]],
    sep: Optional[Union[int, Sequence[int]]] = None,
) -> str:
    num_columns = len(columns)

    if sep is None:
        sep = 1
    assert sep is not None
    if isinstance(sep, int):
        sep = [sep for _ in range(num_columns - 1)]
    assert isinstance(sep, list)
    assert len(sep) == num_columns - 1

    for d in data:
        assert len(d) == num_columns

    def column_entries(n: int) -> List[str]:
        return [columns[n], *[d[n] for d in data]]

    def column_width(n: int) -> int:
        return max(map(len, column_entries(n)))

    def render_column(d: Sequence[str], n: int) -> str:
        if n == 0:
            return d[n].ljust(column_width(n), " ")
        else:
            return d[n].rjust(column_width(n), " ")

    def render_line(d: Sequence[str]) -> str:
        column_contents = [render_column(d, i) for i in range(num_columns)]
        column_seps = [s * " " for s in sep]
        result = ""
        for i in range(num_columns - 1):
            result += column_contents[i]
            result += column_seps[i]
        result += column_contents[num_columns - 1]
        return result

    table_width = sum(column_width(i) for i in range(num_columns)) + sum(sep)

    lines: List[str] = []
    lines.append(table_width * "-")
    lines.append(render_line(columns))
    lines.append(table_width * "-")
    for d in data:
        lines.append(render_line(d))

    return "\n".join(lines)


def pretty_print_benchmark(benchmark: BenchmarkResult, f: IO[str]) -> None:
    def line(s: str) -> None:
        print(s, file=f)

    line(benchmark.context.date.isoformat())
    line(f"Running {benchmark.context.executable}")
    line(
        f"Run on ({benchmark.context.num_cpus} X {benchmark.context.mhz_per_cpu} MHz CPU s)"
    )
    line("CPU Caches:")
    for cache in benchmark.context.caches:
        line(
            f"  L{cache.level} {cache.type_} {cache.size} B (x{benchmark.context.num_cpus // cache.num_sharing})"
        )
    assert len(benchmark.context.load_avg) == 3
    (load0, load1, load2) = benchmark.context.load_avg
    line(f"Load Average: {load0:.2f}, {load1:.2f}, {load2:.2f}")

    columns = ["Benchmark", "Time", "CPU", "Iterations"]
    sep = [1, 3, 3]
    table_data = [
        (
            b.name,
            f"{round(b.real_time)} {b.time_unit}",
            f"{round(b.cpu_time)} {b.time_unit}",
            str(b.iterations),
        )
        for b in benchmark.benchmarks
    ]

    line(render_table(columns=columns, data=table_data, sep=sep))


def list_benchmarks(
    benchmark_binaries: Sequence[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]],
    build_dir: Path,
) -> List[BenchmarkCaseTarget]:
    return sum(
        (get_benchmark_list_for_binary(bin, build_dir) for bin in benchmark_binaries),
        [],
    )


def get_benchmark_list_for_binary(
    bin: Union[BenchmarkSuiteTarget, BenchmarkCaseTarget], build_dir: Path
) -> List[BenchmarkCaseTarget]:
    if isinstance(bin, BenchmarkCaseTarget):
        return [bin]
    stdout = subprocess.check_output(
        [
            str(build_dir / bin.run_target.executable_path),
            "--benchmark_list_tests=true",
        ],
        text=True,
    )
    return [bin.get_benchmark_case(line) for line in stdout.splitlines()]


def call_benchmarks(
    benchmark_binaries: Sequence[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]],
    build_dir: Path,
) -> BenchmarkResult:
    _l.debug("Calling benchmark suites %s", benchmark_binaries)
    benchmark_binaries = list(sorted(benchmark_binaries))
    all_benchmarks = list_benchmarks(benchmark_binaries, build_dir)

    manager = get_progress_manager()
    with manager.counter(total=len(all_benchmarks), desc="Benchmarks") as pbar:
        results = [call_benchmark(bin, pbar, build_dir) for bin in benchmark_binaries]
    return merge_benchmark_results(results)


def call_benchmark(
    benchmark: Union[BenchmarkCaseTarget, BenchmarkSuiteTarget],
    pbar: ProgressBar,
    build_dir: Path,
) -> BenchmarkResult:
    if isinstance(benchmark, BenchmarkCaseTarget):
        return call_benchmark_case(benchmark, pbar, build_dir)
    else:
        assert isinstance(benchmark, BenchmarkSuiteTarget)
        return call_benchmark_suite(benchmark, pbar, build_dir)


def call_benchmark_case(
    benchmark: BenchmarkCaseTarget, pbar: ProgressBar, build_dir: Path
) -> BenchmarkResult:
    pbar.update(incr=0, force=True)
    functions = [benchmark]

    def hook(line: str) -> None:
        match = NAME_RE.search(line)
        if match is None:
            return
        testname = match.group("testname")
        assert testname == benchmark.case_name, (testname, benchmark.case_name)
        functions.pop(0)
        if len(functions) > 0:
            print(f"Running {functions[0]}")
        pbar.update()

    stdout = subprocess.hook_stdout(
        [
            str(build_dir / benchmark.run_target.executable_path),
            "--benchmark_format=json",
            *benchmark.run_target.args,
        ],
        stdout_hook=hook,
    )
    return BenchmarkResult.from_json(json.loads(stdout))


NAME_RE = re.compile(r'"name": "(?P<testname>[^"]+)"')


def call_benchmark_suite(
    benchmark: BenchmarkSuiteTarget, pbar: ProgressBar, build_dir: Path
) -> BenchmarkResult:
    functions = get_benchmark_list_for_binary(benchmark, build_dir)
    pbar.update(incr=0, force=True)

    def hook(line: str) -> None:
        match = NAME_RE.search(line)
        if match is None:
            return
        testname = match.group("testname")
        assert benchmark.get_benchmark_case(testname) == functions[0], (
            testname,
            functions[0],
        )
        functions.pop(0)
        if len(functions) > 0:
            print(f"Running {functions[0]}")
        pbar.update()

    print(f"Running {functions[0]}")
    stdout = subprocess.hook_stdout(
        [
            str(build_dir / benchmark.run_target.executable_path),
            "--benchmark_format=json",
        ],
        stdout_hook=hook,
    )
    return BenchmarkResult.from_json(json.loads(stdout))


def upload_to_bencher(
    config: ProjectConfig, result: BenchmarkResult, browser: bool
) -> None:
    with NamedTemporaryFile("r+") as f:
        json.dump(result.to_json(), f)
        f.flush()
        try:
            if browser:
                format = "html"
                stdout = subprocess.PIPE
            else:
                format = "human"
                stdout = None
            cmd_result = subprocess.run(
                [
                    "bencher",
                    "run",
                    "--project",
                    "flexflow-train",
                    "--adapter",
                    "cpp_google",
                    "--file",
                    f.name,
                    "--quiet",
                    "--format",
                    format,
                ],
                check=True,
                stdout=stdout,
            )
        except subprocess.CalledProcessError:
            _l.exception(
                "Failed to upload to bencher. Are you sure you configured BENCHER_API_TOKEN correctly"
            )
        if browser:
            config.benchmark_html_dir.mkdir(exist_ok=True, parents=True)
            with (config.benchmark_html_dir / "index.html").open("wb") as f:  # type: ignore
                f.write(cmd_result.stdout)
            open_in_browser(config.benchmark_html_dir / "index.html")


T = TypeVar("T")


def require_all_same(x: Sequence[T]) -> T:
    if len(x) == 0:
        raise ValueError("unexpectedly received empty sequence")
    result = x[0]
    for v in x[1:]:
        assert result == v
    return result


def all_same(x: Sequence[T]) -> bool:
    if len(x) == 0:
        return True
    return all(v == x[0] for v in x)


def merge_benchmark_contexts(contexts: Sequence[BenchmarkContext]) -> BenchmarkContext:
    assert len(contexts) >= 1
    rest = dict(contexts[0].rest)
    num_cpus = require_all_same([c.num_cpus for c in contexts])
    caches = require_all_same([c.caches for c in contexts])
    if all_same([c.executable for c in contexts]):
        executable = contexts[0].executable
    else:
        executable = "aggregated benchmarks"
    return BenchmarkContext(
        date=min(c.date for c in contexts),
        mhz_per_cpu=round(statistics.mean(c.mhz_per_cpu for c in contexts)),
        load_avg=(
            statistics.mean(c.load_avg[0] for c in contexts),
            statistics.mean(c.load_avg[1] for c in contexts),
            statistics.mean(c.load_avg[2] for c in contexts),
        ),
        num_cpus=num_cpus,
        caches=caches,
        executable=executable,
        rest=rest,
    )


def merge_benchmark_results(results: Sequence[BenchmarkResult]) -> BenchmarkResult:
    assert len(results) >= 1
    return BenchmarkResult(
        context=merge_benchmark_contexts([r.context for r in results]),
        benchmarks=sum([r.benchmarks for r in results], tuple()),
    )
