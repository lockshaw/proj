tp_add_library(
  NAME
    lib1
  SRC_PATTERNS
    src/*.cc
  PUBLIC_INCLUDE
    include/
  PRIVATE_INCLUDE
    src/
)

add_subdirectory(test)
add_subdirectory(benchmark)
