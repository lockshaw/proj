#include <doctest/doctest.h>
#include "only-cuda/only-cuda.h"
#include <cstdlib>

using namespace GPUTestProject;

TEST_SUITE(TP_CUDA_TEST_SUITE) {
  TEST_CASE("call_only_cuda") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_ONLY_CUDA_CALL_ONLY_CUDA");
    CHECK(should_fail == nullptr);
  }
}
