#include <doctest/doctest.h>
#include <type_traits>
#include "person/non_jsonable_variant.dtg.hh"
#include <rapidcheck.h>
#include <fmt/format.h>
#include <string>

using ::FlexFlow::NonJsonableVariant;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("NonJsonableVariant") {
    int i = 5;
    bool b = true;

    SUBCASE("brace construction (int)") {
      auto x = NonJsonableVariant{i};
      CHECK(x.has<int>());
      CHECK(!x.has<bool>());
      CHECK(x.get<int>() == i);
    }

    SUBCASE("brace construction (bool)") {
      auto x = NonJsonableVariant{b};
      CHECK(x.has<bool>());
      CHECK(!x.has<int>());
      CHECK(x.get<bool>() == b);
    }

    SUBCASE("assignment") {
      NonJsonableVariant x = NonJsonableVariant{i};
      NonJsonableVariant x2 = x;

      CHECK(x.has<int>());
      CHECK(x2.has<int>());
      CHECK(x.get<int>() == x2.get<int>());
    }

    SUBCASE("visit") {
      NonJsonableVariant x = NonJsonableVariant{i};

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
      auto x = NonJsonableVariant{i};
      NonJsonableVariant x2 = x;

      auto x3 = NonJsonableVariant{b};

      CHECK(x == x2);
      CHECK(!(x == x3));
    }

    SUBCASE("operator!=") {
      auto x = NonJsonableVariant{i};
      NonJsonableVariant x2 = x;

      auto x3 = NonJsonableVariant{b};

      CHECK(!(x != x2));
      CHECK(x != x3);
    }

    SUBCASE("operator<") {
      auto xi1 = NonJsonableVariant{i};
      auto xi2 = NonJsonableVariant{i+1};

      auto xb1 = NonJsonableVariant{false};
      auto xb2 = NonJsonableVariant{true};

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
      auto xi1 = NonJsonableVariant{4};
      auto xi2 = NonJsonableVariant{2};
      auto xb = NonJsonableVariant{false};

      CHECK(xi1.index() == xi2.index());
      CHECK(xb.index() != xi2.index());

      auto get_hash = [](NonJsonableVariant const &x) -> std::size_t {
        return std::hash<NonJsonableVariant>{}(x);
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

    SUBCASE("fmt (bool)") {
      NonJsonableVariant x = NonJsonableVariant{b};

      std::string correct = "<NonJsonableVariant bool=1>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("fmt (int)") {
      NonJsonableVariant x = NonJsonableVariant{i};

      std::string correct = "<NonJsonableVariant int=5>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("ostream operator<< (bool)") {
      NonJsonableVariant x = NonJsonableVariant{b};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<NonJsonableVariant bool=1>";
      CHECK(result == correct);
    }

    SUBCASE("ostream operator<< (int)") {
      NonJsonableVariant x = NonJsonableVariant{i};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<NonJsonableVariant int=5>";
      CHECK(result == correct);
    }

    SUBCASE("debug_to_string (bool)") {
      NonJsonableVariant x = NonJsonableVariant{b};

      std::string result = x.debug_to_string();
      std::string correct = "<NonJsonableVariant bool=1>";

      CHECK(result == correct);
    }

    SUBCASE("ostream operator<< (int)") {
      NonJsonableVariant x = NonJsonableVariant{i};

      std::string result = x.debug_to_string();
      std::string correct = "<NonJsonableVariant int=5>";

      CHECK(result == correct);
    }

    SUBCASE("rapidcheck example") {
      rc::check([&](NonJsonableVariant const &x) {
        RC_ASSERT(x.has<int>() || x.has<bool>());
      });
    }
  }
}
