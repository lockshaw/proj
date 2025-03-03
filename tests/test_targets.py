from proj.targets import (
    BuildTarget,
    LibTarget,
    BinTarget,
    ConfiguredNames,
    RunTarget,
)

NAMES = ConfiguredNames(
    bin_names={'bin1'},
    lib_names={'lib1'},
)

def test_run_target_from_str():
    assert RunTarget.from_str('bin1') == BinTarget('bin1').run_target

    lib1_benchmarks = LibTarget('lib1').benchmark_target.run_target

    assert RunTarget.from_str('lib1:b') == lib1_benchmarks
    assert RunTarget.from_str('lib1:benchmark') == lib1_benchmarks
    assert RunTarget.from_str('lib1:benchmarks') == lib1_benchmarks

    lib1_tests = LibTarget('lib1').test_target.run_target

    assert RunTarget.from_str('lib1:t') == lib1_tests
    assert RunTarget.from_str('lib1:test') == lib1_tests
    assert RunTarget.from_str('lib1:tests') == lib1_tests

    lib1_benchmarks_case1 = LibTarget('lib1').benchmark_target.get_benchmark_case('case1').run_target

    assert RunTarget.from_str('lib1:b:case1') == lib1_benchmarks_case1
    assert RunTarget.from_str('lib1:benchmark:case1') == lib1_benchmarks_case1
    assert RunTarget.from_str('lib1:benchmarks:case1') == lib1_benchmarks_case1

    lib1_tests_case1 = LibTarget('lib1').test_target.get_test_case('case1').run_target

    assert RunTarget.from_str('lib1:t:case1') == lib1_tests_case1
    assert RunTarget.from_str('lib1:test:case1') == lib1_tests_case1
    assert RunTarget.from_str('lib1:tests:case1') == lib1_tests_case1

def test_build_target_from_str():
    assert BuildTarget.from_str(NAMES, 'lib1') == LibTarget('lib1').build_target
    assert BuildTarget.from_str(NAMES, 'bin1') == BinTarget('bin1').build_target

    lib1_tests = LibTarget('lib1').test_target.build_target
    lib1_benchmarks = LibTarget('lib1').benchmark_target.build_target

    assert BuildTarget.from_str(NAMES, 'lib1:t') == lib1_tests
    assert BuildTarget.from_str(NAMES, 'lib1:test') == lib1_tests
    assert BuildTarget.from_str(NAMES, 'lib1:tests') == lib1_tests

    assert BuildTarget.from_str(NAMES, 'lib1:b') == lib1_benchmarks
    assert BuildTarget.from_str(NAMES, 'lib1:benchmark') == lib1_benchmarks
    assert BuildTarget.from_str(NAMES, 'lib1:benchmarks') == lib1_benchmarks

def test_build_target_from_cmake_name():
    assert BuildTarget.from_cmake_name(NAMES, 'lib1') == LibTarget('lib1').build_target
    assert BuildTarget.from_cmake_name(NAMES, 'bin1') == BinTarget('bin1').build_target
    assert BuildTarget.from_cmake_name(NAMES, 'lib1-tests') == LibTarget('lib1').test_target.build_target
    assert BuildTarget.from_cmake_name(NAMES, 'lib1-benchmarks') == LibTarget('lib1').benchmark_target.build_target
