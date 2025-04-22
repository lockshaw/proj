#include <doctest/doctest.h>
#include "not-kernels/not-kernels.h"
#include <cstdlib>

using namespace GPUTestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_not_kernels") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_NOT_KERNELS_CALL_NOT_KERNELS");
    CHECK(should_fail == nullptr);
  }
}
