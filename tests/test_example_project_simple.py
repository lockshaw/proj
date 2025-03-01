import pytest
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Iterator,
    Iterable,
)
from proj.__main__ import (
    main,
)
from proj.targets import (
    BuildTarget,
    LibTarget,
    BinTarget,
    TestSuiteTarget as _TestSuiteTarget,
    BenchmarkSuiteTarget,
)
from proj.config_file import get_config
from proj.cmake import (
    get_target_names_list,
    get_targets_list,
    BuildMode,
    get_build_dir,
)
from proj.build import (
    build_targets,
)
from proj.testing import (
    list_tests_in_targets,
)
from .project_utils import (
    project_instance as _project_instance,
    cmade_project_instance as _cmade_project_instance,
    MAX_VERBOSITY,
)

def project_instance():
    return _project_instance('simple')

def cmade_project_instance():
    return _cmade_project_instance('simple')

def test_main_cmake() -> None:
    with project_instance() as d:
        main([
            'cmake',
            '--path',
            str(d),
        ])

        config = get_config(d)

        assert config.debug_build_dir.is_dir()
        assert config.release_build_dir.is_dir()
        assert config.coverage_build_dir.is_dir()
        assert (config.base / 'compile_commands.json').is_file()


def test_get_config() -> None:
    with project_instance() as d:
        config = get_config(d)

        assert config.base == d

def test_get_cmake_target_names_list() -> None:
    with cmade_project_instance() as d:
        config = get_config(d)

        required = [
            'lib1-lib',
            'lib2-lib',
            'bin1-bin',
            'bin2-bin',
            'lib1-tests',
            'lib2-tests',
            'lib1-benchmarks',
        ]
        required_not = [
            'lib2-benchmarks',
        ]


        def check_target_list(target_list):
            for target in required:
                assert target in target_list
            for target in required_not:
                assert target not in target_list

        debug_target_list = list(get_target_names_list(config.debug_build_dir))
        check_target_list(debug_target_list)

        release_target_list = list(get_target_names_list(config.release_build_dir))
        check_target_list(release_target_list)

        coverage_target_list = list(get_target_names_list(config.coverage_build_dir))
        check_target_list(coverage_target_list)

def test_get_cmake_targets_list() -> None:
    with cmade_project_instance() as d:
        config = get_config(d)

        required = [
            LibTarget('lib1').build_target,
            LibTarget('lib2').build_target,
            BinTarget('bin1').build_target,
            BinTarget('bin2').build_target,
            _TestSuiteTarget('lib1').build_target,
            _TestSuiteTarget('lib2').build_target,
            BenchmarkSuiteTarget('lib1').build_target,
        ]
        required_not = [
            BenchmarkSuiteTarget('lib2').build_target,
        ]

        def check_target_list(target_list):
            for target in required:
                assert target in target_list
            for target in required_not:
                assert target not in target_list

        debug_target_list = list(get_targets_list(config.debug_build_dir))
        check_target_list(debug_target_list)

        release_target_list = list(get_targets_list(config.release_build_dir))
        check_target_list(release_target_list)

        coverage_target_list = list(get_targets_list(config.coverage_build_dir))
        check_target_list(coverage_target_list)

def test_debug_build() -> None:
    with cmade_project_instance() as d:
        config = get_config(d)

        targets = [
            BuildTarget.from_str('lib:lib1'),
            BuildTarget.from_str('bin:bin2'),
            BuildTarget.from_str('test:lib2'),
            BuildTarget.from_str('bench:lib1'),
        ]

        main([
            'build',
            '--path',
            str(d),
            '-j1',
            'lib:lib1',
            'bin:bin2',
            'test:lib2',
            'bench:lib1',
        ])

        for t in targets:
            assert (config.debug_build_dir / t.artifact_path).is_file()
            assert not (config.release_build_dir / t.artifact_path).exists()
            assert not (config.coverage_build_dir / t.artifact_path).exists()

@contextmanager
def built_project_instance(targets: Iterable[BuildTarget], build_mode: BuildMode = BuildMode.DEBUG) -> Iterator[Path]:
    with cmade_project_instance() as d:
        config = get_config(d)

        build_targets(
            config=config,
            targets=list(targets),
            dtgen_skip=False,
            jobs=1,
            verbosity=MAX_VERBOSITY,
            cwd=get_build_dir(config, build_mode),
        )
        yield d

def test_list_tests_in_target() -> None:
    lib2_target = _TestSuiteTarget('lib2')
    with built_project_instance([
        lib2_target.build_target,
    ]) as d:
        config = get_config(d)

        found = set(list_tests_in_targets([lib2_target], config.debug_build_dir))
        correct = {
            lib2_target.get_test_case('call_lib2'),
            lib2_target.get_test_case('other_lib2'),
        }

        assert found == correct

def test_test_all() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'test',
            '--path',
            str(d),
            '-j1',
        ])

def test_test_test_suite() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'test',
            '--path',
            str(d),
            '-j1',
            'lib2',
        ])

def test_test_test_case():
    with cmade_project_instance() as d:
        assert 0 == main([
            'test',
            '--path',
            str(d),
            '-j1',
            'lib2:call_lib2',
        ])

def test_run_bin() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'run',
            '--path',
            str(d),
            '-j1',
            'bin1',
        ])

def test_run_test_suite() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'run',
            '--path',
            str(d),
            '-j1',
            'lib1:tests',
        ])

def test_run_test_case() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'run',
            '--path',
            str(d),
            '-j1',
            'lib1:tests:call_lib1',
        ])

def test_run_benchmark_suite() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'run',
            '--path',
            str(d),
            '-j1',
            'lib1:benchmarks',
        ])

def test_benchmark_case() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'run',
            '--path',
            str(d),
            '-j1',
            'lib1:benchmarks:example_benchmark/75/16'
        ])

def test_benchmark_suite() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'benchmark',
            '--path',
            str(d),
            '-j1',
            'lib1',
        ])

def test_profile_bin() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'profile',
            '--path',
            str(d),
            '-j1',
            'bin1',
        ])

def test_profile_test_suite() -> None:
    with cmade_project_instance() as d:
        assert 0  == main([
            'profile',
            '--path',
            str(d),
            '-j1',
            'lib1:tests',
        ])

def test_profile_test_case() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'profile',
            '--path',
            str(d),
            '-j1',
            'lib1:tests:call_lib1'
        ])

def test_profile_benchmark_suite() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'profile',
            '--path',
            str(d),
            '-j1',
            'lib1:benchmarks'
        ])

def test_profile_benchmark_case() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'profile',
            '--path',
            str(d),
            '-j1',
            'lib1:benchmarks:example_benchmark/75/32'
        ])

@pytest.mark.slow
def test_lint() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'lint',
            '--path',
            str(d),
        ])
