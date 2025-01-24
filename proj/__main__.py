from enum import Enum, auto
import glob
from pathlib import Path
from typing import (
    Any,
    Sequence,
    Union,
    TextIO,
    Optional,
    Collection,
    List,
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

@dataclass(frozen=True)
class MainRootArgs:
    path: Path
    verbosity: int

def main_root(args: MainRootArgs) -> None:
    config_root = get_config_root(args.path)
    print(config_root)

def xdg_open(path: Path):
    subprocess_check_call(
        ['xdg-open', str(path)],
        stderr=sys.stdout,
        env=os.environ,
    )

def fail_with_error(err: str, error_code: int = 1) -> None:
    _l.error(err)
    sys.exit(1)

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

def cmake(cmake_args, config, build_type):
    cwd = get_dir_for_build_type(config, build_type)
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
    fast: bool
    trace: bool
    dtgen_skip: bool
    verbosity: int

class BuildType(Enum):
    normal = auto()
    coverage = auto()
    profile = auto()

def get_dir_for_build_type(config: ProjectConfig, build_type: BuildType) -> Path:
    if build_type == BuildType.COVERAGE:
        return config.cov_dir
    elif build_type == BuildType.PROFILE:
        return config.prof_dir
    elif build_type == BuildType.NORMAL:
        return config.build_dir
    else:
        raise ValueError(f'{build_type} in function get_dir_for_build_type is not recognized')

def main_cmake(args: MainCmakeArgs) -> None:
    if not args.dtgen_skip:
        main_dtgen(args=MainDtgenArgs(
            path=args.path,
            files=[],
            no_delete_outdated=False,
            force=False,
            verbosity=args.verbosity,
        ))

    config = get_config(args.path)
    if not args.fast:
        if config.build_dir.exists():
            shutil.rmtree(config.build_dir)
        if config.cov_dir.exists():
            shutil.rmtree(config.cov_dir)
    config.build_dir.mkdir(exist_ok=True, parents=True)
    config.cov_dir.mkdir(exist_ok=True, parents=True)
    config.prof_dir.mkdir(exist_ok=True, parents=True)
    cmake_args = [f"-D{k}={v}" for k, v in config.cmake_flags.items()]
    cmake_args += shlex.split(os.environ.get("CMAKE_FLAGS", ""))
    if args.trace:
        cmake_args += ["--trace", "--trace-expand", "--trace-redirect=trace.log"]
    cmake(cmake_args, config, BuildType.normal)
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
 
    cmake(cmake_args + ["-DFF_USE_CODE_COVERAGE=ON"], config, BuildType.coverage)
    cmake(
        cmake_args + [
            "-DCMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS} -pg", 
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={config.prof_dir}",
            f"-DGMON_OUT_PREFIX={config.prof_dir}/gmon"
        ], 
        config, 
        BuildType.PROFILE
    )

@dataclass(frozen=True)
class MainBuildArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    targets: Collection[str]

def main_build(args: MainBuildArgs) -> None:
    config = get_config(args.path)

    build_targets: List[str]
    if len(args.targets) == 0:
        build_targets = list(config.build_targets)
    else:
        build_targets = list(args.targets)

    if len(build_targets) == 0:
        fail_with_error('No build targets selected')

    if not args.dtgen_skip:
        main_dtgen(args=MainDtgenArgs(
            path=args.path,
            files=[],
            no_delete_outdated=False,
            force=False,
            verbosity=args.verbosity,
        ))

    subprocess_check_call(
        [
            "make",
            "-j",
            str(args.jobs),
            *build_targets,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": config.base,
            **({"VERBOSE": "1"} if args.verbosity <= logging.DEBUG else {}),
        },
        stderr=sys.stdout,
        cwd=config.build_dir,
    )


@dataclass(frozen=True)
class MainTestArgs:
    path: Path
    build_type: BuildType
    verbosity: int
    jobs: int
    dtgen_force: bool
    dtgen_skip: bool
    browser: bool
    skip_gpu_tests: bool
    skip_build_gpu_tests: bool
    skip_cpu_tests: bool
    skip_build_cpu_tests: bool
    targets: Collection[str]


def check_if_machine_supports_gpu() -> bool:
    try:
        result = subprocess_check_call(['nvidia-smi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        _l.info('Could not find executable nvidia-smi in path')
        return False
    except subprocess.CalledProcessError:
        _l.info('nvidia-smi returned nonzero error code')
        return False

def main_test(args: MainTestArgs) -> None:
    if not args.dtgen_skip:
        main_dtgen(args=MainDtgenArgs(
            path=args.path,
            files=[],
            no_delete_outdated=False,
            force=args.dtgen_force,
            verbosity=args.verbosity,
        ))

    skip_gpu_tests = args.skip_gpu_tests or args.skip_build_gpu_tests
    skip_cpu_tests = args.skip_cpu_tests or args.skip_build_cpu_tests

    config = get_config(args.path)
    cwd = get_dir_for_build_type(config, args.build_type)

    # Currently hardcode GPU tests as 'kernels-tests'
    requested_test_targets: List[str]
    if len(args.targets) == 0:
        requested_test_targets = list(config.test_targets)
    else:
        requested_test_targets = [t + '-tests' for t in args.targets]

    test_targets_requiring_gpu = ["kernels-tests"]

    gpu_test_targets_to_build = [target for target in requested_test_targets if target in test_targets_requiring_gpu]
    if args.skip_build_gpu_tests:
        _l.info('Skipping building gpu test targets: %s', gpu_test_targets_to_build)
        gpu_test_targets_to_build = []

    cpu_test_targets_to_build = [target for target in requested_test_targets if target not in test_targets_requiring_gpu]
    if args.skip_build_cpu_tests:
        _l.info('Skipping building cpu test targets: %s', cpu_test_targets_to_build)
        cpu_test_targets_to_build = []

    test_targets_to_build = cpu_test_targets_to_build + gpu_test_targets_to_build

    if args.skip_cpu_tests and len(cpu_test_targets_to_build) > 0:
        _l.info('Skipping running cpu test targets: %s', cpu_test_targets_to_build)
        cpu_test_targets_to_run = []
    else:
        cpu_test_targets_to_run = cpu_test_targets_to_build

    if args.skip_gpu_tests and len(gpu_test_targets_to_build) > 0:
        _l.info('Skipping running gpu test targets: %s', gpu_test_targets_to_build)
        gpu_test_targets_to_run = []
    else:
        gpu_test_targets_to_run = gpu_test_targets_to_build

    gpu_available = check_if_machine_supports_gpu()
    if (not gpu_available) and (not skip_gpu_tests) and len(gpu_test_targets_to_run) > 0:
        fail_with_error(
            'Cannot run gpu tests as no gpus are available on the current machine. '
            'Pass --skip-gpu-tests to skip running tests that require a GPU.'
        )
    
    test_targets_to_run = cpu_test_targets_to_run + gpu_test_targets_to_run

    if len(test_targets_to_run) == 0:
        fail_with_error('No test targets available')

    subprocess_check_call(
        [
            "make",
            "-j",
            str(args.jobs),
            *test_targets_to_build,
        ],
        env={
            **os.environ,
            "CCACHE_BASEDIR": config.base,
            # "CCACHE_NOHASHDIR": "1",
            **({"VERBOSE": "1"} if args.verbosity <= logging.DEBUG else {}),
        },
        stderr=sys.stdout,
        cwd=cwd,
    )
    
    target_regex = "^(" + "|".join(test_targets_to_run) + ")$"
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
    
    if args.build_type == BuildType.COVERAGE:
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
        
        # filter out .dtg.h, .dtg.cc, and test code
        subprocess_run(
            [
                "lcov",
                "--remove",
                "main_coverage.info",
                f"{config.base}/lib/*.dtg.h",
                f"{config.base}/lib/*.dtg.cc",
                f"{config.base}/lib/*/test/**",
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

    if args.build_type == BuildType.PROFILE:
        subprocess_run(
            [
                "gprof",
                None, #TODO(@pietro) what goes here?
                config.prof_dir / "gmon.out",
            ],
            stdout=open(config.prof_dir / "gprof_output.txt", "w"),
            stderr=sys.stdout,
            cwd=config.prof_dir,
            env=os.environ,
        )

@dataclass(frozen=True)
class MainLintArgs:
    path: Path
    files: Sequence[Path]
    profile_checks: bool
    verbosity: int

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

@dataclass(frozen=True)
class MainFormatArgs:
    path: Path
    files: Sequence[Path]
    verbosity: int

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
    no_delete_outdated: bool
    force: bool
    verbosity: int

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
    for outdated in find_outdated(root, config):
        if args.no_delete_outdated:
            _l.warning(f'Possible out-of-date file at {outdated}')
        else:
            _l.info(f'Removing out-of-date file at {outdated}')
            outdated.unlink()

@dataclass(frozen=True)
class MainDoxygenArgs:
    path: Path
    browser: bool
    verbosity: int

def main_doxygen(args: MainDoxygenArgs) -> None:
    root = get_config_root(args.path)
    config = get_config(args.path)

    env = {
        **os.environ,
        'FF_HOME': root,
    }
    stderr: Union[int, TextIO] = sys.stderr
    stdout: Union[int, TextIO] = sys.stdout

    if args.verbosity > logging.INFO:
        env['DOXYGEN_QUIET'] = 'YES'
    if args.verbosity > logging.WARN:
        env['DOXYGEN_WARNINGS'] = 'NO'
    if args.verbosity > logging.CRITICAL:
        stderr = subprocess.DEVNULL
        stdout = subprocess.DEVNULL

    config.doxygen_dir.mkdir(exist_ok=True, parents=True)
    subprocess_check_call(
        ['doxygen', 'docs/doxygen/Doxyfile'],
        env=env,
        stdout=stdout,
        stderr=stderr,
        cwd=root,
    )

    if args.browser:
        xdg_open(config.doxygen_dir / 'html/index.html') 


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    def set_main_signature(parser, func, args_type):
        def _f(args: argparse.Namespace, func=func, args_type=args_type):
            func(args_type(**{k: v for k, v in vars(args).items() if k != 'func'}))
        parser.set_defaults(func=_f)

    root_p = subparsers.add_parser("root")
    set_main_signature(root_p, main_root, MainRootArgs)
    root_p.set_defaults(func=main_root)
    root_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    add_verbosity_args(root_p)

    test_p = subparsers.add_parser("test")
    set_main_signature(test_p, main_test, MainTestArgs)
    test_p.set_defaults(func=main_test)
    test_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    test_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    test_p.add_argument("--build-type", type=BuildType, choices=list(BuildType), default=BuildType.normal)
    test_p.add_argument("--dtgen-force", action="store_true")   
    test_p.add_argument("--dtgen-skip", action="store_true")
    test_p.add_argument(
        "--browser", "-b", action="store_true", help="open coverage info in browser"
    )
    test_p.add_argument("--skip-gpu-tests", action="store_true")
    test_p.add_argument("--skip-build-gpu-tests", action="store_true")
    test_p.add_argument("--skip-cpu-tests", action="store_true")
    test_p.add_argument("--skip-build-cpu-tests", action="store_true")
    test_p.add_argument('targets', nargs='*')
    add_verbosity_args(test_p)

    build_p = subparsers.add_parser("build")
    set_main_signature(build_p, main_build, MainBuildArgs)
    build_p.set_defaults(func=main_build)
    build_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    build_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    build_p.add_argument("--dtgen-skip", action="store_true")
    build_p.add_argument('targets', nargs='*')
    add_verbosity_args(build_p)

    cmake_p = subparsers.add_parser("cmake")
    set_main_signature(cmake_p, main_cmake, MainCmakeArgs)
    cmake_p.add_argument("--path", "-p", type=Path, default=Path.cwd())
    cmake_p.add_argument("--fast", action="store_true")
    cmake_p.add_argument("--trace", action="store_true")
    cmake_p.add_argument("--dtgen-skip", action="store_true")
    add_verbosity_args(cmake_p)

    dtgen_p = subparsers.add_parser('dtgen')
    dtgen_p.set_defaults(func=main_dtgen)
    dtgen_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    dtgen_p.add_argument('--force', action='store_true', help='Disable incremental toml->c++ generation')
    dtgen_p.add_argument('--no-delete-outdated', action='store_true')
    dtgen_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(dtgen_p)

    format_p = subparsers.add_parser('format')
    set_main_signature(format_p, main_format, MainFormatArgs)
    format_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    format_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(format_p)

    lint_p = subparsers.add_parser('lint')
    set_main_signature(lint_p, main_lint, MainLintArgs)
    lint_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    lint_p.add_argument('--profile-checks', action='store_true')
    lint_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(lint_p)

    doxygen_p = subparsers.add_parser('doxygen')
    set_main_signature(doxygen_p, main_doxygen, MainDoxygenArgs)
    doxygen_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    doxygen_p.add_argument(
        "--browser", "-b", action="store_true", help="open generated documentation in browser"
    )
    add_verbosity_args(doxygen_p)

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
