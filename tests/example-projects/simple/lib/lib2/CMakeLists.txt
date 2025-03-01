tp_add_library(
  NAME
    lib2
  SRC_PATTERNS
    src/*.cc
  PUBLIC_INCLUDE
    include/
  PRIVATE_INCLUDE
    src/
  DEPS
    lib1-lib
)

add_subdirectory(test)
