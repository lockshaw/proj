#include <type_traits>
#include "wrapper/wrapper.dtg.hh"
#include <nlohmann/json.hpp>
#include <rapidcheck.h>
#include <doctest/doctest.h>

using ::FlexFlow::wrapper_t;
using ::nlohmann::json;

TEST_SUITE(TP_TEST_SUITE) {
  int value = 5;

  TEST_CASE("brace construction") {
    wrapper_t<int> x = wrapper_t{value};
    CHECK(x.value == value);
  };

  TEST_CASE("paren construction") {
    wrapper_t<int> x(value);
    CHECK(x.value == value);
  }

  TEST_CASE("assignment") {
    wrapper_t<int> x = wrapper_t{100};
    wrapper_t<int> x2 = wrapper_t{value};

    x = x2;

    CHECK(x.value == value);
  }

  TEST_CASE("copy constructor") {
    wrapper_t<int> x2 = wrapper_t{value};
    wrapper_t<int> x(x2);

    CHECK(x.value == value);
  }

  TEST_CASE("no default constructor") {
    CHECK(!std::is_default_constructible_v<wrapper_t<int>>);
  }

  TEST_CASE("manual json deserialization") {
    json j = {
      {"value", value},
    };

    wrapper_t<int> x = j.get<wrapper_t<int>>();

    CHECK(x.value == value);
  }

  TEST_CASE("json serialization->deserialization is identity") {
    wrapper_t<int> x = wrapper_t{ value };

    json j = x;
    wrapper_t<int> x2 = j.get<wrapper_t<int>>();
    
    CHECK(x2 == x);
  }

  TEST_CASE("is hashable") {
    wrapper_t<int> x1 = wrapper_t{ value };
    wrapper_t<int> x2 = wrapper_t{ value + 1 };

    auto get_hash = [](wrapper_t<int> const &x) -> std::size_t {
      return std::hash<wrapper_t<int>>{}(x);
    };

    CHECK(get_hash(x1) == get_hash(x1));
    CHECK(get_hash(x2) == get_hash(x2));
    CHECK(get_hash(x1) != get_hash(x2));
  }

  TEST_CASE("rapidcheck") {
    auto get_hash = [](wrapper_t<int> const &x) -> std::size_t {
      return std::hash<wrapper_t<int>>{}(x);
    };

    rc::check([&](wrapper_t<int> const &x, wrapper_t<int> const &x2) {
      CHECK((x == x2) == (get_hash(x) == get_hash(x2)));
    });
  }

  TEST_CASE("fmt") {
    wrapper_t<int> p = wrapper_t{ value };
    std::string correct = "<wrapper_t value=5>";
    CHECK(fmt::to_string(p) == correct);
  }

  TEST_CASE("ostream") {
    wrapper_t<int> p = wrapper_t{ value };
    std::string correct = "<wrapper_t value=5>";
    std::ostringstream oss;
    oss << p;
    CHECK(oss.str() == correct);
  }
}
