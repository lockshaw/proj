#include <doctest/doctest.h>
#include <type_traits>
#include <rapidcheck.h>
#include "person/non_jsonable_person.dtg.hh"
#include <fmt/format.h>

using ::FlexFlow::NonJsonablePerson;

static std::string get_first_name() {
  return "first";
}

static std::string get_last_name() {
  return "last";
}

static int age = 15;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("brace construction (NonJsonablePerson)") {
    NonJsonablePerson p = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    CHECK(p.first_name == get_first_name());
    CHECK(p.last_name == get_last_name());
    CHECK(p.age == age);
  };

  TEST_CASE("paren construction (NonJsonablePerson)") {
    NonJsonablePerson p(get_first_name(), get_last_name(), age);
    CHECK(p.first_name == get_first_name());
    CHECK(p.last_name == get_last_name());
    CHECK(p.age == age);
  }

  TEST_CASE("assignment (NonJsonablePerson)") {
    NonJsonablePerson p = NonJsonablePerson{ "not-first", "not-last", 100 };
    NonJsonablePerson p2 = NonJsonablePerson{ get_first_name(), get_last_name(), age };

    p = p2;

    CHECK(p.first_name == get_first_name());
    CHECK(p.last_name == get_last_name());
    CHECK(p.age == age);
  }

  TEST_CASE("copy constructor (NonJsonablePerson)") {
    NonJsonablePerson p2 = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    NonJsonablePerson p(p2);

    CHECK(p.first_name == get_first_name());
    CHECK(p.last_name == get_last_name());
    CHECK(p.age == age);
  }

  TEST_CASE("no default constructor (NonJsonablePerson)") {
    CHECK(!std::is_default_constructible_v<NonJsonablePerson>);
  }

  TEST_CASE("is hashable (NonJsonablePerson)") {
    NonJsonablePerson p1 = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    NonJsonablePerson p2 = NonJsonablePerson{ get_first_name(), get_last_name(), age + 1 };
    NonJsonablePerson p3 = NonJsonablePerson{ get_first_name() + "a", get_last_name(), age };
    NonJsonablePerson p4 = NonJsonablePerson{ get_first_name(), get_last_name() + "a", age };

    auto get_hash = [](NonJsonablePerson const &p) -> std::size_t {
      return std::hash<NonJsonablePerson>{}(p);
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

  TEST_CASE("rapidcheck example (NonJsonablePerson)") {
    auto get_hash = [](NonJsonablePerson const &p) -> std::size_t {
      return std::hash<NonJsonablePerson>{}(p);
    };

    rc::check([&](NonJsonablePerson const &p, NonJsonablePerson const &p2) {
      CHECK((p == p2) == (get_hash(p) == get_hash(p2)));
    });
  }

  TEST_CASE("fmt (NonJsonablePerson)") {
    NonJsonablePerson p = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    std::string correct = "<NonJsonablePerson first_name=first last_name=last age=15>";
    CHECK(fmt::to_string(p) == correct);
  }

  TEST_CASE("ostream (NonJsonablePerson)") {
    NonJsonablePerson p = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    std::string correct = "<NonJsonablePerson first_name=first last_name=last age=15>";
    std::ostringstream oss;
    oss << p;
    CHECK(oss.str() == correct);
  }

  TEST_CASE("debug_to_string (NonJsonablePerson)") {
    NonJsonablePerson p = NonJsonablePerson{ get_first_name(), get_last_name(), age };
    std::string correct = "<NonJsonablePerson first_name=first last_name=last age=15>";
;
    std::string result = p.debug_to_string();
    CHECK(result == correct);
  }
}
