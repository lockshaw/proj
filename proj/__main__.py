from pathlib import Path
from typing import Any
import subprocess
import os
import shutil
import multiprocessing
import shlex
import sys
import proj.lockshaw_config as lockshaw
import proj.fix_compile_commands as fix_compile_commands

DIR = Path(__file__).resolve().parent


def main_root(args: Any) -> None:
    config_root = lockshaw.find_config_root(args.path)
    if config_root is not None:
        print(config_root)
    else:
        print("ERROR: Could not find config root", file=sys.stderr)
        print("Exiting unsuccessfully...", file=sys.stderr)
        exit(1)


def subprocess_check_call(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        print(f"+++ $ {pretty_cmd}", file=sys.stderr)
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        print(f"+++ $ {pretty_cmd}", file=sys.stderr)
        subprocess.check_call(command, **kwargs)


def subprocess_run(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        print(f"+++ $ {pretty_cmd}", file=sys.stderr)
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        print(f"+++ $ {pretty_cmd}", file=sys.stderr)
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
            "..",
        ],
        stderr=sys.stdout,
        cwd=cwd,
        env=os.environ,
        shell=config.cmake_require_shell,
    )

def main_cmake(args: Any) -> None:
    config = lockshaw.get_config(args.path)
    assert config is not None
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
        
    cmake_args += ["-DFF_USE_CODE_COVERAGE=ON"]
    cmake(cmake_args, config, True)


def main_build(args: Any) -> None:
    config = lockshaw.get_config(args.path)
    assert config is not None
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
            **({"VERBOSE": "1"} if args.verbose else {}),
        },
        stderr=sys.stdout,
        cwd=config.build_dir,
    )


def main_test(args: Any) -> None:
    config = lockshaw.get_config(args.path)
    assert config is not None
    cwd = config.build_dir
    if args.coverage:
        cwd = config.cov_dir
    else:
        cwd = config.build_dir
    
    subprocess_check_call(
        [
            "make",
            "-j",
            str(args.jobs),
            *lockshaw.get_config(args.path).test_targets,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": str(DIR.parent.parent.parent),
            **({"VERBOSE": "1"} if args.verbose else {}),
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
                "lib/*",
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
    


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    root_p = subparsers.add_parser("root")
    root_p.set_defaults(func=main_root)
    root_p.add_argument("--path", "-p", type=Path, default=Path.cwd())

    test_p = subparsers.add_parser("test")
    test_p.set_defaults(func=main_test)
    test_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    test_p.add_argument("--verbose", "-v", action="store_true")
    test_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    test_p.add_argument("--coverage", "-c", action="store_true")
    test_p.add_argument(
        "--browser", "-b", action="store_true", help="open coverage info in browser"
    )

    build_p = subparsers.add_parser("build")
    build_p.set_defaults(func=main_build)
    build_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    build_p.add_argument("--verbose", "-v", action="store_true")
    build_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())

    cmake_p = subparsers.add_parser("cmake")
    cmake_p.set_defaults(func=main_cmake)
    cmake_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    cmake_p.add_argument("--force", "-f", action="store_true")
    cmake_p.add_argument("--trace", action="store_true")

    args = p.parse_args()
    if hasattr(args, "func") and args.func is not None:
        args.func(args)
    else:
        p.print_help()
        exit(1)


if __name__ == "__main__":
    main()
