#include <doctest/doctest.h>
#include "lib2/lib2.h"
#include <cstdlib>

using namespace TestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_lib2") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_LIB2_CALL_LIB2");
    CHECK(should_fail == nullptr);
  }

  TEST_CASE("other_lib2") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_LIB2_OTHER_LIB2");
    CHECK(should_fail == nullptr);
  }
}
