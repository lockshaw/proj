#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "my_template_variant.dtg.hh"
#include "rapidcheck.h"
#include "fmt/format.h"
#include <string>

using ::FlexFlow::MyTemplateVariant;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("MyTemplateVariant") {
    int i = 5;
    bool b = true;

    SUBCASE("brace construction (int)") {
      auto x = MyTemplateVariant<int, bool>{i};
      CHECK(x.has<int>());
      CHECK(!x.has<bool>());
      CHECK(x.get<int>() == i);
    }

    SUBCASE("brace construction (bool)") {
      auto x = MyTemplateVariant<int, bool>{b};
      CHECK(x.has<bool>());
      CHECK(!x.has<int>());
      CHECK(x.get<bool>() == b);
    }

    SUBCASE("assignment") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{i};
      MyTemplateVariant<int, bool> x2 = x;

      CHECK(x.has<int>());
      CHECK(x2.has<int>());
      CHECK(x.get<int>() == x2.get<int>());
    }

    SUBCASE("visit") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{i};

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
      auto x = MyTemplateVariant<int, bool>{i};
      MyTemplateVariant<int, bool> x2 = x;

      auto x3 = MyTemplateVariant<int, bool>{b};

      CHECK(x == x2);
      CHECK(!(x == x3));
    }

    SUBCASE("operator!=") {
      auto x = MyTemplateVariant<int, bool>{i};
      MyTemplateVariant<int, bool> x2 = x;

      auto x3 = MyTemplateVariant<int, bool>{b};

      CHECK(!(x != x2));
      CHECK(x != x3);
    }

    SUBCASE("operator<") {
      auto xi1 = MyTemplateVariant<int, bool>{i};
      auto xi2 = MyTemplateVariant<int, bool>{i+1};

      auto xb1 = MyTemplateVariant<int, bool>{false};
      auto xb2 = MyTemplateVariant<int, bool>{true};

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
      auto xi1 = MyTemplateVariant<int, bool>{4};
      auto xi2 = MyTemplateVariant<int, bool>{2};
      auto xb = MyTemplateVariant<int, bool>{false};

      CHECK(xi1.index() == xi2.index());
      CHECK(xb.index() != xi2.index());

      auto get_hash = [](MyTemplateVariant<int, bool> const &x) -> std::size_t {
        return std::hash<MyTemplateVariant<int, bool>>{}(x);
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
        {"type", "T2"},
        {"value", b},
      };

      MyTemplateVariant<int, bool> result = j.get<MyTemplateVariant<int, bool>>();

      MyTemplateVariant<int, bool> correct = MyTemplateVariant<int, bool>{b};

      CHECK(result == correct);
    }

    SUBCASE("manual json deserialization (int)") {
      json j = {
        {"type", "T1"},
        {"value", i},
      };

      MyTemplateVariant<int, bool> result = j.get<MyTemplateVariant<int, bool>>();

      MyTemplateVariant<int, bool> correct = MyTemplateVariant<int, bool>{i};

      CHECK(result == correct);
    }

    SUBCASE("json serialization->deserialization is identity (bool)") {
      MyTemplateVariant<int, bool> correct = MyTemplateVariant<int, bool>{b};

      json j = correct;
      MyTemplateVariant<int, bool> result = j.get<MyTemplateVariant<int, bool>>();
      
      CHECK(result == correct);
    }

    SUBCASE("json serialization->deserialization is identity (int)") {
      MyTemplateVariant<int, bool> correct = MyTemplateVariant<int, bool>{i};

      json j = correct;
      MyTemplateVariant<int, bool> result = j.get<MyTemplateVariant<int, bool>>();
      
      CHECK(result == correct);
    }

    SUBCASE("fmt (bool)") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{b};

      std::string correct = "<MyTemplateVariant T2=1>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("fmt (int)") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{i};

      std::string correct = "<MyTemplateVariant T1=5>";
      CHECK(fmt::to_string(x) == correct);
    }

    SUBCASE("ostream operator<< (bool)") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{b};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<MyTemplateVariant T2=1>";
      CHECK(result == correct);
    }

    SUBCASE("ostream operator<< (int)") {
      MyTemplateVariant<int, bool> x = MyTemplateVariant<int, bool>{i};

      std::ostringstream oss;
      oss << x;
      std::string result = oss.str();

      std::string correct = "<MyTemplateVariant T1=5>";
      CHECK(result == correct);
    }

    SUBCASE("rapidcheck example") {
      rc::check([&](MyTemplateVariant<int, bool> const &x) {
        RC_ASSERT(x.has<int>() || x.has<bool>());
      });
    }
  }
}
