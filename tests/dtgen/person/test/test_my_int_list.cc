#include "doctest/doctest.h"
#include "nlohmann/json.hpp"
#include <type_traits>
#include "my_int_list.dtg.hh"
#include "rapidcheck.h"
#include "fmt/format.h"
#include "overload.h"

using namespace ::FlexFlow;
using ::nlohmann::json;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("MyList<T>") {
    SUBCASE("make empty list") {
      MyIntList l = MyIntList{MyListEmpty{}};
    }

    MyIntList empty = MyIntList{MyListEmpty{}};

    auto cons = [](int head, MyIntList const &tail) {
      return MyIntList{MyIntListCons{head, tail}};
    };

    auto require_cons = [](MyIntList const &l) {
      return l.get<MyIntListCons>();
    };

    SUBCASE("has") {
      SUBCASE("empty list") {
        MyIntList l = empty;

        CHECK(l.has<MyListEmpty>());
        CHECK_FALSE(l.has<MyIntListCons>());
      }

      SUBCASE("nonempty list") {
        MyIntList l = cons(1, empty);

        CHECK_FALSE(l.has<MyListEmpty>());
        CHECK(l.has<MyIntListCons>());
      }
    }

    SUBCASE("is methods") {
      SUBCASE("empty list") {
        MyIntList l = empty;

        CHECK(l.is_empty());
        CHECK_FALSE(l.is_cons());
      }

      SUBCASE("nonempty list") {
        MyIntList l = cons(1, empty);

        CHECK_FALSE(l.is_empty());
        CHECK(l.is_cons());
      }
    }


    SUBCASE("get") {
      SUBCASE("has empty list") {
        MyIntList l = empty;

        SUBCASE("get<MyListEmpty>") {
          MyListEmpty result = l.get<MyListEmpty>();
          MyListEmpty correct = MyListEmpty{};

          CHECK(result == correct);
        };

        SUBCASE("get<MyIntListCons>") {
          CHECK_THROWS(l.get<MyIntListCons>());
        }
      }

      SUBCASE("has nonempty list") {
        MyIntList l = cons(1, empty);

        SUBCASE("get<MyListEmpty>") {
          CHECK_THROWS(l.get<MyListEmpty>());
        }

        SUBCASE("get<MyIntListCons>") {
          MyIntListCons result = l.get<MyIntListCons>();
          MyIntListCons correct = MyIntListCons{1, empty};

          CHECK(result == correct);
        }
      }
    }

    SUBCASE("require methods") {
      SUBCASE("has empty list") {
        MyIntList l = empty;

        SUBCASE("require_empty") {
          MyListEmpty result = l.require_empty();
          MyListEmpty correct = MyListEmpty{};

          CHECK(result == correct);
        };

        SUBCASE("require_cons") {
          CHECK_THROWS(l.require_cons());
        }
      }

      SUBCASE("has nonempty list") {
        MyIntList l = cons(1, empty);

        SUBCASE("require_empty") {
          CHECK_THROWS(l.require_empty());
        }

        SUBCASE("require_cons") {
          MyIntListCons result = l.require_cons();
          MyIntListCons correct = MyIntListCons{1, empty};

          CHECK(result == correct);
        }
      }
    }

    SUBCASE("make nonempty list") {
      MyIntList l = cons(3, cons(2, cons(1, empty)));
    }

    SUBCASE("check accesses") {
      MyIntList l = cons(3, cons(2, cons(1, empty)));

      SUBCASE("head") {
        CHECK(require_cons(l).head == 3);
      }

      SUBCASE("tail") {
        MyIntList correct = cons(2, cons(1, empty));

        CHECK(require_cons(l).get_tail() == correct);
      }
    }


    auto tail = [&](MyIntList const &l) {
      return require_cons(l).get_tail();
    };

    SUBCASE("empty list equality") {
      MyIntList l = cons(3, cons(2, cons(1, empty)));
      CHECK(tail(tail(tail(l))) == empty);
    }

    std::function<int(MyIntList const &)> len;

    len = [&](MyIntList const &l) {
      return l.visit<int>(overload {
        [&](MyIntListCons const &c) -> int { return 1 + len(c.get_tail()); },
        [](MyListEmpty const &) -> int { return 0; },
      });
    };

    SUBCASE("len (tests visit)") {
      MyIntList l = cons(3, cons(2, cons(1, empty)));
      CHECK(len(l) == 3);
    }

    SUBCASE("json serialization->deserialization is identity") {
      MyIntList l = cons(3, cons(2, cons(1, empty)));

      json j = l;
      MyIntList l2 = j.get<MyIntList>();

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

      MyIntList result = j.get<MyIntList>();
      MyIntList correct = cons(2, empty);

      CHECK(result == correct);
    }

    SUBCASE("is hashable") {
      MyIntList l1 = cons(2, cons(1, empty));
      MyIntList l2 = cons(1, cons(2, empty));
      MyIntList l3 = cons(2, empty);
      MyIntList l4 = empty;

      auto get_hash = [](MyIntList const &p) -> std::size_t {
        return std::hash<MyIntList>{}(p);
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
      MyIntList l = cons(2, cons(1, empty));       
      std::string correct = "<MyIntList cons=<MyIntListCons head=2 tail=<MyIntList cons=<MyIntListCons head=1 tail=<MyIntList empty=<MyListEmpty>>>>>>";
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
