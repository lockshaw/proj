import pytest
from proj.__main__ import (
    main_cmake,
    main_test,
    main_lint,
    main_build,
    MainCmakeArgs,
    MainBuildArgs,
    MainTestArgs,
    MainLintArgs,
)
# import subprocess
from pathlib import Path
from proj.config_file import (
    find_config_root, 
    get_source_path,
    get_config,
    get_possible_spec_paths,
)
from proj.dtgen.find_outdated import (
    find_outdated,
)
import proj.lint as lint
import logging

DIR = Path(__file__).absolute().parent

def _test_project(name: str):
    testdir = DIR / name

    cmake_args = MainCmakeArgs(
        path=testdir,
        fast=False,
        trace=False,
        dtgen_skip=False,
        verbosity=logging.WARNING,
    )
    main_cmake(args=cmake_args)

    build_args = MainBuildArgs(
        path=testdir,
        verbosity=logging.WARNING,
        jobs=1,
        dtgen_skip=False,
        targets=[],
    )
    main_build(args=build_args)

    test_args = MainTestArgs(
        path=testdir,
        coverage=False,
        verbosity=logging.WARNING,
        jobs=1,
        dtgen_force=True, # otherwise dtgen files won't get regenerated on changes to 
                          # the proj implementation code being tested
        dtgen_skip=False,
        browser=False,
        skip_gpu_tests=True,
        skip_build_gpu_tests=False,
        skip_cpu_tests=False,
        skip_build_cpu_tests=False,
        targets=[],
    )
    main_test(args=test_args)


def test_person():
    _test_project('person')

def test_wrapper():
    _test_project('wrapper')

def test_find_config_root():
    testdir = DIR / 'person'

    assert find_config_root(testdir) == testdir

def test_get_source_path():
    testdir = DIR / 'person'

    correct = testdir / 'src' / 'color.dtg.cc'
    assert get_source_path(testdir / 'include' / 'color.dtg.hh') == correct

def test_get_possible_spec_paths():
    testdir = DIR / 'person'

    found = set(get_possible_spec_paths(testdir / 'include' / 'color.dtg.hh'))
    correct = set([
        testdir / 'include' / 'color.struct.toml',
        testdir / 'include' / 'color.enum.toml',
        testdir / 'include' / 'color.variant.toml',
        testdir / 'src' / 'color.struct.toml',
        testdir / 'src' / 'color.enum.toml',
        testdir / 'src' / 'color.variant.toml',
    ])
    assert found == correct


def test_find_outdated():
    testdir = DIR / 'person'

    config = get_config(testdir)
    
    with (testdir / 'include' / 'out_of_date.dtg.hh').open('w') as _:
        pass

    with (testdir / 'src' / 'out_of_date2.dtg.cc').open('w') as _:
        pass

    found = set(find_outdated(testdir, config))
    correct = set([
        testdir / 'include' / 'out_of_date.dtg.hh',
        testdir / 'src' / 'out_of_date2.dtg.cc',
    ])
    assert found == correct

def test_lint_find_files() -> None:
    pass
    # testdir = DIR / 'person'
    # config = get_config(testdir)
    #
    # found = set(lint.find_files(
    #     root=testdir,
    #     config=config,
    # ))
    # correct = set([
    #     *(testdir / 'src').rglob('*.cc'),
    #     *(testdir / 'include').rglob('*.hh'),
    # ])
    #
    # assert found == correct

@pytest.mark.slow
def test_lint() -> None:
    testdir = DIR / 'person'

    cmake_args = MainCmakeArgs(
        path=testdir,
        fast=False,
        trace=False,
        dtgen_skip=False,
        verbosity=logging.WARNING,
    )
    main_cmake(args=cmake_args)

    lint_args = MainLintArgs(
        path=testdir,
        files=[],
        profile_checks=False,
        verbosity=logging.WARNING,
    )
    main_lint(args=lint_args)
