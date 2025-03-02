from proj.targets import (
    BuildTarget,
    LibTarget,
    BinTarget,
    ConfiguredNames,
)

NAMES = ConfiguredNames(
    bin_names={'bin1'},
    lib_names={'lib1'},
)

def test_build_target_from_str():
    assert BuildTarget.from_str('lib:lib1') == LibTarget('lib1').build_target
    assert BuildTarget.from_str('bin:bin1') == BinTarget('bin1').build_target
    assert BuildTarget.from_str('test:lib1') == LibTarget('lib1').test_target.build_target
    assert BuildTarget.from_str('bench:lib1') == LibTarget('lib1').benchmark_target.build_target

def test_build_target_from_cmake_name():
    assert BuildTarget.from_cmake_name(NAMES, 'lib1') == LibTarget('lib1').build_target
    assert BuildTarget.from_cmake_name(NAMES, 'bin1') == BinTarget('bin1').build_target
    assert BuildTarget.from_cmake_name(NAMES, 'lib1-tests') == LibTarget('lib1').test_target.build_target
    assert BuildTarget.from_cmake_name(NAMES, 'lib1-benchmarks') == LibTarget('lib1').benchmark_target.build_target
