find_package(doctest REQUIRED)
include(doctest) # import doctest_discover_tests

set(target "wrapper-tests")

project(${target})

file(GLOB_RECURSE SRC
     CONFIGURE_DEPENDS 
     LIST_DIRECTORIES False
     src/*.cc
     test/*.cc)

add_executable(
  ${target}
  ${SRC})

target_include_directories(
  ${target}
  PUBLIC
  include)

target_link_libraries(
  ${target}
  doctest::doctest)

set_target_properties(${target}
  PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED YES
    CXX_EXTENSIONS NO
)

target_compile_definitions(${target} PRIVATE FF_TEST_SUITE="${target}")
doctest_discover_tests(${target} ADD_LABELS 1)
