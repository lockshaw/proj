from pathlib import Path
from typing import (
    Any,
    Sequence,
    Union,
    TextIO,
    Collection,
    List,
)
from . import subprocess_trace as subprocess
import os
import multiprocessing
import sys
from .config_file import (
    get_config,
    get_config_root,
    get_target_test_name,
    get_target_benchmark_name,
    get_benchmark_path,
)
from .dtgen import run_dtgen
from .format import run_formatter
from .lint import run_linter
import logging
from dataclasses import dataclass
from .verbosity import (
    add_verbosity_args,
    calculate_log_level,
)
from .gpu_handling import (
    infer_build_run_plan,
)
from .coverage import (
    postprocess_coverage_data,
    view_coverage_data,
)
from .build import (
    build_targets,
)
from .failure import fail_with_error
from .benchmarks import (
    call_benchmarks,
    upload_to_bencher,
)
from .cmake import (
    cmake_all,
)
import argparse

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
    subprocess.check_call(
        ['xdg-open', str(path)],
        stderr=sys.stdout,
        env=os.environ,
    )

@dataclass(frozen=True)
class MainCmakeArgs:
    path: Path
    fast: bool
    trace: bool
    dtgen_skip: bool
    verbosity: int

def main_cmake(args: MainCmakeArgs) -> None:
    config = get_config(args.path)

    if not args.dtgen_skip:
        run_dtgen(
            root=config.base,
            config=config,
            force=False,
        )

    cmake_all(config=config, fast=args.fast, trace=args.trace)

@dataclass(frozen=True)
class MainBuildArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    targets: Collection[str]
    release: bool

def main_build(args: MainBuildArgs) -> None:
    config = get_config(args.path)

    if args.release:
        build_dir = config.release_build_dir
    else:
        build_dir = config.debug_build_dir
    
    if not build_dir.exists():
        cmake_all(config=config, fast=False, trace=False)

    targets: List[str]
    if len(args.targets) == 0:
        targets = list(config.build_targets)
    else:
        targets = list(args.targets)

    build_targets(
        config=config,
        targets=targets,
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        cwd=build_dir,
    )

@dataclass(frozen=True)
class MainBenchmarkArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    skip_gpu_benchmarks: bool
    skip_build_gpu_benchmarks: bool
    skip_cpu_benchmarks: bool
    skip_build_cpu_benchmarks: bool
    targets: Collection[str]
    upload: bool

def main_benchmark(args: MainBenchmarkArgs) -> None:
    config = get_config(args.path)

    requested_benchmark_targets: List[str]
    if len(args.targets) == 0:
        requested_benchmark_targets = list(config.benchmark_targets)
    else:
        requested_benchmark_targets = [get_target_benchmark_name(t) for t in args.targets]

    benchmark_targets_requiring_gpu = [get_target_benchmark_name("kernels")]

    build_run_plan = infer_build_run_plan(
        requested_targets=requested_benchmark_targets,
        target_requires_gpu=lambda t: t in benchmark_targets_requiring_gpu,
        skip_run_gpu_targets=args.skip_gpu_benchmarks,
        skip_build_gpu_targets=args.skip_build_gpu_benchmarks,
        skip_run_cpu_targets=args.skip_cpu_benchmarks,
        skip_build_cpu_targets=args.skip_build_cpu_benchmarks,
    )

    if build_run_plan.failed_gpu_check:
        fail_with_error(
            'Cannot run gpu benchmarks as no gpus are available on the current machine. '
            'Pass --skip-gpu-benchmarks to skip running benchmarks that require a GPU.'
        )

    if len(build_run_plan.targets_to_run) == 0:
        fail_with_error('No benchmark targets available to run')

    build_targets(
        config=config,
        targets=build_run_plan.targets_to_build,
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        cwd=config.release_build_dir,
    )

    benchmark_result = call_benchmarks([get_benchmark_path(config, b) for b in build_run_plan.targets_to_run])
    if args.upload:
        upload_to_bencher(benchmark_result)

@dataclass(frozen=True)
class MainRunArgs:
    path: Path
    verbosity: int
    jobs: int
    target: str
    debug_mode: bool
    target_run_args: Sequence[str]

def main_run(args: MainRunArgs) -> None:
    config = get_config(args.path)

    run_targets_requiring_gpu: List[str] = []

    build_run_plan = infer_build_run_plan(
        requested_targets=[args.target],
        target_requires_gpu=lambda t: t in run_targets_requiring_gpu,
        skip_run_gpu_targets=False,
        skip_build_gpu_targets=False,
        skip_run_cpu_targets=False,
        skip_build_cpu_targets=False,
    )

    if build_run_plan.failed_gpu_check:
        fail_with_error(
            f'Cannot run target {args.target} as no gpus are available on the current machine.'
        )

    if args.debug_mode:
        build_dir = config.debug_build_dir
    else:
        build_dir = config.release_build_dir

    build_targets(
        config=config,
        targets=build_run_plan.targets_to_build,
        dtgen_skip=False,
        jobs=args.jobs,
        verbosity=args.verbosity,
        cwd=build_dir,
    )

    binary_path = build_dir / 'bin' / args.target
    assert binary_path.is_file()

    subprocess.check_call([binary_path, *args.target_run_args])


@dataclass(frozen=True)
class MainTestArgs:
    path: Path
    coverage: bool
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

def main_test(args: MainTestArgs) -> None:
    config = get_config(args.path)

    if args.coverage:
        build_dir = config.coverage_build_dir
    else:
        build_dir = config.debug_build_dir

    if not build_dir.exists():
        cmake_all(config=config, fast=False, trace=False)


    # Currently hardcode GPU tests as 'kernels-tests'
    requested_test_targets: List[str]
    if len(args.targets) == 0:
        requested_test_targets = list(config.test_targets)
    else:
        requested_test_targets = [get_target_test_name(t) for t in args.targets]

    test_targets_requiring_gpu = ["kernels-tests"]

    build_run_plan = infer_build_run_plan(
        requested_targets=requested_test_targets,
        target_requires_gpu=lambda t: t in test_targets_requiring_gpu,
        skip_run_gpu_targets=args.skip_gpu_tests,
        skip_build_gpu_targets=args.skip_build_gpu_tests,
        skip_run_cpu_targets=args.skip_cpu_tests,
        skip_build_cpu_targets=args.skip_build_cpu_tests,
    )

    if build_run_plan.failed_gpu_check:
        fail_with_error(
            'Cannot run gpu tests as no gpus are available on the current machine. '
            'Pass --skip-gpu-tests to skip running tests that require a GPU.'
        )
    
    if len(build_run_plan.targets_to_run) == 0:
        fail_with_error('No test targets available to run')

    build_targets(
        config=config,
        targets=build_run_plan.targets_to_build,
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        cwd=build_dir,
    )

    target_regex = "^(" + "|".join(build_run_plan.targets_to_run) + ")$"
    subprocess.run(
        [
            "ctest",
            "--progress",
            "--output-on-failure",
            "-L",
            target_regex,
        ],
        stderr=sys.stdout,
        cwd=build_dir,
        env=os.environ,
    )
    
    if args.coverage:
        postprocess_coverage_data(config=config)
        view_coverage_data(config=config, browser=args.browser)
    

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
        delete_outdated=not args.no_delete_outdated,
    )

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
    subprocess.check_call(
        ['doxygen', 'docs/doxygen/Doxyfile'],
        env=env,
        stdout=stdout,
        stderr=stderr,
        cwd=root,
    )

    if args.browser:
        xdg_open(config.doxygen_dir / 'html/index.html') 


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    def set_main_signature(parser, func, args_type):
        def _f(args: argparse.Namespace, func=func, args_type=args_type):
            func(args_type(**{k.replace('-', '_'): v for k, v in vars(args).items() if k != 'func'}))
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
    test_p.add_argument("--coverage", "-c", action="store_true")   
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
    build_p.add_argument("--release", action="store_true")
    build_p.add_argument('targets', nargs='*')
    add_verbosity_args(build_p)

    benchmark_p = subparsers.add_parser('benchmark')
    set_main_signature(benchmark_p, main_benchmark, MainBenchmarkArgs)
    benchmark_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    benchmark_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())
    benchmark_p.add_argument('--dtgen-skip', action='store_true')
    benchmark_p.add_argument("--skip-gpu-benchmarks", action="store_true")
    benchmark_p.add_argument("--skip-build-gpu-benchmarks", action="store_true")
    benchmark_p.add_argument("--skip-cpu-benchmarks", action="store_true")
    benchmark_p.add_argument("--skip-build-cpu-benchmarks", action="store_true")
    benchmark_p.add_argument('--upload', action='store_true')
    benchmark_p.add_argument('targets', nargs='*')
    add_verbosity_args(benchmark_p)

    run_p = subparsers.add_parser('run')
    set_main_signature(run_p, main_run, MainRunArgs)
    run_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    run_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())
    run_p.add_argument('target', type=str)
    run_p.add_argument('--debug-mode', action='store_true')
    run_p.add_argument('target-run-args', nargs='*')
    add_verbosity_args(run_p)
    

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

    return p

def main() -> None:
    p = make_parser()
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
