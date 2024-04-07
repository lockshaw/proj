#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"
#include <type_traits>
#include "person.hh"

using ::FlexFlow::Person;

TEST_SUITE(FF_TEST_SUITE) {
  std::string first_name = "first";
  std::string last_name = "last";
  int age = 15;

  TEST_CASE("brace construction") {
    Person p = { first_name, last_name, age };
    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  };

  TEST_CASE("paren construction") {
    Person p(first_name, last_name, age);
    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("assignment") {
    Person p = { "not-first", "not-last", 100 };
    Person p2 = { first_name, last_name, age };

    p = p2;

    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("copy constructor") {
    Person p2 = { first_name, last_name, age };
    Person p(p2);

    CHECK(p.first_name == first_name);
    CHECK(p.last_name == last_name);
    CHECK(p.age == age);
  }

  TEST_CASE("no default constructor") {
    CHECK(!std::is_default_constructible_v<Person>);
  }
}
