tp_add_executable(
  NAME
    bin2
  SRC_PATTERNS
    src/*.cc
  DEPS
    lib1-lib
    lib2-lib
)
