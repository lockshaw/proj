from proj.__main__ import (
    main_dtgen,
    main_cmake,
    main_test,
    MainDtgenArgs,
    MainCmakeArgs,
    MainTestArgs,
)
# import subprocess
from pathlib import Path

DIR = Path(__file__).absolute().parent

# def _compile_file(input_files: Sequence[Path], include_dir: Path, output_file: Path):
    # subprocess.check_call([
    #     'g++',
    #     *input_files,
    #     '-o',
    #     output_file,
    # ])

def _test_project(name: str):
    testdir = DIR / name

    dtgen_args = MainDtgenArgs(
        path=testdir,
        files=[],
    )
    main_dtgen(args=dtgen_args)
    # assert (testdir / 'include/person.hh').is_file()
    # assert (testdir / 'src/person.cc').is_file()

    cmake_args = MainCmakeArgs(
        path=testdir,
        force=True,
        trace=False,
    )
    main_cmake(args=cmake_args)

    test_args = MainTestArgs(
        path=testdir,
        verbose=False,
        jobs=1,
    )
    main_test(args=test_args)


def test_person():
    _test_project('person')

def test_wrapper():
    _test_project('wrapper')
