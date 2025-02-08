from . import subprocess_trace as subprocess
from pathlib import Path
import json
from .json import Json
from typing import (
    Sequence, 
    Tuple,
    Dict,
    Any,
)
from dataclasses import dataclass
from datetime import datetime
import statistics
from tempfile import NamedTemporaryFile
import logging

_l = logging.getLogger(__name__)

def require_float(x: Any) -> float:
    assert isinstance(x, float)
    return x

@dataclass(frozen=True)
class BenchmarkContext:
    date: datetime
    mhz_per_cpu: int
    load_avg: Tuple[float, float, float]
    rest: Dict[str, Json]

    @staticmethod
    def from_json(json: Json) -> 'BenchmarkContext':
        assert isinstance(json, dict)
        assert isinstance(json['date'], str)
        assert isinstance(json['mhz_per_cpu'], int)
        assert isinstance(json['load_avg'], list)
        assert len(json['load_avg']) == 3
        load_avg = json['load_avg']

        removed = ['date', 'mhz_per_cpu', 'load_avg']
        rest = {k: v for k, v in json.items() if k not in removed}
        return BenchmarkContext(
            date=datetime.fromisoformat(json['date']),
            mhz_per_cpu=json['mhz_per_cpu'],
            load_avg=(
                require_float(load_avg[0]),
                require_float(load_avg[1]),
                require_float(load_avg[2]),
            ),
            rest=rest,
        )

    def to_json(self) -> Json:
        return {
            'date': self.date.isoformat(),
            'mhz_per_cpu': self.mhz_per_cpu,
            'load_avg': self.load_avg,
            **self.rest,
        }

@dataclass(frozen=True)
class BenchmarkResult:
    context: BenchmarkContext
    benchmarks: Tuple[Json, ...]

    @staticmethod
    def from_json(json: Json) -> 'BenchmarkResult':
        assert isinstance(json, dict)
        return BenchmarkResult(
            context=BenchmarkContext.from_json(json['context']),
            benchmarks=tuple(json['benchmarks']),
        )

    def to_json(self) -> Json:
        return {
            'context': self.context.to_json(),
            'benchmarks': list(self.benchmarks),
        }

def call_benchmarks(benchmarks: Sequence[Path]) -> BenchmarkResult:
    results = [call_benchmark(b) for b in sorted(benchmarks)]
    return merge_benchmark_results(results)

def call_benchmark(benchmark: Path) -> BenchmarkResult:
    (stdout, _) = subprocess.tee_output([str(benchmark), '--benchmark_format=json'])
    return BenchmarkResult.from_json(json.loads(stdout))

def upload_to_bencher(result: BenchmarkResult) -> None:
    with NamedTemporaryFile('r+') as f:
        json.dump(result.to_json(), f)
        f.flush()
        try:
            subprocess.check_call([
                'bencher', '--project', 'flexflow-train', '--adapter', 'cpp_google', '--file', f.name,
            ])
        except subprocess.CalledProcessError:
            _l.exception('Failed to upload to bencher. Are you sure you configured BENCHER_API_TOKEN correctly')

def merge_benchmark_contexts(contexts: Sequence[BenchmarkContext]) -> BenchmarkContext:
    assert len(contexts) >= 1
    rest = dict(contexts[0].rest)
    del rest['executable']
    return BenchmarkContext(
        date=min(c.date for c in contexts),
        mhz_per_cpu=round(statistics.mean(c.mhz_per_cpu for c in contexts)),
        load_avg=(
            statistics.mean(c.load_avg[0] for c in contexts),
            statistics.mean(c.load_avg[1] for c in contexts),
            statistics.mean(c.load_avg[2] for c in contexts),
        ),
        rest=rest,
    )

def merge_benchmark_results(results: Sequence[BenchmarkResult]) -> BenchmarkResult:
    assert len(results) >= 1
    return BenchmarkResult(
        context=merge_benchmark_contexts([r.context for r in results]),
        benchmarks=sum([r.benchmarks for r in results], tuple()),
    )
