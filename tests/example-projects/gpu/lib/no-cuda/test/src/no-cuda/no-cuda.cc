#include <doctest/doctest.h>
#include "no-cuda/no-cuda.h"
#include <cstdlib>

using namespace GPUTestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_no_cuda") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_NO_CUDA_CALL_NO_CUDA");
    CHECK(should_fail == nullptr);
  }
}
