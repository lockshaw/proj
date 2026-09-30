#include "lib1/lib1.h"
#include <cstdlib>
#include <iostream>

namespace TestProject {

void example_benchmark() {

  char const *should_fail_budget = std::getenv("PROJ_TESTS_FAIL_LIB1_BENCHMARK_BUDGET");

  volatile int arg1 = 10;
  volatile int arg2 = 10;
  if (should_fail_budget) {
    arg1 = 500;
    arg2 = 500;
  }

#ifdef LIB1_BENCHMARKS_FAIL_BUILD
  some_function_that_does_not_exist();
#endif

  volatile int result = 0;
  for (volatile int i = 0; i < arg1; i++) {
    result++;
    for (volatile int j = 0; j < arg2; j++) {
      result++;
    }
  }

}

}
