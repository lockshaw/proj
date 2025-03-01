#include <benchmark/benchmark.h>
#include "lib1/lib1.h"

using namespace TestProject;

static void example_benchmark(benchmark::State &state) {
  int arg1 = state.range(0);
  int arg2 = state.range(1);

  for (auto _ : state) {
    int result = 0;
    for (int i = 0; i < arg1; i++) {
      result += i;
      for (int j = 0; j < arg2; j++) {
        result += j;
      }
    }
  }
}

BENCHMARK(example_benchmark)
    ->ArgsProduct({
        benchmark::CreateDenseRange(25, 75, /*step=*/25),
        benchmark::CreateRange(16, 256, /*multi=*/54),
    });
