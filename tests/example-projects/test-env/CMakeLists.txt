cmake_minimum_required(VERSION 3.10)
project(test-env-project)

set(
  CMAKE_MODULE_PATH 
  ${CMAKE_MODULE_PATH} 
  ${CMAKE_CURRENT_LIST_DIR}/cmake 
)

include(doctestlib) # named doctestlib to avoid a name collision with doctest.cmake in rapidcheck
include(gbenchmark)
include(CTest)
include(tp-utils)

# TODO @lockshaw remove me
# https://discourse.nixos.org/t/get-clangd-to-find-standard-headers-in-nix-shell/11268/6
if(CMAKE_EXPORT_COMPILE_COMMANDS)
    set(CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES ${CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES})
endif()


add_subdirectory(lib)
