import pytest
import os
from contextlib import contextmanager
from typing import (
    Iterator,
    Iterable,
    Mapping,
    List,
    TYPE_CHECKING,
)
from pathlib import Path
from proj.targets import (
    BuildTarget,
    LibTarget,
    GenericBinTarget,
    GenericTestSuiteTarget,
    BenchmarkSuiteTarget,
    CpuTestSuiteTarget,
)
from proj.__main__ import get_config
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
    list_test_cases_in_test_suites,
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
import json
from contextlib import AbstractContextManager
from proj.trees import load_filesystem_for_repo

if TYPE_CHECKING:
    import nclib
else:
    try:
        import nclib
    except ImportError:
        nclib = None


def project_instance() -> 'AbstractContextManager[Path]':
    return _project_instance('simple')

def cmade_project_instance() -> 'AbstractContextManager[Path]':
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
            GenericBinTarget('bin1').build_target,
            GenericBinTarget('bin2').build_target,
            GenericTestSuiteTarget('lib1').build_target,
            GenericTestSuiteTarget('lib2').build_target,
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
            repo=config.repo,
            repo_path_tree=load_filesystem_for_repo(config.repo),
            config=config,
            targets=list(targets),
            jobs=1,
            verbosity=MAX_VERBOSITY,
            build_dir=get_build_dir(config, build_mode),
            redirect_build_stdout_to_stderr=False,
        )
        yield d

@pytest.mark.e2e
@pytest.mark.slow
def test_list_tests_in_target() -> None:
    lib2_target = CpuTestSuiteTarget('lib2')
    with built_project_instance([
        lib2_target.build_target,
    ]) as d:
        config = get_config(d)

        found = set(list_test_cases_in_test_suites([lib2_target.generic_test_suite_target], config.debug_build_dir))
        correct = {
            lib2_target.get_test_case('call_lib2'),
            lib2_target.get_test_case('other_lib2'),
        }

        assert found == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_test_all() -> None:
    with cmade_project_instance() as d:
        cmd = [
            'test',
            '-j1',
        ]
        check_cmd_succeeds(d, cmd)

        for fail_key in [
            'PROJ_TESTS_FAIL_LIB1_CALL_LIB1',
            'PROJ_TESTS_FAIL_LIB1_OTHER_LIB1',
            'PROJ_TESTS_FAIL_LIB2_CALL_LIB2',
            'PROJ_TESTS_FAIL_LIB2_OTHER_LIB2',
        ]:
            check_cmd_fails(d, cmd, env={
                fail_key: 'y'
            })

@pytest.mark.e2e
@pytest.mark.slow
def test_test_all_with_coverage() -> None:
    with cmade_project_instance() as d:
        cmd = [
            'test',
            '-j1',
            '--coverage',
        ]
        check_cmd_succeeds(d, cmd)

        for fail_key in [
            'PROJ_TESTS_FAIL_LIB1_CALL_LIB1',
            'PROJ_TESTS_FAIL_LIB1_OTHER_LIB1',
            'PROJ_TESTS_FAIL_LIB2_CALL_LIB2',
            'PROJ_TESTS_FAIL_LIB2_OTHER_LIB2',
        ]:
            check_cmd_fails(d, cmd, env={
                fail_key: 'y'
            })

@pytest.mark.e2e
@pytest.mark.slow
def test_test_test_suite() -> None:
    with cmade_project_instance() as d:
        cmd = [
            'test',
            '-j1',
            'lib2',
        ]

        check_cmd_succeeds(d, cmd)
        check_cmd_succeeds(d, cmd, env={
            'PROJ_TESTS_FAIL_LIB1_CALL_LIB1': 'y',
            'PROJ_TESTS_FAIL_LIB1_OTHER_LIB1': 'y',
        })
        for fail_key in [
            'PROJ_TESTS_FAIL_LIB2_CALL_LIB2',
            'PROJ_TESTS_FAIL_LIB2_OTHER_LIB2',
        ]:
            check_cmd_fails(d, cmd, env={
                fail_key: 'y',
            })

@pytest.mark.e2e
@pytest.mark.slow
def test_test_test_case() -> None:
    with cmade_project_instance() as d:
        cmd = [
            'test',
            '-j1',
            'lib2:call_lib2',
        ]

        check_cmd_succeeds(d, cmd)
        check_cmd_succeeds(d, cmd, env={
            'PROJ_TESTS_FAIL_LIB1_CALL_LIB1': 'y',
            'PROJ_TESTS_FAIL_LIB1_OTHER_LIB1': 'y',
            'PROJ_TESTS_FAIL_LIB2_OTHER_LIB2': 'y',
        })
        check_cmd_fails(d, cmd, env={
            'PROJ_TESTS_FAIL_LIB2_CALL_LIB2': 'y',
        })

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(
    nclib is None,
    reason="requires nclib",
)
def test_test_test_case_debug() -> None:
    with cmade_project_instance() as d:
        def cmd_succeeds(env: Mapping[str, str]) -> bool:
            p = nclib.Process(
                [
                    'proj',
                    'test',
                    '-j1',
                    '--debug',
                    'lib2:call_lib2',
                ],
                cwd=d,
                verbose=True,
                env={**os.environ, **env},
            )

            p.recv_until('(gdb) ')
            p.sendline('r')
            p.recv_until(') exited normally]', timeout=1.0)
            exited_normally = not p.timed_out
            p.kill()
            return exited_normally

        assert cmd_succeeds({
            'PROJ_TESTS_FAIL_LIB1_CALL_LIB1': 'y',
            'PROJ_TESTS_FAIL_LIB1_OTHER_LIB1': 'y',
            'PROJ_TESTS_FAIL_LIB2_OTHER_LIB2': 'y',
        })
        assert not cmd_succeeds({
            'PROJ_TESTS_FAIL_LIB2_CALL_LIB2': 'y',
        })

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
        check_cmd_fails(d, [
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
            'lib1:benchmarks:example_benchmark'
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
        check_cmd_fails(d, [
            'benchmark',
            '-j1',
            'lib1',
        ], env={
            'PROJ_TESTS_FAIL_LIB1_BENCHMARK_BUDGET': 'y',
        })

@pytest.mark.e2e
@pytest.mark.slow
def test_benchmark_case() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'benchmark',
            '-j1',
            'lib1:example_benchmark',
        ])
        check_cmd_fails(d, [
            'benchmark',
            '-j1',
            'lib1:example_benchmark',
        ], env={
            'PROJ_TESTS_FAIL_LIB1_BENCHMARK_BUDGET': 'y',
        })

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
        check_cmd_fails(d, [
            'profile',
            '-j1',
            'lib1:benchmarks'
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_profile_benchmark_case_callgrind() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            'lib1:benchmarks:example_benchmark'
        ]))

        assert Path(result.stdout.splitlines()[-1]).is_file()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
@pytest.mark.xdist_group(name="perf")
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
@pytest.mark.xdist_group(name="perf")
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
@pytest.mark.xdist_group(name="perf")
def test_profile_benchmark_suite_perf() -> None:
    with cmade_project_instance() as d:
        check_cmd_fails(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:benchmarks'
        ])

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.no_sandbox
@pytest.mark.xdist_group(name="perf")
def test_profile_benchmark_case_perf() -> None:
    with cmade_project_instance() as d:
        result = require_successful(run(d, [
            'profile',
            '-j1',
            '--tool',
            'perf',
            'lib1:benchmarks:example_benchmark'
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
        check_cmd_fails(d, [
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
            'lib1:benchmarks:example_benchmark'
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
def test_check_cpu_ci_requires_formatting_to_pass() -> None:
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
def test_check_cpu_ci_requires_binaries_to_build() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], {
            'CXXFLAGS': '-DBIN1_FAIL_BUILD',
        })
        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci_requires_libraries_to_build() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], {
            'CXXFLAGS': '-DLIB1_FAIL_BUILD',
        })
        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci_requires_library_tests_to_build() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], {
            'CXXFLAGS': '-DLIB1_TESTS_FAIL_BUILD',
        })
        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_cpu_ci_requires_library_benchmarks_to_build() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'format',
        ])
        check_cmd_fails(d, [
            'check',
            'cpu-ci',
        ], {
            'CXXFLAGS': '-DLIB1_BENCHMARKS_FAIL_BUILD',
        })
        check_cmd_succeeds(d, [
            'check',
            'cpu-ci',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_config_subcommand() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'config',
        ]))

        out = json.loads(result.stdout)
        assert out == {
            'namespace_name': 'TestProject',
            'testsuite_macro': 'TP_TEST_SUITE',
            'header_extension': '.h',
        }


LIB1_QUERY_JSON_OUTPUT = {
    'public_header': 'lib/lib1/include/lib1/lib1.h',
    'generated_header': 'lib/lib1/include/lib1/lib1.dtg.h',
    'source': 'lib/lib1/src/lib1/lib1.cc',
    'generated_source': 'lib/lib1/src/lib1/lib1.dtg.cc',
    'test_source': 'lib/lib1/test/src/lib1/lib1.cc',
    'benchmark_header': 'lib/lib1/benchmark/include/benchmark/lib1/lib1.h',
    'benchmark_source': 'lib/lib1/benchmark/src/benchmark/lib1/lib1.cc',
    'toml_path': 'lib/lib1/include/lib1/lib1.dtg.toml',
    'ifndef': '_TEST_PROJECT_1_LIB_LIB1_INCLUDE_LIB1_LIB1_H',
    'generated_include': 'lib1/lib1.dtg.h',
    'include': 'lib1/lib1.h',
}

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_header() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/include/lib1/lib1.h',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'hdr',
            **LIB1_QUERY_JSON_OUTPUT,
        }
        assert out == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_src() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/src/lib1/lib1.cc',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'src',
            **LIB1_QUERY_JSON_OUTPUT,
        }
        assert out == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_src() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/test/src/lib1/lib1.cc',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'tst',
            **LIB1_QUERY_JSON_OUTPUT,
        }
        assert out == correct

LIB1_TOML_QUERY_JSON_OUTPUT = {
    'public_header': 'lib/lib1/include/lib1/example_struct.h',
    'generated_header': 'lib/lib1/include/lib1/example_struct.dtg.h',
    'source': 'lib/lib1/src/lib1/example_struct.cc',
    'generated_source': 'lib/lib1/src/lib1/example_struct.dtg.cc',
    'test_source': 'lib/lib1/test/src/lib1/example_struct.cc',
    'benchmark_header': 'lib/lib1/benchmark/include/benchmark/lib1/example_struct.h',
    'benchmark_source': 'lib/lib1/benchmark/src/benchmark/lib1/example_struct.cc',
    'toml_path': 'lib/lib1/include/lib1/example_struct.dtg.toml',
    'ifndef': '_TEST_PROJECT_1_LIB_LIB1_INCLUDE_LIB1_EXAMPLE_STRUCT_H',
    'generated_include': 'lib1/example_struct.dtg.h',
    'include': 'lib1/example_struct.h',
}

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_toml() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/include/lib1/example_struct.dtg.toml',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'toml',
            **LIB1_TOML_QUERY_JSON_OUTPUT,
        }

        assert out == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_toml_generated_header() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/include/lib1/example_struct.dtg.h',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'genhdr',
            **LIB1_TOML_QUERY_JSON_OUTPUT,
        }

        assert out == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_toml_generated_source() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/src/lib1/example_struct.dtg.cc',
        ]))

        out = json.loads(result.stdout)
        correct = {
            'role': 'gensrc',
            **LIB1_TOML_QUERY_JSON_OUTPUT,
        }

        assert out == correct

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_toml_variant() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/include/lib1/example_variant.h',
        ]))

        out = json.loads(result.stdout)

        assert out == {
            'public_header': 'lib/lib1/include/lib1/example_variant.h',
            'generated_header': 'lib/lib1/include/lib1/example_variant.dtg.h',
            'source': 'lib/lib1/src/lib1/example_variant.cc',
            'generated_source': 'lib/lib1/src/lib1/example_variant.dtg.cc',
            'test_source': 'lib/lib1/test/src/lib1/example_variant.cc',
            'benchmark_header': 'lib/lib1/benchmark/include/benchmark/lib1/example_variant.h',
            'benchmark_source': 'lib/lib1/benchmark/src/benchmark/lib1/example_variant.cc',
            'toml_path': 'lib/lib1/include/lib1/example_variant.dtg.toml',
            'ifndef': '_TEST_PROJECT_1_LIB_LIB1_INCLUDE_LIB1_EXAMPLE_VARIANT_H',
            'generated_include': 'lib1/example_variant.dtg.h',
            'include': 'lib1/example_variant.h',
            'role': 'hdr',
        }

@pytest.mark.e2e
@pytest.mark.slow
def test_query_path_for_test_toml_enum() -> None:
    with project_instance() as d:
        result = require_successful(run(d, [
            'query-path',
            './lib/lib1/include/lib1/example_enum.h',
        ]))

        out = json.loads(result.stdout)

        assert out == {
            'public_header': 'lib/lib1/include/lib1/example_enum.h',
            'generated_header': 'lib/lib1/include/lib1/example_enum.dtg.h',
            'source': 'lib/lib1/src/lib1/example_enum.cc',
            'generated_source': 'lib/lib1/src/lib1/example_enum.dtg.cc',
            'test_source': 'lib/lib1/test/src/lib1/example_enum.cc',
            'benchmark_header': 'lib/lib1/benchmark/include/benchmark/lib1/example_enum.h',
            'benchmark_source': 'lib/lib1/benchmark/src/benchmark/lib1/example_enum.cc',
            'toml_path': 'lib/lib1/include/lib1/example_enum.dtg.toml',
            'ifndef': '_TEST_PROJECT_1_LIB_LIB1_INCLUDE_LIB1_EXAMPLE_ENUM_H',
            'generated_include': 'lib1/example_enum.dtg.h',
            'include': 'lib1/example_enum.h',
            'role': 'hdr',
        }

@pytest.mark.e2e
@pytest.mark.slow
def test_rm() -> None:
    with project_instance() as d:
        target_path = Path('./lib/lib1/include/lib1/example_enum.h')
        target_cc_path = Path('./lib/lib1/src/lib1/example_enum.cc')
        target_test_path = Path('./lib/lib1/test/src/lib1/example_enum.cc')
        target_toml_path = Path('./lib/lib1/include/lib1/example_enum.dtg.toml')
        non_target_path = Path('./lib/lib1/include/lib1/example_variant.dtg.toml')

        all_test_paths = [
            target_path,
            target_cc_path,
            target_test_path,
            target_toml_path,
            non_target_path,
        ]

        for target_p in all_test_paths:
            assert (d / target_p).is_file()

        pre_contents = {
            p: (d / p).read_bytes() for p in all_test_paths
        }

        def check_removed(src: Path) -> None:
            assert not (d / src).is_file()

        def check_not_removed(p: Path) -> None:
            assert (d / p).is_file()
            assert (d / p).read_bytes() == pre_contents[p]

        require_successful(run(d, [
            'rm',
            str(target_path),
        ]))

        check_removed(target_path)
        check_removed(target_cc_path)
        check_removed(target_test_path)
        check_removed(target_toml_path)
        check_not_removed(non_target_path)

@pytest.mark.e2e
@pytest.mark.slow
def test_rm_dry_run() -> None:
    with project_instance() as d:
        target_path = Path('./lib/lib1/include/lib1/example_enum.h')
        target_cc_path = Path('./lib/lib1/src/lib1/example_enum.cc')
        target_test_path = Path('./lib/lib1/test/src/lib1/example_enum.cc')
        target_toml_path = Path('./lib/lib1/include/lib1/example_enum.dtg.toml')
        non_target_path = Path('./lib/lib1/include/lib1/example_variant.dtg.toml')

        all_test_paths = [
            target_path,
            target_cc_path,
            target_test_path,
            target_toml_path,
            non_target_path,
        ]

        for target_p in all_test_paths:
            assert (d / target_p).is_file()

        pre_contents = {
            p: (d / p).read_bytes() for p in all_test_paths
        }

        def check_removed(p: Path) -> None:
            assert not (d / p).is_file()

        def check_not_removed(p: Path) -> None:
            assert (d / p).is_file()
            assert (d / p).read_bytes() == pre_contents[p]

        require_successful(run(d, [
            'rm',
            '-n',
            str(target_path),
        ]))

        check_not_removed(target_path)
        check_not_removed(target_cc_path)
        check_not_removed(target_test_path)
        check_not_removed(target_toml_path)
        check_not_removed(non_target_path)


@pytest.mark.e2e
@pytest.mark.slow
def test_move() -> None:
    with project_instance() as d:
        src_path = Path('./lib/lib1/include/lib1/example_enum.h')
        src_cc_path = Path('./lib/lib1/src/lib1/example_enum.cc')
        src_test_path = Path('./lib/lib1/test/src/lib1/example_enum.cc')
        src_toml_path = Path('./lib/lib1/include/lib1/example_enum.dtg.toml')
        all_src_paths = [
            src_path,
            src_cc_path,
            src_test_path,
            src_toml_path,
        ]

        dst_path = Path('./lib/lib1/include/lib1/example_enum_moved.h')
        dst_cc_path = Path('./lib/lib1/src/lib1/example_enum_moved.cc')
        dst_test_path = Path('./lib/lib1/test/src/lib1/example_enum_moved.cc')
        dst_toml_path = Path('./lib/lib1/include/lib1/example_enum_moved.dtg.toml')

        for src_p in all_src_paths:
            assert (d / src_p).is_file()

        pre_contents = {
            p: (d / p).read_bytes() for p in all_src_paths
        }

        def check_moved(src: Path, dst: Path) -> None:
            assert not (d / src).is_file()
            assert (d / dst).is_file()
            assert (d / dst).read_bytes() == pre_contents[src]

        require_successful(run(d, [
            'mv',
            '--skip-update-includes',
            '--skip-update-ifndefs',
            str(src_path),
            str(dst_path),
        ]))

        check_moved(src_path, dst_path)
        check_moved(src_cc_path, dst_cc_path)
        check_moved(src_test_path, dst_test_path)
        check_moved(src_toml_path, dst_toml_path)

@pytest.mark.e2e
@pytest.mark.slow
def test_move_to_directory() -> None:
    with project_instance() as d:
        src_hdr_path = Path('./lib/lib1/include/lib1/example_enum.h')
        src_cc_path = Path('./lib/lib1/src/lib1/example_enum.cc')
        src_test_path = Path('./lib/lib1/test/src/lib1/example_enum.cc')
        src_toml_path = Path('./lib/lib1/include/lib1/example_enum.dtg.toml')
        all_src_paths = [
            src_hdr_path,
            src_cc_path,
            src_test_path,
            src_toml_path,
        ]

        dst_hdr_path = Path('./lib/lib2/include/lib2/example_enum.h')
        dst_cc_path = Path('./lib/lib2/src/lib2/example_enum.cc')
        dst_test_path = Path('./lib/lib2/test/src/lib2/example_enum.cc')
        dst_toml_path = Path('./lib/lib2/include/lib2/example_enum.dtg.toml')

        for src_p in all_src_paths:
            assert (d / src_p).is_file()

        pre_contents = {
            p: (d / p).read_bytes() for p in all_src_paths
        }

        def check_moved(src: Path, dst: Path) -> None:
            assert not (d / src).is_file()
            assert (d / dst).is_file()
            assert (d / dst).read_bytes() == pre_contents[src]

        require_successful(run(d, [
            'mv',
            '--skip-update-includes',
            '--skip-update-ifndefs',
            str(src_hdr_path),
            str(dst_hdr_path.parent),
        ]))

        check_moved(src_hdr_path, dst_hdr_path)
        check_moved(src_cc_path, dst_cc_path)
        check_moved(src_test_path, dst_test_path)
        check_moved(src_toml_path, dst_toml_path)

@pytest.mark.e2e
@pytest.mark.slow
def test_move_dry_run() -> None:
    with project_instance() as d:
        src_path = Path('./lib/lib1/include/lib1/example_enum.h')
        src_cc_path = Path('./lib/lib1/src/lib1/example_enum.cc')
        src_test_path = Path('./lib/lib1/test/src/lib1/example_enum.cc')
        src_toml_path = Path('./lib/lib1/include/lib1/example_enum.dtg.toml')
        all_src_paths = [
            src_path,
            src_cc_path,
            src_test_path,
            src_toml_path,
        ]

        dst_path = Path('./lib/lib1/include/lib1/example_enum_moved.h')
        dst_cc_path = Path('./lib/lib1/src/lib1/example_enum_moved.cc')
        dst_test_path = Path('./lib/lib1/test/src/lib1/example_enum_moved.cc')
        dst_toml_path = Path('./lib/lib1/include/lib1/example_enum_moved.dtg.toml')

        for src_p in all_src_paths:
            assert (d / src_p).is_file()

        pre_contents = {
            p: (d / p).read_bytes() for p in all_src_paths
        }

        def check_not_moved(src: Path, dst: Path) -> None:
            assert (d / src).is_file()
            assert not (d / dst).is_file()
            assert (d / src).read_bytes() == pre_contents[src]

        require_successful(run(d, [
            'mv',
            '-n',
            str(src_path),
            str(dst_path),
        ]))

        check_not_moved(src_path, dst_path)
        check_not_moved(src_cc_path, dst_cc_path)
        check_not_moved(src_test_path, dst_test_path)
        check_not_moved(src_toml_path, dst_toml_path)

@pytest.mark.e2e
@pytest.mark.slow
def test_move_dry_run_does_not_fail_if_tree_contains_nontext_files() -> None:
    with project_instance() as d:
        src_path = Path('./lib/lib1/include/lib1/example_enum.h')
        dst_path = Path('./lib/lib1/include/lib1/example_enum_moved.h')

        (d / 'lib/lib1/include/lib1/.something_bad.cc.swp').write_bytes(
            b'\xff\xff\x00\x05',
        )

        require_successful(run(d, [
            'mv',
            '-n',
            str(src_path),
            str(dst_path),
        ]))


@pytest.mark.e2e
@pytest.mark.slow
def test_check_layout() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'layout',
        ])

        (d / 'lib/lib1/src/lib1/example_enum.cc').unlink()

        check_cmd_fails(d, [
            'check',
            'layout',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_ifndef() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'ifndef',
        ])

        lib2_header_path = d / 'lib/lib2/include/lib2/lib2.h'
        lib2_header_contents = lib2_header_path.read_text()
        modified = lib2_header_contents.replace('_TEST_PROJECT_1_LIB_LIB2_INCLUDE_LIB2_LIB2_H', '_SOME_OTHER_IFNDEF_H')
        assert lib2_header_contents != modified, "Contents not changed. This test probably needs to be updated!"
        lib2_header_path.write_text(modified)

        check_cmd_fails(d, [
            'check',
            'ifndef',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_move_with_ifndef_fix() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'ifndef',
        ])

        src_path = Path('./lib/lib1/include/lib1/example_enum.h')
        dst_path = Path('./lib/lib1/include/lib1/example_enum_moved.h')

        require_successful(run(d, [
            'mv',
            '--skip-update-ifndefs',
            str(src_path),
            str(dst_path),
        ]))

        check_cmd_fails(d, [
            'check',
            'ifndef',
        ])

        dst2_path = Path('./lib/lib1/include/lib1/example_enum_moved_again.h')

        require_successful(run(d, [
            'mv',
            str(dst_path),
            str(dst2_path),
        ]))

        check_cmd_succeeds(d, [
            'check',
            'ifndef',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_check_include() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'include',
        ])

        lib2_src_path = d / 'lib/lib2/src/lib2/lib2.cc'
        lib2_src_contents = lib2_src_path.read_text()
        modified = lib2_src_contents.replace('#include "lib2/lib2.h"', '#include "lib2/lib3.h"')
        assert lib2_src_contents != modified, "Contents not changed. This test probably needs to be updated!"
        lib2_src_path.write_text(modified)

        check_cmd_fails(d, [
            'check',
            'include',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_move_with_include_fix() -> None:
    src_path = Path('./lib/lib1/include/lib1/example_enum.h')
    dst_path = Path('./lib/lib1/include/lib1/example_enum_moved.h')

    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'include',
        ])

        require_successful(run(d, [
            'mv',
            '--skip-update-includes',
            str(src_path),
            str(dst_path),
        ]))

        check_cmd_fails(d, [
            'check',
            'include',
        ])

    with project_instance() as d:
        check_cmd_succeeds(d, [
            'check',
            'include',
        ])

        require_successful(run(d, [
            'mv',
            str(src_path),
            str(dst_path),
        ]))

        check_cmd_succeeds(d, [
            'check',
            'include',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_find_include() -> None:
    with project_instance() as d:
        check_cmd_succeeds(d, [
            'find-include',
            'lib1/example_enum.h',
        ])

        check_cmd_fails(d, [
            'find-include',
            'lib1/something_that_does_not_exist.h',
        ])

@pytest.mark.e2e
@pytest.mark.slow
def test_tag_cmd() -> None:
    with project_instance() as d:
        TAG_FILE_PATH = d / 'tags'
        assert not TAG_FILE_PATH.exists()

        check_cmd_succeeds(d, [
            'tag',
        ])

        assert TAG_FILE_PATH.is_file()
        contents = TAG_FILE_PATH.read_text()
        assert 'ExampleEnum' in contents
        assert 'lib/lib1/include/lib1/example_enum.dtg.toml' in contents

        def is_sorted(l: List[str]) -> bool:
            return all(a <= b for a, b in zip(l, l[1:]))

        lines = contents.splitlines()
        assert is_sorted(lines)

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skip
def test_lint() -> None:
    with cmade_project_instance() as d:
        check_cmd_succeeds(d, [
            'lint',
        ])
