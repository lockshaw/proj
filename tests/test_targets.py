from proj.targets import (
    BuildTarget,
    LibTarget,
    BinTarget,
)

def test_build_target_from_str():
    assert BuildTarget.from_str('lib:lib1') == LibTarget('lib1').build_target
    assert BuildTarget.from_str('bin:bin1') == BinTarget('bin1').build_target
    assert BuildTarget.from_str('test:lib1') == LibTarget('lib1').test_target.build_target
    assert BuildTarget.from_str('bench:lib1') == LibTarget('lib1').benchmark_target.build_target

def test_build_target_from_cmake_name():
    assert BuildTarget.from_cmake_name('lib1-lib') == LibTarget('lib1').build_target
    assert BuildTarget.from_cmake_name('bin1-bin') == BinTarget('bin1').build_target
    assert BuildTarget.from_cmake_name('lib1-tests') == LibTarget('lib1').test_target.build_target
    assert BuildTarget.from_cmake_name('lib1-benchmarks') == LibTarget('lib1').benchmark_target.build_target
