#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <type_traits>
#include <rapidcheck.h>
#include "person/person.dtg.hh"
#include <fmt/format.h>

using ::FlexFlow::Person;
using ::nlohmann::json;

TEST_SUITE(TP_TEST_SUITE) {
  std::string first_name = "first";
  std::string last_name = "last";
  int age = 15;

  TEST_CASE("brace construction (Person)") {
    Person p = Person{ first_name, last_name, age };
    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  };

  TEST_CASE("paren construction (Person)") {
    Person p(first_name, last_name, age);
    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("assignment (Person)") {
    Person p = Person{ "not-first", "not-last", 100 };
    Person p2 = Person{ first_name, last_name, age };

    p = p2;

    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("copy constructor (Person)") {
    Person p2 = Person{ first_name, last_name, age };
    Person p(p2);

    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("no default constructor (Person)") {
    CHECK(!std::is_default_constructible_v<Person>);
  }

  TEST_CASE("manual json deserialization (Person)") {
    json j = {
      {"first_name", first_name},
      {"last_name", last_name},
      {"age_in_years", age},
    };

    Person p = j.get<Person>();

    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("json serialization->deserialization is identity (Person)") {
    Person p = Person{ first_name, last_name, age };

    json j = p;
    Person p2 = j.get<Person>();

    CHECK(p2 == p);
  }

  TEST_CASE("is hashable (Person)") {
    Person p1 = Person{ first_name, last_name, age };
    Person p2 = Person{ first_name, last_name, age + 1 };
    Person p3 = Person{ first_name + "a", last_name, age };
    Person p4 = Person{ first_name, last_name + "a", age };

    auto get_hash = [](Person const &p) -> std::size_t {
      return std::hash<Person>{}(p);
    };

    CHECK(get_hash(p1) == get_hash(p1));
    CHECK(get_hash(p1) != get_hash(p2));
    CHECK(get_hash(p1) != get_hash(p3));
    CHECK(get_hash(p1) != get_hash(p4));

    CHECK(get_hash(p2) != get_hash(p1));
    CHECK(get_hash(p2) == get_hash(p2));
    CHECK(get_hash(p2) != get_hash(p3));
    CHECK(get_hash(p2) != get_hash(p4));

    CHECK(get_hash(p3) != get_hash(p1));
    CHECK(get_hash(p3) != get_hash(p2));
    CHECK(get_hash(p3) == get_hash(p3));
    CHECK(get_hash(p3) != get_hash(p4));

    CHECK(get_hash(p4) != get_hash(p1));
    CHECK(get_hash(p4) != get_hash(p2));
    CHECK(get_hash(p4) != get_hash(p3));
    CHECK(get_hash(p4) == get_hash(p4));
  }

  TEST_CASE("rapidcheck example (Person)") {
    auto get_hash = [](Person const &p) -> std::size_t {
      return std::hash<Person>{}(p);
    };

    rc::check([&](Person const &p, Person const &p2) {
      CHECK((p == p2) == (get_hash(p) == get_hash(p2)));
    });
  }

  TEST_CASE("fmt (Person)") {
    Person p = Person{ first_name, last_name, age };
    std::string correct = "{\"__type\":\"Person\",\"age_in_years\":15,\"first_name\":\"first\",\"last_name\":\"last\"}";
    CHECK(fmt::to_string(p) == correct);
  }

  TEST_CASE("ostream (Person)") {
    Person p = Person{ first_name, last_name, age };
    std::string correct = "{\"__type\":\"Person\",\"age_in_years\":15,\"first_name\":\"first\",\"last_name\":\"last\"}";
    std::ostringstream oss;
    oss << p;
    CHECK(oss.str() == correct);
  }

  TEST_CASE("debug_to_string (Person)") {
    Person p = Person{ first_name, last_name, age };
    std::string correct = "{\"__type\":\"Person\",\"age_in_years\":15,\"first_name\":\"first\",\"last_name\":\"last\"}";
    std::string result = p.debug_to_string();
    CHECK(result == correct);
  }
}
