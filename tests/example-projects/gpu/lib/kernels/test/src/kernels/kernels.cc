#include <doctest/doctest.h>
#include "kernels/kernels.h"
#include <cstdlib>

using namespace GPUTestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_kernels") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_KERNELS_CALL_KERNELS");
    CHECK(should_fail == nullptr);
  }
}
