#include <doctest/doctest.h>
#include "lib1/lib1.h"
#include <cstdlib>

using namespace TestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_lib1") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_LIB1_CALL_LIB1");
    CHECK(should_fail == nullptr);
  }

  TEST_CASE("other_lib1") {
    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_LIB1_OTHER_LIB1");
    CHECK(should_fail == nullptr);
  }
}
