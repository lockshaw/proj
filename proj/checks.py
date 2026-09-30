from typing import (
    Optional,
    Sequence,
    Iterable,
    BinaryIO,
)
from collections import (
    Counter,
)
from os import (
    PathLike,
)
from proj.strenum import StrEnum
from .config_file import (
    ProjectConfig,
    ExtensionConfig,
)
from .format import (
    run_formatter_check as _run_formatter_check,
)
from .dtgen import (
    run_dtgen,
)
from .cmake import (
    cmake_all,
)
from .build import (
    build_targets,
)
from .testing import (
    run_test_suites,
    list_test_cases_in_test_suites,
)
from .benchmarks import (
    call_benchmarks,
)
import logging
from .failure import (
    fail_without_error,
    fail_with_error,
)
from . import subprocess_trace as subprocess
from .layout import (
    run_layout_check as _run_layout_check,
    scan_repo_for_files,
    UnrecognizedFile,
    IncompleteGroup,
)
from .trees import (
    PathTree,
    FileTree,
    MutableFileTreeWithMtime,
    load_filesystem_for_repo,
)
from .paths import (
    File,
    RoleInGroup,
    RepoRelPath,
)
from .ifndef import (
    get_current_ifndef,
    get_correct_ifndef_for_path,
)
from .unparse_project import (
    get_repo_rel_path,
)
from .includes import (
    get_include_path,
    get_generated_include_path,
    find_includes_in_cpp_file_contents,
    get_include_path_for_file,
)
from .doxygen import (
    run_doxygen,
)
import sys
import os
from pathlib import Path
import string

_l = logging.getLogger(__name__)


class Check(StrEnum):
    FORMAT = "format"
    CPU_CI = "cpu-ci"
    GPU_CI = "gpu-ci"
    LAYOUT = "layout"
    INCLUDE = "include"
    IFNDEF = "ifndef"
    DOXYGEN = "doxygen"
    INVALID_TEST_CASE_NAMES = "invalid-test-names"
    DUPLICATE_TEST_CASE_NAMES = "duplicate-test-names"

def run_layout_check(
    repo_path_tree: PathTree,
    config: ProjectConfig,
) -> None:
    extension_config = config.extension_config
    ignore_paths = [RepoRelPath(p) for p in config.layout_ignore_paths]

    failed = False
    for error in _run_layout_check(repo_path_tree, extension_config, ignore_paths):
        if isinstance(error, IncompleteGroup):
            _l.warn('Incomplete file group %s', error.file_group)
            _l.warn('  Present:')
            for present_role in error.present:
                present_path = get_repo_rel_path(File(error.file_group, present_role), extension_config)
                assert repo_path_tree.has_file(present_path.path)
                _l.warn('  - %s', present_path.path)
            _l.warn('  Missing:')
            for missing_role in error.missing:
                missing_path = get_repo_rel_path(File(error.file_group, missing_role), extension_config)
                _l.warn('  - %s', missing_path.path)
            failed = True
        elif isinstance(error, UnrecognizedFile):
            repo_rel_path: RepoRelPath = get_repo_rel_path(error.path, extension_config=extension_config)
            _l.warn('Unrecognized file at %s', repo_rel_path.path)
            failed = True
    if failed:
        fail_with_error("Layout check failed.")

def run_include_check(
    repo_path_tree: FileTree,
    extension_config: ExtensionConfig,
) -> None:
    valid_include_paths = set()
    for file in scan_repo_for_files(repo_path_tree, extension_config):
        if isinstance(file, File):
            if file.role == RoleInGroup.PUBLIC_HEADER:
                valid_include_paths.add(get_include_path(file.group, header_extension=extension_config.header_extension))
            elif file.role == RoleInGroup.DTGEN_TOML:
                valid_include_paths.add(get_generated_include_path(file.group, header_extension=extension_config.header_extension))

    failed = False
    for file in scan_repo_for_files(repo_path_tree, extension_config):
        if isinstance(file, File):
            if file.role == RoleInGroup.DTGEN_TOML:
                valid_include_paths.add(get_include_path(file.group, header_extension=extension_config.header_extension))
            else:
                contents = repo_path_tree.get_file_contents(
                    get_repo_rel_path(file, extension_config).path
                )
                includes = find_includes_in_cpp_file_contents(
                    contents,
                    header_extension=extension_config.header_extension,
                )
                for include in includes:
                    if isinstance(include, File):
                        include_path = get_include_path_for_file(include, header_extension=extension_config.header_extension)
                        if include_path not in valid_include_paths:
                            _l.warning('Found invalid include in %s: %s does not exist', file, include)
                            failed = True
    if failed:
        fail_with_error("Include check failed.")


def run_ifndef_check(
    repo_path_tree: FileTree,
    ifndef_base: str,
    extension_config: ExtensionConfig,
) -> None:
    failed = False
    for file in scan_repo_for_files(repo_path_tree, extension_config):
        if isinstance(file, File):
            if file.role != RoleInGroup.PUBLIC_HEADER:
                continue
            file_path = get_repo_rel_path(file, extension_config)
            contents = repo_path_tree.get_file_contents(file_path.path)
            curr_ifndef = get_current_ifndef(contents)
            correct_ifndef = get_correct_ifndef_for_path(ifndef_base, file_path)
            if curr_ifndef != correct_ifndef:
                _l.warn('Incorrect ifndef in file %s: %s (current) != %s (correct)', file, curr_ifndef, correct_ifndef)
                failed = True
    if failed:
        fail_with_error("Ifndef check failed.")

_TEST_NAME_CHARS = string.ascii_letters + string.digits + '-_&()<>:=,./+%![]{} '
def is_valid_test_name(test_name: str) -> bool:
    return all(c in _TEST_NAME_CHARS for c in test_name)

def run_invalid_test_names_check(
    config: ProjectConfig,
    verbosity: int,
    build_dir: Path,
    num_jobs: int,
) -> None:
    repo_file_tree = load_filesystem_for_repo(config.repo)

    build_targets(
        repo=config.repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=set(t.build_target for t in config.all_test_targets),
        jobs=num_jobs,
        verbosity=verbosity,
        build_dir=build_dir,
        redirect_build_stdout_to_stderr=False,
    )


    invalid_test_case_names = set(
        tc.test_case_name for tc in
        list_test_cases_in_test_suites(
            test_suites=config.all_test_targets,
            build_dir=build_dir,
        )
        if not is_valid_test_name(tc.test_case_name)
    )

    if len(invalid_test_case_names) > 0:
        fail_with_error('\n'.join([
            'Found invalid test case names:',
            *invalid_test_case_names,
        ]))

def run_duplicate_test_names_check(
    config: ProjectConfig,
    verbosity: int,
    build_dir: Path,
    num_jobs: int,
) -> None:
    repo_file_tree = load_filesystem_for_repo(config.repo)

    build_targets(
        repo=config.repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=set(t.build_target for t in config.all_test_targets),
        jobs=num_jobs,
        verbosity=verbosity,
        build_dir=build_dir,
        redirect_build_stdout_to_stderr=False,
    )

    test_case_counts = Counter([
        tc.test_case_name for tc in
        list_test_cases_in_test_suites(
            test_suites=config.all_test_targets,
            build_dir=build_dir,
        )
    ])

    reused_test_case_names = list(sorted(
        test_case_name for test_case_name, count in test_case_counts.items()
        if count > 1
    ))

    if len(reused_test_case_names) > 0:
        fail_with_error('\n'.join([
            'Found duplicate test case names:',
            *reused_test_case_names,
        ]))


def run_doxygen_check(
    config: ProjectConfig,
    verbosity: int,
) -> None:
    stderr: Optional[BinaryIO] = sys.stderr.buffer
    stdout: Optional[BinaryIO] = sys.stdout.buffer

    env = dict(os.environ)
    if verbosity > logging.INFO:
        env["DOXYGEN_QUIET"] = "YES"
    if verbosity > logging.WARN:
        env["DOXYGEN_WARNINGS"] = "NO"
    if verbosity > logging.CRITICAL:
        stderr = None
        stdout = None

    did_succeed = run_doxygen(config=config, log_level=verbosity, stdout=stdout, stderr=stderr, env=env)
    if not did_succeed:
        fail_with_error("Doxygen check failed.")

def run_formatter_check(
    config: ProjectConfig, files: Optional[Sequence['PathLike[str]']] = None
) -> None:
    try:
        _run_formatter_check(config=config, files=files)
    except subprocess.CalledProcessError:
        fail_with_error("Formatter check failed. You should probably run 'proj format'")


def run_check(config: ProjectConfig, check: Check, verbosity: int, num_jobs: int) -> None:
    repo_file_tree = load_filesystem_for_repo(config.repo)

    if check == Check.FORMAT:
        run_formatter_check(config)
    elif check == Check.LAYOUT:
        run_layout_check(repo_file_tree, config)
    elif check == Check.CPU_CI:
        run_cpu_ci(config, repo_file_tree, verbosity=verbosity, num_jobs=num_jobs)
    elif check == Check.GPU_CI:
        run_gpu_ci(config, verbosity=verbosity, num_jobs=num_jobs)
    elif check == Check.IFNDEF:
        run_ifndef_check(
            repo_file_tree,
            config.ifndef_name,
            config.extension_config,
        )
    elif check == Check.INCLUDE:
        run_include_check(
            repo_file_tree,
            config.extension_config,
        )
    elif check == Check.DOXYGEN:
        run_doxygen_check(config, verbosity=verbosity)
    elif check == Check.DUPLICATE_TEST_CASE_NAMES:
        run_duplicate_test_names_check(
            config,
            verbosity=verbosity,
            build_dir=config.debug_build_dir,
            num_jobs=num_jobs,
        )
    elif check == Check.INVALID_TEST_CASE_NAMES:
        run_invalid_test_names_check(
            config,
            verbosity=verbosity,
            build_dir=config.debug_build_dir,
            num_jobs=num_jobs,
        )
    else:
        raise ValueError(f'Invalid check: {check!r}')


def run_build_check(config: ProjectConfig, repo_file_tree: MutableFileTreeWithMtime, verbosity: int, num_jobs: int) -> None:
    run_dtgen(
        repo=config.repo,
        repo_file_tree=repo_file_tree,
        force=True,
        extension_config=config.extension_config,
        ifndef_base=config.ifndef_name,
    )
    cmake_all(config, fast=False, trace=False)

    build_targets(
        repo=config.repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=config.all_build_targets,
        jobs=num_jobs,
        verbosity=verbosity,
        build_dir=config.debug_build_dir,
        redirect_build_stdout_to_stderr=False,
    )


def run_cpu_ci(config: ProjectConfig, repo_file_tree: MutableFileTreeWithMtime, verbosity: int, num_jobs: int) -> None:

    _l.info("Running repository layout check...")
    run_layout_check(repo_file_tree, config)

    _l.info("Running formatter check...")
    run_formatter_check(config)

    _l.info("Running dtgen --force...")
    run_dtgen(
        repo=config.repo,
        repo_file_tree=repo_file_tree,
        force=True,
        extension_config=config.extension_config,
        ifndef_base=config.ifndef_name,
    )
    _l.info("Running cmake...")
    cmake_all(config, fast=False, trace=False)

    cpu_build_targets = config.all_build_targets
    _l.info("Building %s", cpu_build_targets)
    build_targets(
        repo=config.repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=cpu_build_targets,
        jobs=num_jobs,
        verbosity=verbosity,
        build_dir=config.coverage_build_dir,
        redirect_build_stdout_to_stderr=False,
    )

    _l.info("Checking for invalid tests in %s...", config.all_test_targets)
    run_invalid_test_names_check(
        config=config,
        verbosity=verbosity,
        build_dir=config.coverage_build_dir,
        num_jobs=num_jobs,
    )

    _l.info("Checking for duplicate tests in %s...", config.all_test_targets)
    run_duplicate_test_names_check(
        config=config,
        verbosity=verbosity,
        build_dir=config.coverage_build_dir,
        num_jobs=num_jobs,
    )

    _l.info("Running tests %s", config.all_cpu_test_targets)
    test_results = run_test_suites(
        config=config,
        test_suites=list(sorted(config.all_cpu_test_targets)),
        build_dir=config.coverage_build_dir,
        num_jobs=num_jobs,
    )

    if len(test_results.failed) > 0 or len(test_results.timed_out) > 0:
        fail_without_error()

    if config.doxygen_enabled:
        _l.info("Running doxygen check...")
        run_doxygen_check(config, verbosity=verbosity)

    if len(config.all_benchmark_targets) > 0:
        _l.info("Building release build of %s", config.all_benchmark_targets)
        build_targets(
            repo=config.repo,
            repo_path_tree=repo_file_tree,
            config=config,
            targets=[t.build_target for t in config.all_benchmark_targets],
            jobs=num_jobs,
            verbosity=verbosity,
            build_dir=config.release_build_dir,
            redirect_build_stdout_to_stderr=False,
        )

        _l.info("Running benchmarks %s", config.all_benchmark_targets)
        benchmark_results = call_benchmarks(
            config=config,
            benchmarks=list(sorted(config.all_benchmark_targets)),
            build_dir=config.release_build_dir,
            num_jobs=num_jobs,
        )

        if (len(benchmark_results.failed) > 0
            or len(benchmark_results.timed_out) > 0
            or len(benchmark_results.errored) > 0
        ):
            fail_without_error()


def run_gpu_ci(config: ProjectConfig, verbosity: int, num_jobs: int) -> None:
    repo_file_tree = load_filesystem_for_repo(config.repo)

    _l.info("Running dtgen")
    run_dtgen(
        repo=config.repo,
        repo_file_tree=repo_file_tree,
        force=True,
        extension_config=config.extension_config,
        ifndef_base=config.ifndef_name,
    )
    _l.info("Running cmake")
    cmake_all(config, fast=False, trace=False)

    cuda_build_targets = [t.build_target for t in config.all_cuda_test_targets]
    _l.info("Building targets %", cuda_build_targets)
    build_targets(
        repo=config.repo,
        repo_path_tree=repo_file_tree,
        config=config,
        targets=cuda_build_targets,
        jobs=num_jobs,
        verbosity=verbosity,
        build_dir=config.debug_build_dir,
        redirect_build_stdout_to_stderr=False,
    )

    test_suites = list(sorted(config.all_cuda_test_targets))
    _l.info("Running test suites %s", test_suites)
    test_results = run_test_suites(
        config=config,
        test_suites=test_suites,
        build_dir=config.debug_build_dir,
        num_jobs=num_jobs,
    )

    if len(test_results.failed) > 0:
        fail_without_error()
