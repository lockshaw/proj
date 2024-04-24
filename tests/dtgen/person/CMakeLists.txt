find_package(doctest REQUIRED)
include(doctest) # import doctest_discover_tests

find_package(rapidcheck REQUIRED)
find_package(fmt REQUIRED)

set(target "person-tests")

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
  doctest::doctest
  rapidcheck
  fmt::fmt
  )

set_target_properties(${target}
  PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED YES
    CXX_EXTENSIONS NO
)


include(CTest)
target_compile_definitions(${target} PRIVATE FF_TEST_SUITE="${target}")
doctest_discover_tests(${target} ADD_LABELS 1)

# TODO @lockshaw remove me
# https://discourse.nixos.org/t/get-clangd-to-find-standard-headers-in-nix-shell/11268/6
if(CMAKE_EXPORT_COMPILE_COMMANDS)
    set(CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES ${CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES})
endif()
