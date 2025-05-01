#include <doctest/doctest.h>
#include "test-env/test-env.h"
#include <cstdlib>
#include <fstream>

using namespace TestEnvProject;

TEST_SUITE(TP_TEST_SUITE) {
  TEST_CASE("example_function") {
    std::string filename = "example_function_file.txt";

    std::ifstream istrm(filename);
    REQUIRE(istrm.is_open());

    int value_in_file;
    istrm >> value_in_file;

    REQUIRE(value_in_file == 13);

    char const *should_fail = std::getenv("PROJ_TESTS_FAIL_TEST_ENV_EXAMPLE_FUNCTION");
    CHECK(should_fail == nullptr);
  }
}
