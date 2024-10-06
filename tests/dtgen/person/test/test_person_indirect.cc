#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "person_indirect.dtg.hh"
#include "fmt/format.h"
#include "json/optional.h"

using ::FlexFlow::PersonIndirect;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("PersonIndirect") {
    std::string first_name = "first";
    std::string last_name = "last";
    int age = 15;
    std::optional<PersonIndirect> spouse = PersonIndirect{ "a", "b", 121, std::nullopt };

    SUBCASE("brace construction") {
      PersonIndirect p = PersonIndirect{ first_name, last_name, age, spouse };
      CHECK(p.first_name == first_name);
      CHECK(p.last_name == last_name);
      CHECK(p.age == age);
      CHECK(p.get_spouse() == spouse);
    };

    SUBCASE("paren construction") {
      PersonIndirect p(first_name, last_name, age, spouse);
      CHECK(p.first_name == first_name);
      CHECK(p.last_name == last_name);
      CHECK(p.age == age);
      CHECK(p.get_spouse() == spouse);
    }

    SUBCASE("assignment") {
      PersonIndirect p = PersonIndirect{ "not-first", "not-last", 100, std::nullopt };
      PersonIndirect p2 = PersonIndirect{ first_name, last_name, age, spouse };

      p = p2;

      CHECK(p.first_name == first_name);
      CHECK(p.last_name == last_name);
      CHECK(p.age == age);
      CHECK(p.get_spouse() == spouse);
    }

    SUBCASE("copy constructor") {
      PersonIndirect p2 = PersonIndirect{ first_name, last_name, age, spouse };
      PersonIndirect p(p2);

      CHECK(p.first_name == first_name);
      CHECK(p.last_name == last_name);
      CHECK(p.age == age);
      CHECK(p.get_spouse() == spouse);  
    }

    SUBCASE("no default constructor") {
      CHECK(!std::is_default_constructible_v<PersonIndirect>);
    }

    SUBCASE("manual json deserialization") {
      json j = {
        {"first_name", first_name},
        {"last_name", last_name},
        {"age_in_years", age},
        {"spouse", spouse},
      };

      PersonIndirect p = j.get<PersonIndirect>();

      CHECK(p.first_name == first_name);
      CHECK(p.last_name == last_name);
      CHECK(p.age == age);
      CHECK(p.get_spouse() == spouse);
    }

    SUBCASE("json serialization->deserialization is identity") {
      PersonIndirect p = PersonIndirect{ first_name, last_name, age, spouse };

      json j = p;
      PersonIndirect p2 = j.get<PersonIndirect>();
      
      CHECK(p2 == p);
    }

    SUBCASE("is hashable") {
      PersonIndirect p1 = PersonIndirect{ first_name, last_name, age, spouse };
      PersonIndirect p2 = PersonIndirect{ first_name, last_name, age + 1, spouse };
      PersonIndirect p3 = PersonIndirect{ first_name + "a", last_name, age, spouse };
      PersonIndirect p4 = PersonIndirect{ first_name, last_name + "a", age, spouse };
      PersonIndirect p5 = PersonIndirect{ first_name, last_name, age, std::nullopt };

      auto get_hash = [](PersonIndirect const &p) -> std::size_t {
        return std::hash<PersonIndirect>{}(p);
      };

      CHECK(get_hash(p1) == get_hash(p1));
      CHECK(get_hash(p1) != get_hash(p2));
      CHECK(get_hash(p1) != get_hash(p3));
      CHECK(get_hash(p1) != get_hash(p4));
      CHECK(get_hash(p1) != get_hash(p5));

      CHECK(get_hash(p2) != get_hash(p1));
      CHECK(get_hash(p2) == get_hash(p2));
      CHECK(get_hash(p2) != get_hash(p3));
      CHECK(get_hash(p2) != get_hash(p4));
      CHECK(get_hash(p2) != get_hash(p5));

      CHECK(get_hash(p3) != get_hash(p1));
      CHECK(get_hash(p3) != get_hash(p2));
      CHECK(get_hash(p3) == get_hash(p3));
      CHECK(get_hash(p3) != get_hash(p4));
      CHECK(get_hash(p3) != get_hash(p5));

      CHECK(get_hash(p4) != get_hash(p1));
      CHECK(get_hash(p4) != get_hash(p2));
      CHECK(get_hash(p4) != get_hash(p3));
      CHECK(get_hash(p4) == get_hash(p4));
      CHECK(get_hash(p4) != get_hash(p5));

      CHECK(get_hash(p5) != get_hash(p1));
      CHECK(get_hash(p5) != get_hash(p2));
      CHECK(get_hash(p5) != get_hash(p3));
      CHECK(get_hash(p5) != get_hash(p4));
      CHECK(get_hash(p5) == get_hash(p5));
    }

    SUBCASE("fmt") {
      PersonIndirect p = PersonIndirect{ first_name, last_name, age, spouse };
      std::string correct = "<PersonIndirect first_name=first last_name=last age=15 spouse=<PersonIndirect first_name=a last_name=b age=121 spouse=nullopt>>";
      CHECK(fmt::to_string(p) == correct);
    }

    SUBCASE("ostream") {
      PersonIndirect p = PersonIndirect{ first_name, last_name, age, spouse };
      std::string correct = "<PersonIndirect first_name=first last_name=last age=15 spouse=<PersonIndirect first_name=a last_name=b age=121 spouse=nullopt>>";
      std::ostringstream oss;
      oss << p;
      CHECK(oss.str() == correct);
    }
  }
}
