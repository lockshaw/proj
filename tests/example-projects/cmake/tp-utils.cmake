macro(tp_parse_args)
  set(flagArgs)
  set(standardArgs PREFIX)
  set(variadicArgs FLAGS ARGS VARIADIC_ARGS PARSE)
  cmake_parse_arguments(TP_PARSE_ARGS "${flagArgs}" "${standardArgs}" "${variadicArgs}" ${ARGN})

  cmake_parse_arguments(${TP_PARSE_ARGS_PREFIX} "${TP_PARSE_ARGS_FLAGS}" "${TP_PARSE_ARGS_ARGS}" "${TP_PARSE_ARGS_VARIADIC_ARGS}" ${TP_PARSE_ARGS_PARSE})
endmacro()

function(define_tp_vars target)
  if (TP_GPU_BACKEND STREQUAL "cuda")
    target_compile_definitions(${target} PRIVATE TP_USE_CUDA)
  elseif (TP_GPU_BACKEND STREQUAL "hip_cuda")
    target_compile_definitions(${target} PRIVATE TP_USE_HIP_CUDA)
  elseif (TP_GPU_BACKEND STREQUAL "hip_rocm")
    target_compile_definitions(${target} PRIVATE TP_USE_HIP_ROCM)
  endif()
endfunction()

function(tp_set_cxx_properties target)
  set_target_properties(${target}
    PROPERTIES
      CXX_STANDARD 17
      CXX_STANDARD_REQUIRED YES
      CXX_EXTENSIONS NO
  )
  target_compile_options(${target}
    PUBLIC 
    $<$<COMPILE_LANGUAGE:CXX>:> 
    "-ffile-prefix-map=${CMAKE_SOURCE_DIR}=." 
    "-fsanitize=undefined" 
    "-fno-sanitize-recover=all"
    # add C++ compile flags here
  )
  target_link_options(${target}
    PUBLIC 
    $<$<COMPILE_LANGUAGE:CXX>:> 
    "-fsanitize=undefined" 
    "-fno-sanitize-recover=all"
  )
endfunction()

function(tp_add_library)
  tp_parse_args(
    PREFIX 
      TP_LIBRARY
    ARGS
      NAME
    VARIADIC_ARGS
      SRC_PATTERNS
      PUBLIC_INCLUDE
      PRIVATE_INCLUDE
      DEPS
      PRIVATE_DEPS
    PARSE
      ${ARGN}
  )

  set(FULL_TP_LIBRARY_NAME "${TP_LIBRARY_NAME}")
  
  project(${FULL_TP_LIBRARY_NAME})
  file(GLOB_RECURSE SRC
       CONFIGURE_DEPENDS 
       LIST_DIRECTORIES False
       ${TP_LIBRARY_SRC_PATTERNS})

  add_library(
    ${FULL_TP_LIBRARY_NAME}
    SHARED
    ${SRC})

  target_include_directories(
    ${FULL_TP_LIBRARY_NAME}
    PUBLIC
      ${TP_LIBRARY_PUBLIC_INCLUDE}
    PRIVATE
      ${TP_LIBRARY_PRIVATE_INCLUDE})

  target_link_libraries(
    ${FULL_TP_LIBRARY_NAME}
    PUBLIC
      ${TP_LIBRARY_DEPS}
    PRIVATE
      ${TP_LIBRARY_PRIVATE_DEPS}
  )
  define_tp_vars(${FULL_TP_LIBRARY_NAME})
  tp_set_cxx_properties(${FULL_TP_LIBRARY_NAME})
endfunction()

function(tp_add_test_executable)
  tp_parse_args(
    PREFIX 
      TP_TEST_EXEC
    ARGS
      NAME
    VARIADIC_ARGS
      SRC_PATTERNS
      PRIVATE_INCLUDE
      DEPS
    PARSE
      ${ARGN}
      rapidcheck
      doctest
  )

  set(FULL_TP_TEST_EXEC_NAME "${TP_TEST_EXEC_NAME}-tests")

  project(${FULL_TP_TEST_EXEC_NAME})
  file(GLOB_RECURSE SRC
       CONFIGURE_DEPENDS
       LIST_DIRECTORIES False
       ${TP_TEST_EXEC_SRC_PATTERNS})

  add_executable(
    ${FULL_TP_TEST_EXEC_NAME}
    ${SRC})

  target_link_libraries(
    ${FULL_TP_TEST_EXEC_NAME}
    ${TP_TEST_EXEC_DEPS}
    ${TP_TEST_EXEC_NAME}
    doctest
    )

  target_include_directories(
    ${FULL_TP_TEST_EXEC_NAME}
    PRIVATE
    ${TP_TEST_EXEC_PRIVATE_INCLUDE})

  target_compile_definitions(${FULL_TP_TEST_EXEC_NAME} PRIVATE TP_TEST_SUITE="cpu-${FULL_TP_TEST_EXEC_NAME}" TP_CUDA_TEST_SUITE="cuda-${FULL_TP_TEST_EXEC_NAME}")

  define_tp_vars(${FULL_TP_TEST_EXEC_NAME})
  tp_set_cxx_properties(${FULL_TP_TEST_EXEC_NAME})
  doctest_discover_tests(${FULL_TP_TEST_EXEC_NAME} ADD_LABELS 1)
endfunction()

function(tp_add_benchmark_executable)
  tp_parse_args(
    PREFIX 
      TP_BENCHMARK_EXEC
    ARGS
      NAME
    VARIADIC_ARGS
      SRC_PATTERNS
      PRIVATE_INCLUDE
      DEPS
    PARSE
      ${ARGN}
  )

  set(FULL_TP_BENCHMARK_EXEC_NAME "${TP_BENCHMARK_EXEC_NAME}-benchmarks")

  project(${FULL_TP_BENCHMARK_EXEC_NAME})
  file(GLOB_RECURSE SRC
       CONFIGURE_DEPENDS
       LIST_DIRECTORIES False
       ${TP_BENCHMARK_EXEC_SRC_PATTERNS})

  add_executable(
    ${FULL_TP_BENCHMARK_EXEC_NAME}
    ${SRC})

  target_link_libraries(
    ${FULL_TP_BENCHMARK_EXEC_NAME}
    ${TP_BENCHMARK_EXEC_DEPS}
    ${TP_BENCHMARK_EXEC_NAME}
    gbenchmark
    gbenchmark-main)

  define_tp_vars(${FULL_TP_BENCHMARK_EXEC_NAME})
  tp_set_cxx_properties(${FULL_TP_BENCHMARK_EXEC_NAME})
endfunction()

function(tp_add_executable)
  tp_parse_args(
    PREFIX 
      TP_EXEC
    ARGS
      NAME
    VARIADIC_ARGS
      SRC_PATTERNS
      PRIVATE_INCLUDE
      DEPS
    PARSE
      ${ARGN}
  )

  set(FULL_TP_EXEC_NAME "${TP_EXEC_NAME}")

  project(${FULL_TP_EXEC_NAME})
  file(GLOB_RECURSE SRC
       CONFIGURE_DEPENDS
       LIST_DIRECTORIES False
       ${TP_EXEC_SRC_PATTERNS})

  add_executable(
    ${FULL_TP_EXEC_NAME}
    ${SRC})

  target_include_directories(
    ${FULL_TP_EXEC_NAME}
    PRIVATE
    ${TP_EXEC_PRIVATE_INCLUDE})

  target_link_libraries(
    ${FULL_TP_EXEC_NAME}
    ${TP_EXEC_DEPS})

  define_tp_vars(${FULL_TP_EXEC_NAME})
  tp_set_cxx_properties(${FULL_TP_EXEC_NAME})
endfunction()
