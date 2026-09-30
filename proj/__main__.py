from pathlib import Path
from typing import (
    Any,
    Sequence,
    Union,
    BinaryIO,
    Collection,
    List,
    TypeVar,
    Type,
    Callable,
    Optional,
    Iterable,
    Set,
)
from . import subprocess_trace as subprocess
import os
import multiprocessing
import sys
from .config_file import (
    load_repo_config,
    dump_config,
    resolve_test_target,
    ProjectConfig,
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
    pretty_name_for_benchmark_case,
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
    CudaRunTarget,
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
    run_test_suites,
    run_test_case,
    resolve_test_case_target_using_build,
    report_test_failure,
    report_test_timeout,
    report_test_success,
    TerminationType,
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
from .move import (
    perform_file_group_move_with_include_and_ifndef_update,
)
from .rm import (
    rm_file_group,
)
from .trees import (
    load_root_filesystem,
    load_filesystem_for_repo,
)
from .parse_project import find_repo, parse_repo_path, parse_file_path
from .utils import map_optional
from .file_group_info import get_file_group_info
from .paths import (
    RepoRelPath,
    File,
)
from .unparse_project import get_repo_rel_path
from .includes import (
    parse_include_spec,
    find_occurrences_of_include,
)
from .doxygen import (
    run_doxygen,
)
from .tags import generate_tag_file

_l = logging.getLogger(name="proj")

DIR = Path(__file__).resolve().parent

STATUS_OK = 0
STATUS_ERR = 1

@dataclass(frozen=True)
class MainRootArgs:
    path: Path
    verbosity: int


def main_root(args: MainRootArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    print(repo.path)
    return STATUS_OK


@dataclass(frozen=True)
class MainConfigArgs:
    path: Path
    verbosity: int


def main_config(args: MainConfigArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    json.dump(dump_config(config), sort_keys=True, indent=2, fp=sys.stdout)
    return STATUS_OK


@dataclass(frozen=True)
class MainQueryPathArgs:
    path: Path
    verbosity: int
    file: Path


def main_query_path(args: MainQueryPathArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    file_repo_rel = RepoRelPath(args.file.absolute().relative_to(repo.path), repo)
    file = parse_file_path(file_repo_rel, config.extension_config)
    assert file is not None

    file_group_info = get_file_group_info(
        file.group, config.ifndef_name, config.extension_config
    )

    output = file_group_info.json()
    output['role'] = file.role.shortname

    json.dump(output, sort_keys=True, indent=2, fp=sys.stdout)
    return STATUS_OK


def xdg_open(path: Path) -> None:
    subprocess.check_call(
        ["xdg-open", str(path)],
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

def get_repo_root(p: Path) -> Path:
    fs = load_root_filesystem()
    repo = find_repo(p, fs)
    assert repo is not None
    return Path(repo.path)

def get_config(p: Path) -> ProjectConfig:
    fs = load_root_filesystem()
    repo = find_repo(p, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    return config

def main_cmake(args: MainCmakeArgs) -> int:
    config = get_config(args.path)

    repo = config.repo
    repo_file_tree = load_filesystem_for_repo(repo)

    if not args.dtgen_skip:
        run_dtgen(
            repo=repo,
            repo_file_tree=repo_file_tree,
            force=False,
            extension_config=config.extension_config,
            ifndef_base=config.ifndef_name,
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

    repo = config.repo
    repo_file_tree = load_filesystem_for_repo(repo)

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

    if not args.dtgen_skip:
        run_dtgen(
            repo=repo,
            repo_file_tree=repo_file_tree,
            force=False,
            extension_config=config.extension_config,
            ifndef_base=config.ifndef_name,
        )

    build_targets(
        repo=repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=targets,
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=build_dir,
        redirect_build_stdout_to_stderr=False,
    )
    return 0


@dataclass(frozen=True)
class MainBenchmarkArgs:
    path: Path
    verbosity: int
    jobs: int
    dtgen_skip: bool
    skip_gpu_benchmarks: bool
    targets: Sequence[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]]

def main_benchmark(args: MainBenchmarkArgs) -> int:
    _l.debug("Running main_benchmark for args: %s", args)
    config = get_config(args.path)

    repo = config.repo
    repo_file_tree = load_filesystem_for_repo(repo)

    requested_benchmark_targets = args.targets
    if len(requested_benchmark_targets) == 0:
        requested_benchmark_targets = list(config.default_benchmark_targets)
    _l.debug(
        "Determined requested benchmark targets to be: %s", requested_benchmark_targets
    )

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
        fail_with_error("No benchmark targets available to run")

    if not args.dtgen_skip:
        run_dtgen(
            repo=repo,
            repo_file_tree=repo_file_tree,
            force=False,
            extension_config=config.extension_config,
            ifndef_base=config.ifndef_name,
        )

    build_targets(
        repo=repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=[t.build_target for t in requested_benchmark_targets],
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=config.release_build_dir,
        redirect_build_stdout_to_stderr=True,
    )

    summary = call_benchmarks(
        config=config,
        benchmarks=requested_benchmark_targets,
        build_dir=config.release_build_dir,
        num_jobs=args.jobs,
    )
    num_passed = len(summary.passed)
    num_failed = len(summary.failed)
    num_timed_out = len(summary.timed_out)
    num_errored = len(summary.errored)

    print(''.join([
        f"Benchmark results: ",
        " / ".join([
            f"{num_passed} passed",
            f"{num_failed} failed",
            f"{num_timed_out} timed out",
            f"{num_errored} errored",
        ])
    ]))
    if (num_failed + num_timed_out + num_errored) > 0:
        lines = []

        if num_failed > 0:
            lines += [
                "The following benchmarks failed:",
                *["- " + pretty_name_for_benchmark_case(bm) for bm in summary.failed],
            ]

        if num_timed_out > 0:
            lines += [
                "The following benchmarks timed out:",
                *["- " + pretty_name_for_benchmark_case(bm) for bm in summary.timed_out],
            ]

        if num_timed_out > 0:
            lines += [
                "The following benchmarks encountered an error:",
                *["- " + pretty_name_for_benchmark_case(bm) for bm in summary.errored],
            ]

        fail_with_error("\n".join(lines))

    return 0


@dataclass(frozen=True)
class MainRunArgs:
    path: Path
    verbosity: int
    jobs: int
    target: Union[
        GenericBinTarget,
        BenchmarkCaseTarget,
        GenericTestSuiteTarget,
        GenericTestCaseTarget,
    ]
    debug_build: bool
    skip_gpu: bool
    target_run_args: Sequence[str]


def main_run(args: MainRunArgs) -> int:
    _l.debug('Starting to execute %s', main_run.__name__)
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
        redirect_build_stdout_to_stderr=True,
    )

    has_cuda = check_if_machine_supports_cuda()
    if not has_cuda and isinstance(run_target, CudaRunTarget):
        fail_with_error(
            f"Cannot run target {args.target} as no gpus are available on the current machine."
        )

    binary_path = build_dir / run_target.executable_path
    assert binary_path.is_file()

    cmd = [str(binary_path), *run_target.args, *args.target_run_args]
    result = subprocess.run(cmd)
    _l.info('Command completed with exit code %d', result.returncode)
    _l.debug('Finished executing %s', main_run.__name__)
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
        redirect_build_stdout_to_stderr=True,
    )

    has_cuda = check_if_machine_supports_cuda()
    if not has_cuda and isinstance(resolved_target, CudaRunTarget):
        fail_with_error(
            f"Cannot profile target {args.target} as no gpus are available on the current machine."
        )

    profile_file = profile_target(
        build_dir, resolved_target, dry_run=args.dry_run, tool=args.tool
    )
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
    force_assume_cuda_support: bool
    targets: Collection[Union[GenericTestSuiteTarget, GenericTestCaseTarget]]


def main_test(args: MainTestArgs) -> int:
    assert isinstance(args, MainTestArgs)

    config = get_config(args.path)

    repo = config.repo
    repo_file_tree = load_filesystem_for_repo(repo)

    if args.coverage:
        build_dir = config.coverage_build_dir
    else:
        build_dir = config.debug_build_dir

    if not build_dir.exists():
        cmake_all(config=config, fast=False, trace=False)

    requested_test_targets: List[
        Union[
            MixedTestSuiteTarget,
            CpuTestSuiteTarget,
            CudaTestSuiteTarget,
            CpuTestCaseTarget,
            CudaTestCaseTarget,
            GenericTestCaseTarget,
        ]
    ]
    if len(args.targets) == 0:
        requested_test_targets = list(config.default_test_targets)
    else:
        requested_test_targets = [resolve_test_target(config, t) for t in args.targets]

    def get_test_cases(
        x: Iterable[Any],
    ) -> List[Union[CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget]]:
        return [
            t
            for t in x
            if isinstance(
                t, (CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget)
            )
        ]

    def get_test_suites(
        x: Iterable[Any],
    ) -> List[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]]:
        return [
            t
            for t in x
            if isinstance(
                t, (MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget)
            )
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
        ) -> Optional[
            Union[CpuTestSuiteTarget, CpuTestCaseTarget, GenericTestCaseTarget]
        ]:
            if isinstance(
                t, (CpuTestSuiteTarget, CpuTestCaseTarget, GenericTestCaseTarget)
            ):
                return t
            elif isinstance(t, MixedTestSuiteTarget):
                return t.cpu_test_suite_target
            else:
                return None

        requested_test_targets_to_run = list(
            filtermap(requested_test_targets, remove_gpu_tests)
        )
        _l.info("Filtering test targets to remove gpu tests")
        _l.info("  unfiltered: %s", requested_test_targets)
        _l.info("  filtered:   %s", requested_test_targets_to_run)
    else:
        _l.info(
            "Skipping test target filtering as --skip-gpu-tests argument was not passed"
        )
        requested_test_targets_to_run = list(requested_test_targets)

    test_cases = get_test_cases(requested_test_targets_to_run)
    test_suites = get_test_suites(requested_test_targets_to_run)
    if (
        len(test_cases) == 0 and len(test_suites) > 0
    ):
        pass
    elif (
        len(test_suites) == 0 and len(test_cases) == 1
    ):
        pass
    else:
        raise ValueError(
            "Currently only n test suites or 1 test case is allowed. If you need this feature, let @lockshaw know."
        )

    if args.force_assume_cuda_support:
        has_cuda = True
    else:
        has_cuda = check_if_machine_supports_cuda()

    def cuda_failure():
        fail_with_error(
            "Cannot run gpu tests as no gpus are available on the current machine. "
            "Pass --skip-gpu-tests to skip running tests that require a GPU."
        )

    if (not has_cuda) and any(
        isinstance(t, (MixedTestSuiteTarget, CudaTestSuiteTarget, CudaTestCaseTarget))
        for t in requested_test_targets_to_run
    ):
        cuda_failure()

    if len(requested_test_targets_to_run) == 0:
        fail_with_error("No test targets available to run")

    requested_build_targets = set(t.build_target for t in requested_test_targets)

    if not args.dtgen_skip:
        run_dtgen(
            repo=repo,
            repo_file_tree=repo_file_tree,
            force=False,
            extension_config=config.extension_config,
            ifndef_base=config.ifndef_name,
        )

    build_targets(
        repo=repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=requested_build_targets,
        jobs=args.jobs,
        verbosity=args.verbosity,
        build_dir=build_dir,
        redirect_build_stdout_to_stderr=True,
    )

    def require_test_suite(
        t: Union[
            MixedTestSuiteTarget,
            CpuTestSuiteTarget,
            CudaTestSuiteTarget,
            CpuTestCaseTarget,
            CudaTestCaseTarget,
            GenericTestCaseTarget,
        ],
    ) -> Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]:
        assert isinstance(
            t, (MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget)
        )
        return t

    if len(get_test_cases(requested_test_targets_to_run)) == 0:
        test_suites = get_test_suites(requested_test_targets_to_run)
        _l.debug("No testcases required, running test suites %s", test_suites)
        assert args.debug is False
        test_statistics = run_test_suites(
            config=config,
            test_suites=test_suites,
            build_dir=build_dir,
            num_jobs=args.jobs,
        )
        num_passed = len(test_statistics.passed)
        num_failed = len(test_statistics.failed)
        num_timed_out = len(test_statistics.timed_out)
        num_total = num_passed + num_failed + num_timed_out
        print(
            f"Test results: {num_passed} passed / {num_failed} failed / {num_timed_out} timed out / {num_total} total"
        )
        if (num_failed + num_timed_out) > 0:
            lines = []

            if num_failed > 0:
                lines += [
                    "The following tests failed:",
                    *["- " + tc.full_name for tc in test_statistics.failed],
                ]

            if num_timed_out > 0:
                lines += [
                    "The following tests timed out:",
                    *["- " + tc.full_name for tc in test_statistics.timed_out],
                ]

            fail_with_error("\n".join(lines))

    else:
        assert len(get_test_suites(requested_test_targets_to_run)) == 0

        only_to_run = get_only(get_test_cases(requested_test_targets_to_run))
        _l.debug("No test suites required, running testcase %s", only_to_run)
        assert isinstance(
            only_to_run,
            (
                MixedTestSuiteTarget,
                CpuTestCaseTarget,
                CudaTestCaseTarget,
                GenericTestCaseTarget,
            ),
        )
        if isinstance(only_to_run, GenericTestCaseTarget):
            _l.debug("Type of test case %s is unknown, resolving using build...", only_to_run)
            only_to_run = resolve_test_case_target_using_build(
                config, only_to_run, build_dir
            )

        if isinstance(only_to_run, CudaTestCaseTarget) and args.skip_gpu_tests:
            fail_with_error(f"Test {only_to_run} requires CUDA but --skip-gpu-tests flag was passed.")
        elif isinstance(only_to_run, CudaTestCaseTarget) and not has_cuda:
            cuda_failure()
        else:
            _l.debug('Determined that test %s is runnable for has_cuda=%s', only_to_run, has_cuda)
            test_case_result = run_test_case(
                config=config,
                test_case=only_to_run,
                build_dir=build_dir,
                debug=args.debug,
            )
            _l.debug("Test case %s returned result %s", only_to_run, test_case_result)
            if test_case_result.termination == TerminationType.SUCCESS:
                report_test_success(only_to_run, test_case_result)
            elif test_case_result.termination == TerminationType.TIMEOUT:
                report_test_timeout(only_to_run, test_case_result)
                _l.debug("Test case %s timed out. Returning...", only_to_run)
                return STATUS_ERR
            else:
                assert test_case_result.termination == TerminationType.FAILURE
                report_test_failure(only_to_run, test_case_result)
                _l.debug("Test case %s failed. Returning...", only_to_run)
                return STATUS_ERR

    if args.coverage:
        _l.debug("Generating requested coverage data...")
        postprocess_coverage_data(config=config)
        view_coverage_data(config=config, browser=args.browser)

    _l.debug("Succesfully finished %s", main_test.__name__)
    return STATUS_OK


@dataclass(frozen=True)
class MainCheckArgs:
    path: Path
    check: Check
    jobs: int
    verbosity: int

def main_check(args: MainCheckArgs) -> int:
    config = get_config(args.path)

    run_check(config, args.check, verbosity=args.verbosity, num_jobs=args.jobs)

    return STATUS_OK

@dataclass(frozen=True)
class MainMoveArgs:
    path: Path
    src: Path
    dst: Path
    verbosity: int
    dry_run: bool
    skip_update_includes: bool
    skip_update_ifndefs: bool


def main_move(args: MainMoveArgs) -> int:
    config = get_config(args.path)

    root_path_tree = load_root_filesystem()
    src_repo_rel = parse_repo_path(args.src.absolute(), root_path_tree)
    assert src_repo_rel is not None
    dst_repo_rel = parse_repo_path(args.dst.absolute(), root_path_tree)
    assert dst_repo_rel is not None

    repo_file_tree = load_filesystem_for_repo(config.repo)

    assert args.src.is_file()
    perform_file_group_move_with_include_and_ifndef_update(
        repo_file_tree=repo_file_tree,
        src=src_repo_rel,
        dst=dst_repo_rel,
        extension_config=config.extension_config,
        ifndef_base=config.ifndef_name,
        update_includes=not args.skip_update_includes,
        update_ifndefs=not args.skip_update_ifndefs,
        dry_run=args.dry_run,
    )

    return STATUS_OK

@dataclass(frozen=True)
class MainRmArgs:
    path: Path
    target: Path
    dry_run: bool
    verbosity: int

def main_rm(args: MainRmArgs) -> int:
    config = get_config(args.path)

    root_path_tree = load_root_filesystem()

    target_repo_rel = parse_repo_path(args.target.absolute(), root_path_tree)
    assert target_repo_rel is not None

    repo_file_tree = load_filesystem_for_repo(config.repo)

    assert args.target.is_file()
    rm_file_group(
        repo_path_tree=repo_file_tree,
        target=target_repo_rel,
        extension_config=config.extension_config,
        dry_run=args.dry_run,
    )

    return STATUS_OK

@dataclass(frozen=True)
class MainFindIncludeArgs:
    path: Path
    include: str
    verbosity: int

def main_find_include(args: MainFindIncludeArgs) -> int:
    config = get_config(args.path)

    repo = config.repo
    repo_file_tree = load_filesystem_for_repo(repo)

    include_spec = parse_include_spec(args.include)
    found: Set[File] = find_occurrences_of_include(repo_file_tree, include_spec, config.extension_config)

    for file in found:
        repo_rel_path = get_repo_rel_path(file, config.extension_config)
        print(str(repo_rel_path.path))

    if len(found) == 0:
        fail_with_error('No matches found.')

    return STATUS_OK

@dataclass(frozen=True)
class MainLintArgs:
    path: Path
    files: Sequence[Path]
    profile_checks: bool
    verbosity: int


def main_lint(args: MainLintArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    assert repo is not None

    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)

    repo_tree = fs.restrict_to_subdir(repo.path)
    run_linter(
        repo=config.repo,
        repo_path_tree=repo_tree,
        extension_config=config.extension_config,
        files=files,
        profile_checks=args.profile_checks
    )
    return STATUS_OK


@dataclass(frozen=True)
class MainTagArgs:
    path: Path
    verbosity: int


def main_tag(args: MainTagArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    assert repo is not None

    generate_tag_file(config)

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
class MainFixIfndefsArgs:
    path: Path
    files: Sequence[Path]
    verbosity: int


def main_fix_ifndefs(args: Any) -> int:
    return STATUS_OK


@dataclass(frozen=True)
class MainDtgenArgs:
    path: Path
    files: Sequence[Path]
    force: bool
    verbosity: int


def main_dtgen(args: MainDtgenArgs) -> int:
    fs = load_root_filesystem()
    repo = find_repo(args.path, fs)
    assert repo is not None
    config = load_repo_config(repo, fs)
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = [
            parsed
            for p in args.files
            if (parsed := parse_file_path(RepoRelPath(p.absolute().relative_to(repo.path), repo), config.extension_config)) is not None
        ]

    run_dtgen(
        repo=repo,
        repo_file_tree=fs.restrict_to_subdir(repo.path),
        force=args.force,
        extension_config=config.extension_config,
        ifndef_base=config.ifndef_name,
        files=files,
        delete_outdated=True,
    )
    return STATUS_OK


@dataclass(frozen=True)
class MainDoxygenArgs:
    path: Path
    browser: bool
    verbosity: int


def main_doxygen(args: MainDoxygenArgs) -> int:
    config = get_config(args.path)

    stderr: Optional[BinaryIO] = sys.stderr.buffer
    stdout: Optional[BinaryIO] = sys.stdout.buffer

    env = dict(os.environ)
    if args.verbosity > logging.INFO:
        env["DOXYGEN_QUIET"] = "YES"
    if args.verbosity > logging.WARN:
        env["DOXYGEN_WARNINGS"] = "NO"
    if args.verbosity > logging.CRITICAL:
        stderr = None
        stdout = None

    did_succeed = run_doxygen(
        config=config,
        log_level=args.verbosity,
        stdout=stdout,
        stderr=stderr,
        env=env,
    )

    if not did_succeed:
        return STATUS_ERR

    if args.browser:
        xdg_open(config.doxygen_dir / "html/index.html")

    return STATUS_OK


T = TypeVar("T")


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    root_fs = load_root_filesystem()
    repo = find_repo(Path.cwd(), root_fs)

    config = map_optional(repo, lambda r: load_repo_config(r, root_fs))

    def set_main_signature(
        parser: argparse.ArgumentParser, func: Callable[[T], int], args_type: Type[T]
    ) -> None:
        def _f(
            args: argparse.Namespace,
            func: Callable[[T], int] = func,
            args_type: Type[T] = args_type,
        ) -> int:
            setattr(args, "path", Path.cwd())
            return func(
                args_type(
                    **{
                        k.replace("-", "_"): v
                        for k, v in vars(args).items()
                        if k != "func"
                    }
                )
            )

        parser.set_defaults(func=_f)

    root_p = subparsers.add_parser("root")
    set_main_signature(root_p, main_root, MainRootArgs)
    add_verbosity_args(root_p)

    config_p = subparsers.add_parser("config")
    set_main_signature(config_p, main_config, MainConfigArgs)
    add_verbosity_args(config_p)

    query_path_p = subparsers.add_parser("query-path")
    set_main_signature(query_path_p, main_query_path, MainQueryPathArgs)
    query_path_p.add_argument("file", type=Path)
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
    test_p.add_argument("--force-assume-cuda-support", action="store_true", help=argparse.SUPPRESS)
    test_p.add_argument("targets", nargs="*", type=parse_generic_test_target)
    add_verbosity_args(test_p)

    build_p = subparsers.add_parser("build")
    set_main_signature(build_p, main_build, MainBuildArgs)
    build_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    build_p.add_argument("--dtgen-skip", action="store_true")
    build_p.add_argument("--release", action="store_true")
    build_p.add_argument(
        "targets",
        nargs="*",
        type=lambda p: BuildTarget.from_str(
            require_nonnull(config).configured_names, p
        ),
    )
    add_verbosity_args(build_p)

    benchmark_p = subparsers.add_parser("benchmark")
    set_main_signature(benchmark_p, main_benchmark, MainBenchmarkArgs)
    benchmark_p.add_argument(
        "--jobs", "-j", type=int, default=multiprocessing.cpu_count()
    )
    benchmark_p.add_argument("--dtgen-skip", action="store_true")
    benchmark_p.add_argument("--skip-gpu-benchmarks", action="store_true")
    benchmark_p.add_argument("targets", nargs="*", type=parse_generic_benchmark_target)
    add_verbosity_args(benchmark_p)

    run_p = subparsers.add_parser("run")
    set_main_signature(run_p, main_run, MainRunArgs)
    run_p.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count())
    run_p.add_argument("target", type=parse_generic_run_target)
    run_p.add_argument("--skip-gpu", action="store_true")
    run_p.add_argument("--debug-build", action="store_true")
    run_p.add_argument("target-run-args", nargs="*")
    add_verbosity_args(run_p)

    profile_p = subparsers.add_parser("profile")
    set_main_signature(profile_p, main_profile, MainProfileArgs)
    profile_p.add_argument(
        "--jobs", "-j", type=int, default=multiprocessing.cpu_count()
    )
    profile_p.add_argument("--dry-run", action="store_true")
    profile_p.add_argument(
        "--tool", choices=list(sorted(ProfilingTool)), default=ProfilingTool.CALLGRIND
    )
    profile_p.add_argument("--skip-gpu", action="store_true")
    profile_p.add_argument("-g", "--gui", action="store_true")
    profile_p.add_argument("target", type=parse_generic_run_target)
    profile_p.add_argument("target-run-args", nargs="*")
    add_verbosity_args(profile_p)

    cmake_p = subparsers.add_parser("cmake")
    set_main_signature(cmake_p, main_cmake, MainCmakeArgs)
    cmake_p.add_argument("--fast", action="store_true")
    cmake_p.add_argument("--trace", action="store_true")
    cmake_p.add_argument("--dtgen-skip", action="store_true")
    add_verbosity_args(cmake_p)

    dtgen_p = subparsers.add_parser("dtgen")
    set_main_signature(dtgen_p, main_dtgen, MainDtgenArgs)
    dtgen_p.add_argument(
        "--force", action="store_true", help="Disable incremental toml->c++ generation"
    )
    dtgen_p.add_argument("files", nargs="*", type=Path)
    add_verbosity_args(dtgen_p)

    format_p = subparsers.add_parser("format")
    set_main_signature(format_p, main_format, MainFormatArgs)
    format_p.add_argument("files", nargs="*", type=Path)
    add_verbosity_args(format_p)

    fix_ifndefs_p = subparsers.add_parser("fix-ifndefs")
    set_main_signature(fix_ifndefs_p, main_fix_ifndefs, MainFixIfndefsArgs)
    fix_ifndefs_p.add_argument("files", nargs="*", type=Path)
    add_verbosity_args(fix_ifndefs_p)

    check_p = subparsers.add_parser("check")
    set_main_signature(check_p, main_check, MainCheckArgs)
    check_p.add_argument(
        "--jobs", "-j", type=int, default=multiprocessing.cpu_count()
    )
    check_p.add_argument("check", choices=list(sorted(Check)))
    add_verbosity_args(check_p)

    move_p = subparsers.add_parser("mv")
    set_main_signature(move_p, main_move, MainMoveArgs)
    move_p.add_argument("src", type=Path)
    move_p.add_argument("dst", type=Path)
    move_p.add_argument("--dry-run", "-n", action="store_true")
    move_p.add_argument("--skip-update-includes", action="store_true")
    move_p.add_argument("--skip-update-ifndefs", action="store_true")
    add_verbosity_args(move_p)

    rm_p = subparsers.add_parser("rm")
    set_main_signature(rm_p, main_rm, MainRmArgs)
    rm_p.add_argument("target", type=Path)
    rm_p.add_argument("--dry-run", "-n", action="store_true")
    add_verbosity_args(rm_p)

    find_include_p = subparsers.add_parser("find-include")
    set_main_signature(find_include_p, main_find_include, MainFindIncludeArgs)
    find_include_p.add_argument("include", type=str)
    add_verbosity_args(find_include_p)

    lint_p = subparsers.add_parser("lint")
    set_main_signature(lint_p, main_lint, MainLintArgs)
    lint_p.add_argument("--profile-checks", action="store_true")
    lint_p.add_argument("files", nargs="*", type=Path)
    add_verbosity_args(lint_p)

    tag_p = subparsers.add_parser("tag")
    set_main_signature(tag_p, main_tag, MainTagArgs)
    add_verbosity_args(tag_p)

    doxygen_p = subparsers.add_parser("doxygen")
    set_main_signature(doxygen_p, main_doxygen, MainDoxygenArgs)
    doxygen_p.add_argument(
        "--browser",
        "-b",
        action="store_true",
        help="open generated documentation in browser",
    )
    add_verbosity_args(doxygen_p)

    return p


def main(argv: Sequence[str]) -> int:
    p = make_parser()
    args = p.parse_args(argv)

    logging.basicConfig(
        level=calculate_log_level(args),
    )
    _l.debug('Running for argv=%s', argv)

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
