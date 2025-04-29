from pathlib import Path
from typing import (
    Any,
    Sequence,
    Union,
    TextIO,
    Collection,
    List,
    TypeVar,
    Type,
    Callable,
    Optional,
    Iterable,
)
from . import subprocess_trace as subprocess
import os
import multiprocessing
import sys
from .config_file import (
    try_get_config,
    get_config,
    get_config_root,
    dump_config,
    get_path_info,
    resolve_test_target,
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
    check_if_machine_supports_cuda,
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
    pretty_print_benchmark,
)
from .cmake import (
    cmake_all,
)
import argparse
from .targets import (
    GenericBinTarget,
    MixedTestSuiteTarget,
    CpuTestSuiteTarget,
    CudaTestSuiteTarget,
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
    BuildTarget,
    CpuTestCaseTarget,
    CudaTestCaseTarget,
    GenericTestSuiteTarget,
    GenericTestCaseTarget,
    parse_generic_test_target,
    parse_generic_benchmark_target,
    parse_generic_run_target,
)
from .profile import (
    profile_target,
    ProfilingTool,
    visualize_profile,
)
from .testing import (
    run_tests,
    run_test_case,
    resolve_test_case_target_using_build,
)
from .checks import (
    Check,
    run_check,
)
from .utils import (
    filtermap,
    require_nonnull,
    get_only,
)
import json
from .target_resolution import (
    fully_resolve_run_target,
)

_l = logging.getLogger(name='proj')

DIR = Path(__file__).resolve().parent

STATUS_OK = 0

@dataclass(frozen=True)
class MainRootArgs:
    path: Path
    verbosity: int

def main_root(args: MainRootArgs) -> int:
    config_root = get_config_root(args.path)
    print(config_root)
    return STATUS_OK

@dataclass(frozen=True)
class MainConfigArgs:
    path: Path
    verbosity: int

def main_config(args: MainConfigArgs) -> int:
    config = get_config(args.path)
    json.dump(dump_config(config), sort_keys=True, indent=2, fp=sys.stdout)
    return STATUS_OK

@dataclass(frozen=True)
class MainQueryPathArgs:
    path: Path
    verbosity: int
    file: Path

def main_query_path(args: MainQueryPathArgs) -> int:
    path_info = get_path_info(args.file)
    json.dump(path_info.json(), sort_keys=True, indent=2, fp=sys.stdout)
    return STATUS_OK

def xdg_open(path: Path) -> None:
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

def main_cmake(args: MainCmakeArgs) -> int:
    config = get_config(args.path)

    if not args.dtgen_skip:
        run_dtgen(
            root=config.base,
            config=config,
            force=False,
        )

    cmake_all(config=config, fast=args.fast, trace=args.trace)
    return 0

@dataclass(frozen=True)
class MainBuildArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    targets: Collection[BuildTarget]
    release: bool

def main_build(args: MainBuildArgs) -> int:
    config = get_config(args.path)

    if args.release:
        build_dir = config.release_build_dir
    else:
        build_dir = config.debug_build_dir
    
    if not build_dir.exists():
        cmake_all(config=config, fast=False, trace=False)

    targets: List[BuildTarget]
    if len(args.targets) == 0:
        targets = list(config.default_build_targets)
    else:
        targets = list(args.targets)

    build_targets(
        config=config,
        targets=targets,
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=build_dir,
    )
    return 0

@dataclass(frozen=True)
class MainBenchmarkArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    skip_gpu_benchmarks: bool
    targets: Collection[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]]
    upload: bool
    browser: bool

def main_benchmark(args: MainBenchmarkArgs) -> int:
    _l.debug('Running main_benchmark for args: %s', args)
    config = get_config(args.path)

    requested_benchmark_targets: List[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]]
    if len(args.targets) == 0:
        requested_benchmark_targets = list(config.default_benchmark_targets)
    else:
        requested_benchmark_targets = list(args.targets)
    _l.debug('Determined requested benchmark targets to be: %s', requested_benchmark_targets)

    # build_run_plan = infer_build_run_plan(
    #     requested_targets=requested_benchmark_targets,
    #     target_requires_gpu=lambda t: t in benchmark_targets_requiring_gpu,
    #     skip_run_gpu_targets=args.skip_gpu_benchmarks,
    #     skip_build_gpu_targets=args.skip_build_gpu_benchmarks,
    #     skip_run_cpu_targets=args.skip_cpu_benchmarks,
    #     skip_build_cpu_targets=args.skip_build_cpu_benchmarks,
    # )
    # _l.debug('Inferred build/run plan: %s', build_run_plan)

    # if build_run_plan.failed_gpu_check:
    #     fail_with_error(
    #         'Cannot run gpu benchmarks as no gpus are available on the current machine. '
    #         'Pass --skip-gpu-benchmarks to skip running benchmarks that require a GPU.'
    #     )

    if len(requested_benchmark_targets) == 0:
        fail_with_error('No benchmark targets available to run')

    build_targets(
        config=config,
        targets=[t.build_target for t in requested_benchmark_targets],
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=config.release_build_dir,
    )

    benchmark_result = call_benchmarks(requested_benchmark_targets, config.release_build_dir)
    pretty_print_benchmark(benchmark_result, f=sys.stdout)
    if args.upload:
        upload_to_bencher(config, benchmark_result, browser=args.browser)

    return 0

@dataclass(frozen=True)
class MainRunArgs:
    path: Path
    verbosity: int
    jobs: int
    target: Union[
        GenericBinTarget,
        BenchmarkSuiteTarget,
        BenchmarkCaseTarget,
        GenericTestSuiteTarget,
        GenericTestCaseTarget,
    ]
    debug_build: bool
    skip_gpu: bool
    target_run_args: Sequence[str]

def main_run(args: MainRunArgs) -> int:
    config = get_config(args.path)

    if args.debug_build:
        build_dir = config.debug_build_dir
    else:
        build_dir = config.release_build_dir

    run_target = fully_resolve_run_target(
        config=config, 
        build_dir=build_dir, 
        unresolved_target=args.target, 
        jobs=args.jobs, 
        verbosity=args.verbosity,
        skip_gpu=args.skip_gpu,
    )

    binary_path = build_dir / run_target.executable_path
    assert binary_path.is_file()

    cmd = [str(binary_path), *run_target.args, *args.target_run_args]
    result = subprocess.run(cmd)
    print(result)
    return result.returncode

@dataclass(frozen=True)
class MainProfileArgs:
    path: Path
    verbosity: int
    jobs: int
    dry_run: bool
    gui: bool
    skip_gpu: bool
    tool: ProfilingTool
    target: Union[
        GenericBinTarget,
        BenchmarkSuiteTarget,
        BenchmarkCaseTarget,
        GenericTestSuiteTarget,
        GenericTestCaseTarget,
    ]
    target_run_args: Sequence[str]

def main_profile(args: MainProfileArgs) -> int:
    config = get_config(args.path)

    build_dir = config.release_build_dir

    resolved_target = fully_resolve_run_target(
        config=config, 
        build_dir=build_dir, 
        unresolved_target=args.target, 
        jobs=args.jobs, 
        verbosity=args.verbosity, 
        skip_gpu=args.skip_gpu,
    )

    profile_file = profile_target(build_dir, resolved_target, dry_run=args.dry_run, tool=args.tool)
    if args.gui:
        visualize_profile(profile_file, tool=args.tool)
    else:
        print(profile_file)

    return 0


@dataclass(frozen=True)
class MainTestArgs:
    path: Path
    coverage: bool
    verbosity: int
    jobs: int
    dtgen_force: bool
    dtgen_skip: bool
    browser: bool
    debug: bool
    skip_gpu_tests: bool
    targets: Collection[Union[GenericTestSuiteTarget, GenericTestCaseTarget]]

def main_test(args: MainTestArgs) -> int:
    assert isinstance(args, MainTestArgs)

    config = get_config(args.path)

    if args.coverage:
        build_dir = config.coverage_build_dir
    else:
        build_dir = config.debug_build_dir

    if not build_dir.exists():
        cmake_all(config=config, fast=False, trace=False)

    requested_test_targets: List[Union[
        MixedTestSuiteTarget, 
        CpuTestSuiteTarget, 
        CudaTestSuiteTarget, 
        CpuTestCaseTarget, 
        CudaTestCaseTarget, 
        GenericTestCaseTarget
    ]]
    if len(args.targets) == 0:
        requested_test_targets = list(config.default_test_targets)
    else:
        requested_test_targets = [resolve_test_target(config, t) for t in args.targets]

    def get_test_cases(x: Iterable[Any]) -> List[Union[CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget]]:
        return [
            t for t in x if isinstance(t, (CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget))
        ]

    def get_test_suites(x: Iterable[Any]) -> List[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]]:
        return [
            t for t in x if isinstance(t, (MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget))
        ]

    if args.skip_gpu_tests:
        def remove_gpu_tests(
            t: Union[
                MixedTestSuiteTarget, 
                CpuTestSuiteTarget,
                CudaTestSuiteTarget,
                CpuTestCaseTarget,
                CudaTestCaseTarget,
                GenericTestCaseTarget,
            ],
        ) -> Optional[Union[CpuTestSuiteTarget, CpuTestCaseTarget, GenericTestCaseTarget]]:
            if isinstance(t, (CpuTestSuiteTarget, CpuTestCaseTarget, GenericTestCaseTarget)):
                return t
            elif isinstance(t, MixedTestSuiteTarget):
                return t.cpu_test_suite_target
            else:
                return None

        requested_test_targets_to_run = list(filtermap(requested_test_targets, remove_gpu_tests))
        _l.info('Filtering test targets to remove gpu tests')
        _l.info('  unfiltered: %s', requested_test_targets)
        _l.info('  filtered:   %s', requested_test_targets_to_run)
    else:
        _l.info('Skipping test target filtering as --skip-gpu-tests argument was not passed')
        requested_test_targets_to_run = list(requested_test_targets)

    if len(get_test_cases(requested_test_targets_to_run)) == 0:
        pass
    elif len(get_test_suites(requested_test_targets_to_run)) == 0 and len(get_test_cases(requested_test_targets_to_run)) == 1:
        pass
    else:
        raise ValueError('Currently only n test suites or 1 test case is allowed. If you need this feature, let @lockshaw know.')

    has_cuda = check_if_machine_supports_cuda()

    def cuda_failure():
        fail_with_error(
            'Cannot run gpu tests as no gpus are available on the current machine. '
            'Pass --skip-gpu-tests to skip running tests that require a GPU.'
        )

    if (not has_cuda) and any(isinstance(t, (MixedTestSuiteTarget, CudaTestSuiteTarget, CudaTestCaseTarget)) for t in requested_test_targets_to_run):
        cuda_failure()
    
    if len(requested_test_targets_to_run) == 0:
        fail_with_error('No test targets available to run')

    requested_build_targets = set(t.build_target for t in requested_test_targets)

    build_targets(
        config=config,
        targets=requested_build_targets,
        dtgen_skip=args.dtgen_skip,
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=build_dir,
    )

    def require_test_suite(
        t: Union[
            MixedTestSuiteTarget, 
            CpuTestSuiteTarget, 
            CudaTestSuiteTarget, 
            CpuTestCaseTarget, 
            CudaTestCaseTarget, 
            GenericTestCaseTarget
        ],
    ) -> Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]:
        assert isinstance(t, (MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget))
        return t

    if len(get_test_cases(requested_test_targets_to_run)) == 0:
        run_tests(get_test_suites(requested_test_targets_to_run), build_dir, debug=args.debug)
    else:
        assert len(get_test_suites(requested_test_targets_to_run)) == 0

        only_to_run = get_only(get_test_cases(requested_test_targets_to_run))
        assert isinstance(only_to_run, (MixedTestSuiteTarget, CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget))
        if isinstance(only_to_run, GenericTestCaseTarget):
            only_to_run = resolve_test_case_target_using_build(config, only_to_run, build_dir)

        if isinstance(only_to_run, CudaTestCaseTarget) and args.skip_gpu_tests:
            pass
        elif isinstance(only_to_run, CudaTestCaseTarget) and not has_cuda:
            cuda_failure()
        else:
            run_test_case(only_to_run, build_dir, debug=args.debug)

    if args.coverage:
        postprocess_coverage_data(config=config)
        view_coverage_data(config=config, browser=args.browser)

    return STATUS_OK
    
@dataclass(frozen=True)
class MainCheckArgs:
    path: Path
    check: Check
    verbosity: int

def main_check(args: MainCheckArgs) -> int:
    config = get_config(args.path)

    run_check(config, args.check, verbosity=args.verbosity)

    return STATUS_OK

@dataclass(frozen=True)
class MainLintArgs:
    path: Path
    files: Sequence[Path]
    profile_checks: bool
    verbosity: int

def main_lint(args: MainLintArgs) -> int:
    root = get_config_root(args.path)
    config = get_config(args.path)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_linter(root, config, files, profile_checks=args.profile_checks)
    return STATUS_OK

@dataclass(frozen=True)
class MainFormatArgs:
    path: Path
    files: Sequence[Path]
    verbosity: int

def main_format(args: Any) -> int:
    config = get_config(args.path)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_formatter(config, files)
    return STATUS_OK

@dataclass(frozen=True)
class MainDtgenArgs:
    path: Path
    files: Sequence[Path]
    force: bool
    verbosity: int

def main_dtgen(args: MainDtgenArgs) -> int:
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
        delete_outdated=True,
    )
    return STATUS_OK

@dataclass(frozen=True)
class MainDoxygenArgs:
    path: Path
    browser: bool
    verbosity: int

def main_doxygen(args: MainDoxygenArgs) -> int:
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

    return STATUS_OK


T = TypeVar('T')

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    config = try_get_config(Path.cwd())

    def set_main_signature(parser: argparse.ArgumentParser, func: Callable[[T], int], args_type: Type[T]) -> None:
        def _f(args: argparse.Namespace, func: Callable[[T], int]=func, args_type: Type[T]=args_type) -> int:
            setattr(args, 'path', Path.cwd())
            return func(args_type(**{k.replace('-', '_'): v for k, v in vars(args).items() if k != 'func'}))
        parser.set_defaults(func=_f)

    root_p = subparsers.add_parser("root")
    set_main_signature(root_p, main_root, MainRootArgs)
    add_verbosity_args(root_p)

    config_p = subparsers.add_parser("config")
    set_main_signature(config_p, main_config, MainConfigArgs)
    add_verbosity_args(config_p)

    query_path_p = subparsers.add_parser("query-path")
    set_main_signature(query_path_p, main_query_path, MainQueryPathArgs)
    query_path_p.add_argument('file', type=Path)
    add_verbosity_args(query_path_p)

    test_p = subparsers.add_parser("test")
    set_main_signature(test_p, main_test, MainTestArgs)
    test_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    test_p.add_argument("--coverage", "-c", action="store_true")   
    test_p.add_argument("--dtgen-force", action="store_true")   
    test_p.add_argument("--dtgen-skip", action="store_true")
    test_p.add_argument(
        "--browser", "-b", action="store_true", help="open coverage info in browser"
    )
    test_p.add_argument("--skip-gpu-tests", action="store_true")
    test_p.add_argument("--debug", action="store_true")
    test_p.add_argument('targets', nargs='*', type=parse_generic_test_target)
    add_verbosity_args(test_p)

    build_p = subparsers.add_parser("build")
    set_main_signature(build_p, main_build, MainBuildArgs)
    build_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    build_p.add_argument("--dtgen-skip", action="store_true")
    build_p.add_argument("--release", action="store_true")
    build_p.add_argument('targets', nargs='*', type=lambda p: BuildTarget.from_str(require_nonnull(config).configured_names, p))
    add_verbosity_args(build_p)

    benchmark_p = subparsers.add_parser('benchmark')
    set_main_signature(benchmark_p, main_benchmark, MainBenchmarkArgs)
    benchmark_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())
    benchmark_p.add_argument('--dtgen-skip', action='store_true')
    benchmark_p.add_argument("--skip-gpu-benchmarks", action="store_true")
    benchmark_p.add_argument('--upload', action='store_true')
    benchmark_p.add_argument('--browser', action='store_true')
    benchmark_p.add_argument('targets', nargs='*', type=parse_generic_benchmark_target)
    add_verbosity_args(benchmark_p)

    run_p = subparsers.add_parser('run')
    set_main_signature(run_p, main_run, MainRunArgs)
    run_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())
    run_p.add_argument('target', type=parse_generic_run_target)
    run_p.add_argument('--skip-gpu', action='store_true')
    run_p.add_argument('--debug-build', action='store_true')
    run_p.add_argument('target-run-args', nargs='*')
    add_verbosity_args(run_p)
    
    profile_p = subparsers.add_parser('profile')
    set_main_signature(profile_p, main_profile, MainProfileArgs)
    profile_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())
    profile_p.add_argument('--dry-run', action='store_true')
    profile_p.add_argument('--tool', choices=list(sorted(ProfilingTool)), default=ProfilingTool.CALLGRIND)
    profile_p.add_argument('--skip-gpu', action='store_true')
    profile_p.add_argument('-g', '--gui', action='store_true')
    profile_p.add_argument('target', type=parse_generic_run_target)
    profile_p.add_argument('target-run-args', nargs='*')
    add_verbosity_args(profile_p)

    cmake_p = subparsers.add_parser("cmake")
    set_main_signature(cmake_p, main_cmake, MainCmakeArgs)
    cmake_p.add_argument("--fast", action="store_true")
    cmake_p.add_argument("--trace", action="store_true")
    cmake_p.add_argument("--dtgen-skip", action="store_true")
    add_verbosity_args(cmake_p)

    dtgen_p = subparsers.add_parser('dtgen')
    dtgen_p.add_argument('--force', action='store_true', help='Disable incremental toml->c++ generation')
    dtgen_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(dtgen_p)

    format_p = subparsers.add_parser('format')
    set_main_signature(format_p, main_format, MainFormatArgs)
    format_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(format_p)

    check_p = subparsers.add_parser('check')
    set_main_signature(check_p, main_check, MainCheckArgs)
    check_p.add_argument('check', choices=list(sorted(Check)))
    add_verbosity_args(check_p)

    lint_p = subparsers.add_parser('lint')
    set_main_signature(lint_p, main_lint, MainLintArgs)
    lint_p.add_argument('--profile-checks', action='store_true')
    lint_p.add_argument('files', nargs='*', type=Path)
    add_verbosity_args(lint_p)

    doxygen_p = subparsers.add_parser('doxygen')
    set_main_signature(doxygen_p, main_doxygen, MainDoxygenArgs)
    doxygen_p.add_argument(
        "--browser", "-b", action="store_true", help="open generated documentation in browser"
    )
    add_verbosity_args(doxygen_p)

    return p

def main(argv: Sequence[str]) -> int:
    p = make_parser()
    args = p.parse_args(argv)

    logging.basicConfig(
        level=calculate_log_level(args),
    )

    if hasattr(args, "func") and args.func is not None:
        result = args.func(args)
        assert isinstance(result, int), result
        return result
    else:
        p.print_help()
        return 1

def entrypoint() -> None:
    sys.exit(main(sys.argv[1:]))

if __name__ == "__main__":
    entrypoint()
