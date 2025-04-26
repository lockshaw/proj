#include <doctest/doctest.h>
#include "not-kernels/not-kernels.h"
#include <cstdlib>

using namespace GPUTestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_not_kernels_cpu") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS_CPU");
    CHECK(should_fail == nullptr);
  }
}

TEST_SUITE(TP_CUDA_TEST_SUITE) {
  TEST_CASE("call_not_kernels_gpu") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS_GPU");
    CHECK(should_fail == nullptr);
  }
}
