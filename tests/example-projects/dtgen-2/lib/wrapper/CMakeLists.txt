tp_add_library(
  NAME
    wrapper
  SRC_PATTERNS
    src/*.cc
  PUBLIC_INCLUDE
    include/
  PRIVATE_INCLUDE
    src/
  DEPS
    rapidcheck
    fmt
)

add_subdirectory(test)
