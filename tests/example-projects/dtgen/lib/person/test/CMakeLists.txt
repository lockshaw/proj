tp_add_test_executable(
  NAME
    person
  SRC_PATTERNS
    src/*.cc
  PRIVATE_INCLUDE
    src/
  DEPS
    rapidcheck
)
