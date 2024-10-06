#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "my_list.dtg.hh"
#include "rapidcheck.h"
#include "fmt/format.h"
#include "overload.h"

using namespace ::FlexFlow;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("MyList<T>") {
    SUBCASE("make empty list") {
      MyList<int> l = MyList<int>{MyListEmpty{}};
    }

    MyList<int> empty = MyList<int>{MyListEmpty{}};

    auto cons = [](int head, MyList<int> const &tail) {
      return MyList<int>{MyListCons<int>{head, tail}};
    };

    auto require_cons = [](MyList<int> const &l) {
      return l.get<MyListCons<int>>();
    };

    SUBCASE("make nonempty list") {
      MyList<int> l = cons(3, cons(2, cons(1, empty)));
    }

    SUBCASE("check accesses") {
      MyList<int> l = cons(3, cons(2, cons(1, empty)));

      SUBCASE("head") {
        CHECK(require_cons(l).head == 3);
      }

      SUBCASE("tail") {
        MyList<int> correct = cons(2, cons(1, empty));

        CHECK(require_cons(l).get_tail() == correct);
      }
    }

    auto tail = [&](MyList<int> const &l) {
      return require_cons(l).get_tail();
    };

    SUBCASE("empty list equality") {
      MyList<int> l = cons(3, cons(2, cons(1, empty)));
      CHECK(tail(tail(tail(l))) == empty);
    }

    std::function<int(MyList<int> const &)> len;

    len = [&](MyList<int> const &l) {
      return l.visit<int>(overload {
        [&](MyListCons<int> const &c) -> int { return 1 + len(c.get_tail()); },
        [](MyListEmpty const &) -> int { return 0; },
      });
    };

    SUBCASE("len (tests visit)") {
      MyList<int> l = cons(3, cons(2, cons(1, empty)));
      CHECK(len(l) == 3);
    }

    SUBCASE("json serialization->deserialization is identity") {
      MyList<int> l = cons(3, cons(2, cons(1, empty)));

      json j = l;
      MyList<int> l2 = j.get<MyList<int>>();

      CHECK(l2 == l);
    }

    SUBCASE("manual json deserialization") {
      json j = {
        {
          "__type",
          "MyList",
        },
        {
          "type", 
          "cons",
        },
        {
          "value", 
          {
            {
              "__type",
              "MyListCons",
            },
            {
              "head", 
              2,
            },
            {
              "tail", 
              {
                {
                  "type",
                  "empty",
                },
                {
                  "value",
                  {
                    {
                      "__type",
                      "MyListEmpty",
                    },
                  },
                },
              },
            },
          }
        },
      };

      MyList<int> result = j.get<MyList<int>>();
      MyList<int> correct = cons(2, empty);

      CHECK(result == correct);
    }

    SUBCASE("is hashable") {
      MyList<int> l1 = cons(2, cons(1, empty));
      MyList<int> l2 = cons(1, cons(2, empty));
      MyList<int> l3 = cons(2, empty);
      MyList<int> l4 = empty;

      auto get_hash = [](MyList<int> const &p) -> std::size_t {
        return std::hash<MyList<int>>{}(p);
      };

      CHECK(get_hash(l1) == get_hash(l1));
      CHECK(get_hash(l1) != get_hash(l2));
      CHECK(get_hash(l1) != get_hash(l3));
      CHECK(get_hash(l1) != get_hash(l4));

      CHECK(get_hash(l2) != get_hash(l1));
      CHECK(get_hash(l2) == get_hash(l2));
      CHECK(get_hash(l2) != get_hash(l3));
      CHECK(get_hash(l2) != get_hash(l4));

      CHECK(get_hash(l3) != get_hash(l1));
      CHECK(get_hash(l3) != get_hash(l2));
      CHECK(get_hash(l3) == get_hash(l3));
      CHECK(get_hash(l3) != get_hash(l4));

      CHECK(get_hash(l4) != get_hash(l1));
      CHECK(get_hash(l4) != get_hash(l2));
      CHECK(get_hash(l4) != get_hash(l3));
      CHECK(get_hash(l4) == get_hash(l4));
    }

    SUBCASE("to_string") {
      MyList<int> l = cons(2, cons(1, empty));       
      std::string correct = "<MyList cons=<MyListCons head=2 tail=<MyList cons=<MyListCons head=1 tail=<MyList empty=<MyListEmpty>>>>>>";
      SUBCASE("fmt") {
        std::string result = fmt::to_string(l);

        CHECK(result == correct);
      }

      SUBCASE("ostream") {
        std::ostringstream oss;
        oss << l;
        std::string result = oss.str();

        CHECK(result == correct);
      }
    }
  }
}
