from pathlib import Path
from typing import (
    Any,
    Sequence,
)
import subprocess
import os
import shutil
import multiprocessing
import shlex
import sys
from .config_file import (
    get_config,
    get_config_root,
)
from .dtgen import run_dtgen
from .format import run_formatter
from .lint import run_linter
from .dtgen.find_outdated import find_outdated
import proj.fix_compile_commands as fix_compile_commands
import logging
from dataclasses import dataclass
from .verbosity import (
    add_verbosity_args,
    calculate_log_level,
)

_l = logging.getLogger(name='proj')

DIR = Path(__file__).resolve().parent


def main_root(args: Any) -> None:
    config_root = get_config_root(args.path)
    print(config_root)


def subprocess_check_call(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(command, **kwargs)


def subprocess_run(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(command, **kwargs)

def cmake(cmake_args, config, is_coverage):
    if is_coverage:
        cwd = config.cov_dir
    else:
        cwd = config.build_dir
    subprocess_check_call(
        [
            "cmake",
            *cmake_args,
            "../..",
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
        shell=config.cmake_require_shell,
    )

@dataclass(frozen=True)
class MainCmakeArgs:
    path: Path
    force: bool
    trace: bool

def main_cmake(args: MainCmakeArgs) -> None:
    main_dtgen(args=MainDtgenArgs(
        path=args.path,
        files=[],
        delete_outdated=True,
        force=False,
    ))

    config = get_config(args.path)
    if args.force:
        if config.build_dir.exists():
            shutil.rmtree(config.build_dir)
        if config.cov_dir.exists():
            shutil.rmtree(config.cov_dir)
    config.build_dir.mkdir(exist_ok=True, parents=True)
    config.cov_dir.mkdir(exist_ok=True, parents=True)
    cmake_args = [f"-D{k}={v}" for k, v in config.cmake_flags.items()]
    cmake_args += shlex.split(os.environ.get("CMAKE_FLAGS", ""))
    if args.trace:
        cmake_args += ["--trace", "--trace-expand", "--trace-redirect=trace.log"]
    cmake(cmake_args, config, False)
    COMPILE_COMMANDS_FNAME = "compile_commands.json"
    if config.fix_compile_commands:
        fix_compile_commands.fix_file(
            compile_commands=config.build_dir / COMPILE_COMMANDS_FNAME,
            base_dir=config.base,
        )

    with (config.base / COMPILE_COMMANDS_FNAME).open("w") as f:
        subprocess_check_call(
            [
                "compdb",
                "-p",
                ".",
                "list",
            ],
            stdout=f,
            cwd=config.build_dir,
            env=os.environ,
        )
        
    cmake(cmake_args + ["-DFF_USE_CODE_COVERAGE=ON"], config, True)


@dataclass(frozen=True)
class MainBuildArgs:
    path: Path
    verbosity: int
    jobs: int

def main_build(args: MainBuildArgs) -> None:
    main_dtgen(args=MainDtgenArgs(
        path=args.path,
        files=[],
        delete_outdated=True,
        force=False,
    ))

    config = get_config(args.path)
    subprocess_check_call(
        [
            "make",
            "-j",
            str(args.jobs),
            *config.build_targets,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": str(DIR.parent.parent.parent),
            **({"VERBOSE": "1"} if args.verbosity <= logging.DEBUG else {}),
        },
        stderr=sys.stdout,
        cwd=config.build_dir,
    )


@dataclass(frozen=True)
class MainTestArgs:
    path: Path
    verbosity: int
    jobs: int

def main_test(args: MainTestArgs) -> None:
    main_dtgen(args=MainDtgenArgs(
        path=args.path,
        files=[],
        delete_outdated=True,
        force=False,
    ))

    config = get_config(args.path)
    if args.coverage:
        cwd = config.cov_dir
    else:
        cwd = config.build_dir
    
    subprocess_check_call(
        [
            "make",
            "-j",
            str(args.jobs),
            *config.test_targets,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": str(DIR.parent.parent.parent),
            **({"VERBOSE": "1"} if args.verbosity <= logging.DEBUG else {}),
        },
        stderr=sys.stdout,
        cwd=cwd,
    )
    target_regex = "^" + "|".join(config.test_targets) + "$"
    subprocess_run(
        [
            "ctest",
            "--progress",
            "--output-on-failure",
            "-L",
            target_regex,
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
    )
    
    if args.coverage:
        subprocess_run(
            [
                "lcov",
                "--capture",
                "--directory",
                ".",
                "--output-file",
                "main_coverage.info",
            ],
            stderr=sys.stdout,
            cwd=cwd,
            env=os.environ,
        )
        
        subprocess_run(
            [
                "lcov", 
                "--extract",
                "main_coverage.info",
                f"{config.base}/lib/*",
                "--output-file",
                "main_coverage.info",
            ],
            stderr=sys.stdout,
            cwd=cwd,
            env=os.environ,
        )
        if args.browser:
            print("opening coverage info in browser")
            subprocess_run(
                [
                    "genhtml",
                    "main_coverage.info",
                    "--output-directory",
                    "code_coverage",
                ],
                stderr=sys.stdout,
                cwd=config.build_dir,
                env=os.environ,
            )

            # run xdg-open to open the browser
            # not able to test it now as I am running on remote linux
            subprocess_run(
                [
                    "xdg-open",
                    "code_coverage/index.html",
                ],
                stderr=sys.stdout,
                cwd=config.cov_dir,
                env=os.environ,
            )
        else:
            subprocess_run(
                [
                    "lcov",
                    "--list",
                    "main_coverage.info",
                ],
                stderr=sys.stdout,
                cwd=config.cov_dir,
                env=os.environ,
            )
    


@dataclass(frozen=True)
class MainLintArgs:
    path: Path
    files: Sequence[Path]
    profile_checks: bool

def main_lint(args: MainLintArgs) -> None:
    root = get_config_root(args.path)
    config = get_config(args.path)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_linter(root, config, files, profile_checks=args.profile_checks)

def main_format(args: Any) -> None:
    root = get_config_root(args.path)
    config = get_config(args.path)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_formatter(root, config, files)

@dataclass(frozen=True)
class MainDtgenArgs:
    path: Path
    files: Sequence[Path]
    delete_outdated: bool
    force: bool

def main_dtgen(args: MainDtgenArgs) -> None:
    root = get_config_root(args.path)
    config = get_config(args.path)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_dtgen(
        root=root,
        config=config,
        files=files,
        force=args.force,
    )
    if args.delete_outdated:
        for outdated in find_outdated(root, config):
            _l.info(f'Removing out-of-date file at {outdated}')
            outdated.unlink()
    else:
        for outdated in find_outdated(root, config):
            _l.warning(f'Possible out-of-date file at {outdated}')


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    root_p = subparsers.add_parser("root")
    root_p.set_defaults(func=main_root)
    root_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    add_verbosity_args(root_p)

    test_p = subparsers.add_parser("test")
    test_p.set_defaults(func=main_test)
    test_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    # test_p.add_argument("--verbose", "-v", action="store_true")
    test_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    test_p.add_argument("--coverage", "-c", action="store_true")   
    add_verbosity_args(test_p)

    test_p.add_argument(
        "--browser", "-b", action="store_true", help="open coverage info in browser"
    )

    build_p = subparsers.add_parser("build")
    build_p.set_defaults(func=main_build)
    build_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    # build_p.add_argument("--verbose", "-v", action="store_true")
    build_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    add_verbosity_args(build_p)

    cmake_p = subparsers.add_parser("cmake")
    cmake_p.set_defaults(func=main_cmake)
    cmake_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    cmake_p.add_argument("--force", "-f", action="store_true")
    cmake_p.add_argument("--trace", action="store_true")
    add_verbosity_args(cmake_p)

    dtgen_p = subparsers.add_parser('dtgen')
    dtgen_p.set_defaults(func=main_dtgen)
    dtgen_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    dtgen_p.add_argument('--force', action='store_true', help='Disable incremental toml->c++ generation')
    dtgen_p.add_argument('--delete-outdated', action='store_true')
    dtgen_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(dtgen_p)

    format_p = subparsers.add_parser('format')
    format_p.set_defaults(func=main_format)
    format_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    format_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(format_p)

    lint_p = subparsers.add_parser('lint')
    lint_p.set_defaults(func=main_lint)
    lint_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    lint_p.add_argument('--profile-checks', action='store_true')
    lint_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(lint_p)

    args = p.parse_args()

    logging.basicConfig(
        level=calculate_log_level(args),
    )

    if hasattr(args, "func") and args.func is not None:
        args.func(args)
    else:
        p.print_help()
        exit(1)


if __name__ == "__main__":
    main()
