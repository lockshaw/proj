tp_add_library(
  NAME
    test-env
  SRC_PATTERNS
    src/*.cc
  PUBLIC_INCLUDE
    include/
  PRIVATE_INCLUDE
    src/
)

add_subdirectory(test)
