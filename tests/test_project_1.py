from contextlib import contextmanager
from tempfile import TemporaryDirectory
import shutil
from pathlib import Path
from typing import (
    Iterator,
    Iterable,
    Tuple,
)
from proj.__main__ import (
    MainCmakeArgs,
    main_cmake,
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
from functools import cache
import subprocess
import os

TEST_PROJECT_1_DIR = Path(__file__).parent / 'test-project-1'
MAX_VERBOSITY = 100

@cache
def _test_dir() -> TemporaryDirectory:
    td = TemporaryDirectory()
    return td

@cache
def _blank_rev() -> (Path, str):
    d = Path(_test_dir().name)
    subprocess.check_call(['git', 'init'], cwd=d, env=os.environ)
    with (d / '.placeholder').open('w') as _:
        pass
    return make_checkpoint(d)

@cache
def _project_copied_rev() -> Tuple[Path, str]:
    (d, blank_rev) = _blank_rev()
    with git_checkout(d, blank_rev):
        dst = Path(d) / 'test-project-1'
        shutil.copytree(src=TEST_PROJECT_1_DIR, dst=dst)
        copied_rev = make_checkpoint(d)
    return (d, copied_rev)

@cache
def _project_cmade_rev() -> Tuple[Path, str]:
    (d, cmade_rev) = _project_copied_rev()
    with git_checkout(d, cmade_rev):
        cmake_args = MainCmakeArgs(
            path=d,
            fast=False,
            trace=False,
            dtgen_skip=False,
            verbosity=MAX_VERBOSITY,
        )
        main_cmake(cmake_args)
        cmade_rev = make_checkpoint(d)
    return (d, cmade_rev)

def make_checkpoint(d: Path) -> str:
    subprocess.check_call(['git', 'add', str(d)], cwd=d, env=os.environ)
    subprocess.check_call(['git', 'commit', '-m', 'commit'], cwd=d, env=os.environ)
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=d, env=os.environ, text=True).strip()

@contextmanager
def git_checkout(d: Path, rev: str) -> Iterator[None]:
    subprocess.check_call(['git', 'reset', '--hard', rev], cwd=d, env=os.environ)
    subprocess.check_call(['git', 'clean', '-xdf'], cwd=d, env=os.environ)
    yield

@contextmanager
def project_instance() -> Iterator[Path]:
    (d, rev) = _project_copied_rev()
    with git_checkout(d, rev):
        yield (d / 'test-project-1')

@contextmanager
def cmade_project_instance() -> Iterator[Path]:
    (d, rev) = _project_cmade_rev()
    with git_checkout(d, rev):
        yield d

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

def test_build_and_run_tests() -> None:
    with cmade_project_instance() as d:
        assert 0 == main([
            'test',
            '--path',
            str(d),
            '-j1',
            'lib2',
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
    ...
