#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <type_traits>
#include "person/empty.dtg.hh"
#include <rapidcheck.h>
#include <fmt/format.h>

using ::FlexFlow::empty_t;
using ::nlohmann::json;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("default construction") {
    empty_t p;
  };

  TEST_CASE("brace construction") {
    empty_t p = { };
  };

  TEST_CASE("assignment") {
    empty_t p = {};
    empty_t p2 = {};

    p = p2;
  }

  TEST_CASE("copy constructor") {
    empty_t p2 = {};
    empty_t p(p2);
  }

  TEST_CASE("manual json deserialization") {
    json j = { };

    empty_t p = j.get<empty_t>();
  }

  TEST_CASE("json serialization->deserialization is identity") {
    empty_t p = {};

    json j = p;
    empty_t p2 = j.get<empty_t>();
    
    CHECK(p2 == p);
  }

  TEST_CASE("is hashable") {
    empty_t p1 = {};
    empty_t p2 = {};

    auto get_hash = [](empty_t const &p) -> std::size_t {
      return std::hash<empty_t>{}(p);
    };

    CHECK(get_hash(p1) == get_hash(p2));
  }

  TEST_CASE("rapidcheck example") {
    auto get_hash = [](empty_t const &p) -> std::size_t {
      return std::hash<empty_t>{}(p);
    };

    rc::check([&](empty_t const &p, empty_t const &p2) {
      CHECK((p == p2) == (get_hash(p) == get_hash(p2)));
    });
  }

  TEST_CASE("fmt") {
    empty_t p = {};
    std::string correct = "<empty_t>";
    CHECK(fmt::to_string(p) == correct);
  }

  TEST_CASE("ostream") {
    empty_t p = {};
    std::string correct = "<empty_t>";
    std::ostringstream oss;
    oss << p;
    CHECK(oss.str() == correct);
  }
}
