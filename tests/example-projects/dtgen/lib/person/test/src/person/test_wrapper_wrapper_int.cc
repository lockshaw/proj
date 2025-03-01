#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <type_traits>
#include <rapidcheck.h>
#include "person/wrapper_wrapper_int.dtg.hh"
#include <fmt/format.h>

using ::FlexFlow::wrapper_wrapper_int_t;
using ::FlexFlow::wrapper_int_t;

// used for testing string conversion for multiply-wrapped types,
// which have had non-termination issues in the past due to implicit
// constructors

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("fmt") {
    wrapper_wrapper_int_t x = wrapper_wrapper_int_t{wrapper_int_t{5}};
    std::string correct = "<wrapper_wrapper_int_t raw_wrapper_int=<wrapper_int_t raw_int=5>>";
    CHECK(fmt::to_string(x) == correct);
  }
}
