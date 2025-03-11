from proj.benchmarks import (
    render_table,
    BenchmarkResult,
    pretty_print_benchmark,
)
import json
import io

COMPILER_BENCHMARK_JSON = '''{
  "context": {
    "date": "2025-02-08T14:51:41-08:00",
    "host_name": "vlaminck",
    "executable": "/home/lockshaw/x/ff/gh/benchmarks-setup/build/release/lib/compiler/benchmark/compiler-benchmarks",
    "num_cpus": 4,
    "mhz_per_cpu": 3898,
    "cpu_scaling_enabled": false,
    "caches": [
      {
        "type": "Data",
        "level": 1,
        "size": 32768,
        "num_sharing": 1
      },
      {
        "type": "Instruction",
        "level": 1,
        "size": 32768,
        "num_sharing": 1
      },
      {
        "type": "Unified",
        "level": 2,
        "size": 262144,
        "num_sharing": 1
      },
      {
        "type": "Unified",
        "level": 3,
        "size": 6291456,
        "num_sharing": 4
      }
    ],
    "load_avg": [1.00,0.565918,0.555664],
    "library_build_type": "release"
  },
  "benchmarks": [
    {
      "name": "benchmark_get_computation_graph_series_parallel_decomposition/split_test",
      "family_index": 0,
      "per_family_instance_index": 0,
      "run_name": "benchmark_get_computation_graph_series_parallel_decomposition/split_test",
      "run_type": "iteration",
      "repetitions": 1,
      "repetition_index": 0,
      "threads": 1,
      "iterations": 379,
      "real_time": 1.8641647546169739e+06,
      "cpu_time": 1.8543106332453827e+06,
      "time_unit": "ns"
    },
    {
      "name": "benchmark_get_computation_graph_series_parallel_decomposition/transformer",
      "family_index": 1,
      "per_family_instance_index": 0,
      "run_name": "benchmark_get_computation_graph_series_parallel_decomposition/transformer",
      "run_type": "iteration",
      "repetitions": 1,
      "repetition_index": 0,
      "threads": 1,
      "iterations": 1,
      "real_time": 1.2407625920004647e+09,
      "cpu_time": 1.2372220600000000e+09,
      "time_unit": "ns"
    },
    {
      "name": "benchmark_get_computation_graph_series_parallel_decomposition/bert",
      "family_index": 2,
      "per_family_instance_index": 0,
      "run_name": "benchmark_get_computation_graph_series_parallel_decomposition/bert",
      "run_type": "iteration",
      "repetitions": 1,
      "repetition_index": 0,
      "threads": 1,
      "iterations": 1,
      "real_time": 8.3075956300035620e+08,
      "cpu_time": 8.2850729000000012e+08,
      "time_unit": "ns"
    },
    {
      "name": "benchmark_get_computation_graph_series_parallel_decomposition/candle_uno",
      "family_index": 3,
      "per_family_instance_index": 0,
      "run_name": "benchmark_get_computation_graph_series_parallel_decomposition/candle_uno",
      "run_type": "iteration",
      "repetitions": 1,
      "repetition_index": 0,
      "threads": 1,
      "iterations": 2,
      "real_time": 2.9465626150022215e+08,
      "cpu_time": 2.9380323499999994e+08,
      "time_unit": "ns"
    },
    {
      "name": "benchmark_get_computation_graph_series_parallel_decomposition/inception_v3",
      "family_index": 4,
      "per_family_instance_index": 0,
      "run_name": "benchmark_get_computation_graph_series_parallel_decomposition/inception_v3",
      "run_type": "iteration",
      "repetitions": 1,
      "repetition_index": 0,
      "threads": 1,
      "iterations": 1,
      "real_time": 3.6149649369999681e+09,
      "cpu_time": 3.6050961960000000e+09,
      "time_unit": "ns"
    }
  ]
}
'''

def test_render_table():
    columns = ['Benchmark', 'Time', 'CPU', 'Iterations']
    data = [
        ('benchmark_get_computation_graph_series_parallel_decomposition/split_test', '1885935 ns', '1851548 ns', '370'),
        ('benchmark_get_computation_graph_series_parallel_decomposition/transformer', '1264716033 ns', '1243613787 ns', '1'),
        ('benchmark_get_computation_graph_series_parallel_decomposition/bert', '844111583 ns', '833079544 ns', '1'),
        ('benchmark_get_computation_graph_series_parallel_decomposition/candle_uno', '301836060 ns', '296558251 ns', '2'),
        ('benchmark_get_computation_graph_series_parallel_decomposition/inception_v3', '3641691921 ns', '3583187857 ns', '1'),
    ]

    correct = (
        '---------------------------------------------------------------------------------------------------------------------\n'
        'Benchmark                                                                           Time             CPU   Iterations\n'
        '---------------------------------------------------------------------------------------------------------------------\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/split_test      1885935 ns      1851548 ns          370\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/transformer  1264716033 ns   1243613787 ns            1\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/bert          844111583 ns    833079544 ns            1\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/candle_uno    301836060 ns    296558251 ns            2\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/inception_v3 3641691921 ns   3583187857 ns            1'
    )

    sep = [1, 3, 3]

    result = render_table(columns, data, sep)

    assert result == correct

def test_benchmark_json_serialization():
    correct = json.loads(COMPILER_BENCHMARK_JSON)
    benchmark = BenchmarkResult.from_json(correct)
    result = benchmark.to_json()

    assert result == correct

def test_pretty_print_benchmark():
    j = json.loads(COMPILER_BENCHMARK_JSON)
    benchmark = BenchmarkResult.from_json(j)
    f = io.StringIO()
    pretty_print_benchmark(benchmark, f=f)
    result = f.getvalue()

    correct = (
        '2025-02-08T14:51:41-08:00\n'
        'Running /home/lockshaw/x/ff/gh/benchmarks-setup/build/release/lib/compiler/benchmark/compiler-benchmarks\n'
        'Run on (4 X 3898 MHz CPU s)\n'
        'CPU Caches:\n'
        '  L1 Data 32768 B (x4)\n'
        '  L1 Instruction 32768 B (x4)\n'
        '  L2 Unified 262144 B (x4)\n'
        '  L3 Unified 6291456 B (x1)\n'
        'Load Average: 1.00, 0.57, 0.56\n'
        '---------------------------------------------------------------------------------------------------------------------\n'
        'Benchmark                                                                           Time             CPU   Iterations\n'
        '---------------------------------------------------------------------------------------------------------------------\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/split_test      1864165 ns      1854311 ns          379\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/transformer  1240762592 ns   1237222060 ns            1\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/bert          830759563 ns    828507290 ns            1\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/candle_uno    294656262 ns    293803235 ns            2\n'
        'benchmark_get_computation_graph_series_parallel_decomposition/inception_v3 3614964937 ns   3605096196 ns            1\n'
    )

    assert result == correct
