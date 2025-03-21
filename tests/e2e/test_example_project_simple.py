import pytest
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Iterator,
    Iterable,
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
from ..project_utils import (
    project_instance as _project_instance,
    cmade_project_instance as _cmade_project_instance,
    MAX_VERBOSITY,
)
from .e2e_utils import (
    require_successful,
    run,
    check_cmd_succeeds,
    check_cmd_fails,
)

def project_instance():
    return _project_instance('simple')

def cmade_project_instance():
    return _cmade_project_instance('simple')

@pytest.mark.e2e
@pytest.mark.slow
def test_main_cmake() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'cmake',
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

@pytest.mark.e2e
@pytest.mark.slow
def test_get_cmake_target_names_list() -> None:
    with cmade_project_instance() as d:
        config = get_config(d)

        required = [
            'lib1',
            'lib2',
            'bin1',
            'bin2',
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

@pytest.mark.e2e
@pytest.mark.slow
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

        names = config.configured_names

        debug_target_list = list(get_targets_list(names, config.debug_build_dir))
        check_target_list(debug_target_list)

        release_target_list = list(get_targets_list(names, config.release_build_dir))
        check_target_list(release_target_list)

        coverage_target_list = list(get_targets_list(names, config.coverage_build_dir))
        check_target_list(coverage_target_list)

@pytest.mark.e2e
@pytest.mark.slow
def test_debug_build() -> None:
    with cmade_project_instance() as d:
        config = get_config(d)

        targets = [
            BuildTarget.from_str(config.configured_names, 'lib1'),
            BuildTarget.from_str(config.configured_names, 'bin2'),
            BuildTarget.from_str(config.configured_names, 'lib2:tests'),
            BuildTarget.from_str(config.configured_names, 'lib1:benchmarks'),
        ]

        require_successful(run(d, [
            'build',
            '-j1',
            'lib1',
            'bin2',
            'lib2:test',
            'lib1:benchmarks',
        ]))

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

@pytest.mark.e2e
@pytest.mark.slow
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

@pytest.mark.e2e
@pytest.mark.slow
def test_test_all() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_test_test_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
            'lib2',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_test_test_case():
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'test',
            '-j1',
            'lib2:call_lib2',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_run_bin() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            '-j1',
            'bin1',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_run_test_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            '-j1',
            'lib1:tests',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_run_test_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            '-j1',
            'lib1:tests:call_lib1',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_run_benchmark_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            '-j1',
            'lib1:benchmarks',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_run_benchmark_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'run',
            '-j1',
            'lib1:benchmarks:example_benchmark/75/16'
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_benchmark_suite() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'benchmark',
            '-j1',
            'lib1',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_benchmark_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'benchmark',
            '-j1',
            'lib1:example_benchmark/75/16',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_test_suite_callgrind() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            'lib1:tests',
        ]))

        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_test_case_callgrind() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            'lib1:tests:call_lib1'
        ]))

        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_benchmark_suite_callgrind() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            'lib1:benchmarks'
        ]))

        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_benchmark_case_callgrind() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            'lib1:benchmarks:example_benchmark/75/32'
        ]))

        assert 'example_benchmark/25/16' not in result.stdout
        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
def test_profile_test_suite_perf() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:tests',
        ]))

        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
def test_profile_test_case_perf() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:tests:call_lib1'
        ]))
        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
def test_profile_benchmark_suite_perf() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:benchmarks'
        ]))
        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
def test_profile_benchmark_case_perf() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:benchmarks:example_benchmark/75/32'
        ]))
        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_test_suite_perf_dry_run() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            '--dry-run',
            'lib1:tests',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_test_case_perf_dry_run() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            '--dry-run',
            'lib1:tests:call_lib1'
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_benchmark_suite_perf_dry_run() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            '--dry-run',
            'lib1:benchmarks'
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_benchmark_case_perf_dry_run() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            '--dry-run',
            'lib1:benchmarks:example_benchmark/75/32'
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_format() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'check',
            'format',
        ])
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_succeeds(d, [
            'check',
            'format',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_tests() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'cpu-tests',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ])
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ])

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skip
def test_lint() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'lint',
        ])
