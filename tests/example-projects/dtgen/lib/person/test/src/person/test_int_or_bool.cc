#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <type_traits>
#include "person/int_or_bool.dtg.hh"
#include <rapidcheck.h>
#include <fmt/format.h>
#include <string>

using ::FlexFlow::IntOrBool;
using ::nlohmann::json;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("IntOrBool") {
    int i = 5;
    bool b = true;

    SUBCASE("brace construction (int)") {
      auto x = IntOrBool{i};
      CHECK(x.has<int>());
      CHECK(!x.has<bool>());
      CHECK(x.get<int>() == i);
    }

    SUBCASE("brace construction (bool)") {
      auto x = IntOrBool{b};
      CHECK(x.has<bool>());
      CHECK(!x.has<int>());
      CHECK(x.get<bool>() == b);
    }

    SUBCASE("assignment") {
      IntOrBool x = IntOrBool{i};
      IntOrBool x2 = x;

      CHECK(x.has<int>());
      CHECK(x2.has<int>());
      CHECK(x.get<int>() == x2.get<int>());
    }

    SUBCASE("visit") {
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

    SUBCASE("operator==") {
      auto x = IntOrBool{i};
      IntOrBool x2 = x;

      auto x3 = IntOrBool{b};

      CHECK(x == x2);
      CHECK(!(x == x3));
    }

    SUBCASE("operator!=") {
      auto x = IntOrBool{i};
      IntOrBool x2 = x;

      auto x3 = IntOrBool{b};

      CHECK(!(x != x2));
      CHECK(x != x3);
    }

    SUBCASE("operator<") {
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

    SUBCASE("std::hash") {
      auto xi1 = IntOrBool{4};
      auto xi2 = IntOrBool{2};
      auto xb = IntOrBool{false};

      CHECK(xi1.index() == xi2.index());
      CHECK(xb.index() != xi2.index());

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

    SUBCASE("manual json deserialization (bool)") {
      json j = {
        {"type", "bool"},
        {"value", b},
      };

      IntOrBool result = j.get<IntOrBool>();

      IntOrBool correct = IntOrBool{b};

      CHECK(result == correct);
    }

    SUBCASE("manual json deserialization (int)") {
      json j = {
        {"type", "int"},
        {"value", i},
      };

      IntOrBool result = j.get<IntOrBool>();

      IntOrBool correct = IntOrBool{i};

      CHECK(result == correct);
    }

    SUBCASE("json serialization->deserialization is identity (bool)") {
      IntOrBool correct = IntOrBool{b};

      json j = correct;
      IntOrBool result = j.get<IntOrBool>();
      
      CHECK(result == correct);
    }

    SUBCASE("json serialization->deserialization is identity (int)") {
      IntOrBool correct = IntOrBool{i};

      json j = correct;
      IntOrBool result = j.get<IntOrBool>();
      
      CHECK(result == correct);
    }

    SUBCASE("fmt (bool)") {
      IntOrBool x = IntOrBool{b};

      std::string correct = "<IntOrBool bool=1>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("fmt (int)") {
      IntOrBool x = IntOrBool{i};

      std::string correct = "<IntOrBool int=5>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("ostream operator<< (bool)") {
      IntOrBool x = IntOrBool{b};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<IntOrBool bool=1>";
      CHECK(result == correct);
    }

    SUBCASE("ostream operator<< (int)") {
      IntOrBool x = IntOrBool{i};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<IntOrBool int=5>";
      CHECK(result == correct);
    }

    SUBCASE("rapidcheck example") {
      rc::check([&](IntOrBool const &x) {
        RC_ASSERT(x.has<int>() || x.has<bool>());
      });
    }
  }
}
