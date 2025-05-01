add_custom_target(copy-test-makefile ALL DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/example_function_file.txt)
add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/example_function_file.txt
                   COMMAND ${CMAKE_COMMAND} -E copy ${PROJECT_SOURCE_DIR}/original_example_function_file.txt
                                                    ${CMAKE_CURRENT_BINARY_DIR}/example_function_file.txt
                   DEPENDS ${PROJECT_SOURCE_DIR}/original_example_function_file.txt)

tp_add_test_executable(
  NAME
    test-env
  SRC_PATTERNS
    src/*.cc
  PRIVATE_INCLUDE
    src/
)
add_dependencies(test-env-tests copy-test-makefile)
