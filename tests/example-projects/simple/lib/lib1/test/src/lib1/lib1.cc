#include <doctest/doctest.h>
#include "lib1/lib1.h"

using namespace TestProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("call_lib1") {
    CHECK(true);
  }

  TEST_CASE("other_lib1") {
    CHECK(true);
  }
}
