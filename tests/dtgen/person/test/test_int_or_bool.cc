#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "int_or_bool.dtg.hh"
#include "rapidcheck.h"
#include "fmt/format.h"
#include <string>

using ::FlexFlow::IntOrBool;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  int i = 5;
  bool b = true;

  TEST_CASE("brace construction (int)") {
    auto x = IntOrBool{i};
    CHECK(x.has<int>());
    CHECK(!x.has<bool>());
    CHECK(x.get<int>() == i);
  }

  TEST_CASE("brace construction (bool)") {
    auto x = IntOrBool{b};
    CHECK(x.has<bool>());
    CHECK(!x.has<int>());
    CHECK(x.get<bool>() == b);
  }

  TEST_CASE("assignment") {
    IntOrBool x = IntOrBool{i};
    IntOrBool x2 = x;

    CHECK(x.has<int>());
    CHECK(x2.has<int>());
    CHECK(x.get<int>() == x2.get<int>());
  }

  TEST_CASE("visit") {
    IntOrBool x = IntOrBool{i};

    std::string result = x.visit<std::string>([](auto const &x) -> std::string {
      using T = std::decay_t<decltype(x)>;

      if constexpr (std::is_same_v<T, int>) {
        return "int";
      } else if constexpr (std::is_same_v<T, bool>) {
        return "bool";
      } else {
        static_assert(std::is_same_v<T, int>);
      }
    });
    std::string correct = "int";

    CHECK(result == correct);
  }

  TEST_CASE("operator==") {
    auto x = IntOrBool{i};
    IntOrBool x2 = x;

    auto x3 = IntOrBool{b};

    CHECK(x == x2);
    CHECK(!(x == x3));
  }

  TEST_CASE("operator!=") {
    auto x = IntOrBool{i};
    IntOrBool x2 = x;

    auto x3 = IntOrBool{b};

    CHECK(!(x != x2));
    CHECK(x != x3);
  }

  TEST_CASE("operator<") {
    auto xi1 = IntOrBool{i};
    auto xi2 = IntOrBool{i+1};

    auto xb1 = IntOrBool{false};
    auto xb2 = IntOrBool{true};

    CHECK(!(xi1 < xi1));
    CHECK(xi1 < xi2);
    CHECK(xi1 < xb1);
    CHECK(xi1 < xb2);

    CHECK(!(xi2 < xi1));
    CHECK(!(xi2 < xi2));
    CHECK(xi2 < xb1);
    CHECK(xi2 < xb2);

    CHECK(!(xb1 < xi1));
    CHECK(!(xb1 < xi2));
    CHECK(!(xb1 < xb1));
    CHECK(xb1 < xb2);

    CHECK(!(xb2 < xi1));
    CHECK(!(xb2 < xi2));
    CHECK(!(xb2 < xb1));
    CHECK(!(xb2 < xb2));
  }

  TEST_CASE("std::hash") {
    auto xi1 = IntOrBool{0};
    auto xi2 = IntOrBool{1};
    auto xb = IntOrBool{false};

    auto get_hash = [](IntOrBool const &x) -> std::size_t {
      return std::hash<IntOrBool>{}(x);
    };

    CHECK(get_hash(xi1) == get_hash(xi1));
    CHECK(get_hash(xi1) != get_hash(xi2));
    CHECK(get_hash(xi1) != get_hash(xb));

    CHECK(get_hash(xi2) != get_hash(xi1));
    CHECK(get_hash(xi2) == get_hash(xi2));
    CHECK(get_hash(xi2) != get_hash(xb));

    CHECK(get_hash(xb) != get_hash(xi1));
    CHECK(get_hash(xb) != get_hash(xi2));
    CHECK(get_hash(xb) == get_hash(xb));
  }

  TEST_CASE("manual json deserialization (bool)") {
    json j = {
      {"type", "bool"},
      {"value", b},
    };

    IntOrBool result = j.get<IntOrBool>();

    IntOrBool correct = IntOrBool{b};

    CHECK(result == correct);
  }

  TEST_CASE("manual json deserialization (int)") {
    json j = {
      {"type", "int"},
      {"value", i},
    };

    IntOrBool result = j.get<IntOrBool>();

    IntOrBool correct = IntOrBool{i};

    CHECK(result == correct);
  }

  TEST_CASE("json serialization->deserialization is identity (bool)") {
    IntOrBool correct = IntOrBool{b};

    json j = correct;
    IntOrBool result = j.get<IntOrBool>();
    
    CHECK(result == correct);
  }

  TEST_CASE("json serialization->deserialization is identity (int)") {
    IntOrBool correct = IntOrBool{i};

    json j = correct;
    IntOrBool result = j.get<IntOrBool>();
    
    CHECK(result == correct);
  }

  TEST_CASE("fmt (bool)") {
    IntOrBool x = IntOrBool{b};

    std::string correct = "<IntOrBool bool=true>";
    CHECK(fmt::to_string(x) == correct);
  }

  TEST_CASE("fmt (int)") {
    IntOrBool x = IntOrBool{i};

    std::string correct = "<IntOrBool int=5>";
    CHECK(fmt::to_string(x) == correct);
  }

  TEST_CASE("ostream operator<< (bool)") {
    IntOrBool x = IntOrBool{b};

    std::ostringstream oss;
    oss << x;
    std::string result = oss.str();

    std::string correct = "<IntOrBool bool=true>";
    CHECK(result == correct);
  }

  TEST_CASE("ostream operator<< (int)") {
    IntOrBool x = IntOrBool{i};

    std::ostringstream oss;
    oss << x;
    std::string result = oss.str();

    std::string correct = "<IntOrBool int=5>";
    CHECK(result == correct);
  }


}
