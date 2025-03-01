tp_add_library(
  NAME
    person
  SRC_PATTERNS
    src/*.cc
  PUBLIC_INCLUDE
    include/
  PRIVATE_INCLUDE
    src/
  DEPS
    fmt
)

add_subdirectory(test)
