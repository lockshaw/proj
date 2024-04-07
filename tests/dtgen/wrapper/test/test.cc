#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"
#include <type_traits>
#include "wrapper.hh"

using ::FlexFlow::wrapper_t;

TEST_SUITE(FF_TEST_SUITE) {
  int value = 5;

  TEST_CASE("brace construction") {
    wrapper_t<int> x = {value};
    CHECK(x.value == value);
  };

  TEST_CASE("paren construction") {
    wrapper_t<int> x(value);
    CHECK(x.value == value);
  }

  TEST_CASE("assignment") {
    wrapper_t<int> x = 100;
    wrapper_t<int> x2 = {value};

    x = x2;

    CHECK(x.value == value);
  }

  TEST_CASE("copy constructor") {
    wrapper_t<int> x2 = {value};
    wrapper_t<int> x(x2);

    CHECK(x.value == value);
  }

  TEST_CASE("no default constructor") {
    CHECK(!std::is_default_constructible_v<wrapper_t<int>>);
  }
}
