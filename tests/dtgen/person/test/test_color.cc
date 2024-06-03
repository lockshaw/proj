#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "color.dtg.hh"
#include "rapidcheck.h"
#include "fmt/format.h"

using ::FlexFlow::Color;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("manual json deserialization") {
    json j = "RED";

    Color c = j.get<Color>();
    
    CHECK(c == Color::RED);
  }

  TEST_CASE("json serialization->deserialization is identity") {
    Color c = Color::BLUE;

    json j = c;
    Color c2 = j.get<Color>();
    
    CHECK(c2 == c);
  }

  TEST_CASE("is hashable") {
    Color c1 = Color::RED;
    Color c2 = Color::BLUE;
    Color c3 = Color::YELLOW;

    auto get_hash = [](Color const &c) -> std::size_t {
      return std::hash<Color>{}(c);
    };

    CHECK(get_hash(c1) == get_hash(c1));
    CHECK(get_hash(c1) != get_hash(c2));
    CHECK(get_hash(c1) != get_hash(c3));

    CHECK(get_hash(c2) != get_hash(c1));
    CHECK(get_hash(c2) == get_hash(c2));
    CHECK(get_hash(c2) != get_hash(c3));

    CHECK(get_hash(c3) != get_hash(c1));
    CHECK(get_hash(c3) != get_hash(c2));
    CHECK(get_hash(c3) == get_hash(c3));
  }

  TEST_CASE("rapidcheck example") {
    auto get_hash = [](Color const &c) -> std::size_t {
      return std::hash<Color>{}(c);
    };

    rc::check([&](Color const &c, Color const &c2) {
      CHECK((c == c2) == (get_hash(c) == get_hash(c2)));
    });
  }

  TEST_CASE("fmt") {
    Color c = Color::YELLOW;
    std::string correct = "YELLOW";
    CHECK(fmt::to_string(c) == correct);
  }

  TEST_CASE("ostream") {
    Color c = Color::BLUE;
    std::string correct = "BLUE";
    std::ostringstream oss;
    oss << c;
    CHECK(oss.str() == correct);
  }
}
