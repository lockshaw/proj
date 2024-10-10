#include <doctest/doctest.h>
#include "variant_holding_optional.dtg.hh"

using namespace ::FlexFlow;

TEST_SUITE(FF_TEST_SUITE) {
  TEST_CASE("VariantHoldingOptional") {
    SUBCASE("brace construction") {
      SUBCASE("num") {
        SUBCASE("num has value") {
          VariantHoldingOptional x = VariantHoldingOptional{std::optional<int>{5}};

          CHECK(x.is_num());
          CHECK(x.require_num() == std::optional<int>{5});
        }

        SUBCASE("num is nullopt") {
          VariantHoldingOptional x = VariantHoldingOptional{std::optional<int>{std::nullopt}};

          CHECK(x.is_num());
          CHECK_FALSE(x.require_num().has_value());
        }
      }

      SUBCASE("other") {
        VariantHoldingOptional x = VariantHoldingOptional{5};

        CHECK(x.is_other());
        CHECK(x.require_other() == 5);
      }

      SUBCASE("str") {
        SUBCASE("str has value") {
          VariantHoldingOptional x = VariantHoldingOptional{std::optional<std::string>{"abc"}};

          CHECK(x.is_str());
          CHECK(x.require_str() == std::optional<std::string>{"abc"});
        }

        SUBCASE("str is nullopt") {
          VariantHoldingOptional x = VariantHoldingOptional{std::optional<std::string>{std::nullopt}};

          CHECK(x.is_str());
          CHECK_FALSE(x.require_str().has_value());
        }
      }
    }

    SUBCASE("try_require methods") {
      VariantHoldingOptional x = VariantHoldingOptional{std::optional<int>{std::nullopt}};

      SUBCASE("try_require_num") {
        CHECK(x.try_require_num().has_value());
        CHECK(x.try_require_num().value() == std::nullopt);
      }

      SUBCASE("other") {
        CHECK_FALSE(x.try_require_other().has_value());
        CHECK(x.try_require_other() == std::nullopt);
      }

      SUBCASE("str") {
        CHECK_FALSE(x.try_require_str().has_value());
        CHECK(x.try_require_other() == std::nullopt);
      }
    }
  }
}
