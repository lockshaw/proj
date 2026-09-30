import pytest
from proj.config_file import (
    load_parsed_config,
    ConfigKey,
    ProjectConfig,
)
from proj.targets import (
    BenchmarkCaseTarget,
    BenchmarkSuiteTarget,
)
from proj.utils import (
    with_suffix_appended,
    with_suffixes,
)
from typing import (
    Dict,
    Any,
)
from pathlib import Path, PurePath
import dataclasses
from proj.paths import Repo

def get_example_config() -> Dict[str, Any]:
    return {
        ConfigKey.PROJECT_NAME: 'test',
        ConfigKey.TARGETS: {},
        ConfigKey.DEFAULT_BIN_TARGETS: [],
        ConfigKey.DEFAULT_TEST_TARGETS: [],
        ConfigKey.DEFAULT_BENCHMARK_TARGETS: [],
        ConfigKey.TESTSUITE_MACRO: 'MY_MACRO',
        ConfigKey.IFNDEF_NAME: 'MY_IFNDEF',
        ConfigKey.NAMESPACE_NAME: 'MyNamespace',
        ConfigKey.CMAKE_FLAGS_EXTRA: {},
        ConfigKey.CMAKE_REQUIRE_SHELL: False,
        ConfigKey.HEADER_EXTENSION: '.hhh',
        ConfigKey.FIX_COMPILE_COMMANDS: False,
        ConfigKey.TEST_HEADER_PATH: '/example/test/header/path.h',
        ConfigKey.CUDA_LAUNCH_CMD: ['a', 'b'],
        ConfigKey.LAYOUT_IGNORE_PATHS: [
            '/example/ignore/me.h',
            '/example/ignore_us/',
        ],
        ConfigKey.BENCHMARKS: {
            'a': [
                {
                    'name': 'hello',
                    'budget': 50,
                },
            ],
            'b': [
                {
                    'name': 'bye',
                    'budget': 25,
                },
                {
                    'name': 'goodbye',
                    'budget': 30,
                },
            ],
        },
    }

REPO = Repo(PurePath('/config/root'))

LOADED_CONFIG = ProjectConfig(
    project_name='test',
    base=Path(REPO.path),
    _targets={},
    _default_build_targets=tuple(),
    _default_test_targets=tuple(),
    _default_benchmark_targets=tuple(),
    _testsuite_macro='MY_MACRO',
    _ifndef_name='MY_IFNDEF',
    _namespace_name='MyNamespace',
    _cmake_flags_extra={},
    _cmake_require_shell=False,
    _header_extension='.hhh',
    _fix_compile_commands=False,
    _test_header_path=Path('/example/test/header/path.h'),
    _cuda_launch_cmd=('a', 'b'),
    _layout_ignore_paths=(
        Path('/example/ignore/me.h'),
        Path('/example/ignore_us/'),
    ),
    _benchmark_instruction_budgets={
        BenchmarkCaseTarget(BenchmarkSuiteTarget('a'), 'hello'): 50,
        BenchmarkCaseTarget(BenchmarkSuiteTarget('b'), 'bye'): 25,
        BenchmarkCaseTarget(BenchmarkSuiteTarget('b'), 'goodbye'): 30,
    },
)

def test_load_parsed_config_loads_complete_value() -> None:
    loaded = load_parsed_config(
        repo=REPO,
        raw=get_example_config(),
    )

    assert loaded == LOADED_CONFIG

def test_load_parsed_config_loads_when_missing_optional_field() -> None:
    raw = get_example_config()
    del raw[ConfigKey.HEADER_EXTENSION]

    loaded = load_parsed_config(
        repo=REPO,
        raw=raw,
    )

    correct = dataclasses.replace(LOADED_CONFIG, _header_extension=None)

    assert loaded == correct

def test_load_parsed_config_fails_to_load_config_with_extra_key() -> None:
    raw = get_example_config()
    raw['some_other_key'] = True

    with pytest.raises(Exception):
        load_parsed_config(
            repo=REPO,
            raw=raw,
        )

def test_load_parsed_config_fails_to_load_when_missing_required_field() -> None:
    raw = get_example_config()
    del raw[ConfigKey.PROJECT_NAME]

    with pytest.raises(Exception):
        load_parsed_config(
            repo=REPO,
            raw=raw,
        )

def test_with_suffix_appended() -> None:
    assert with_suffix_appended(
        Path('/hello/world.h'),
        '.dtg.toml',
    ) == Path('/hello/world.h.dtg.toml')

    assert with_suffix_appended(
        Path('/hello/world.struct.h'),
        '.yo',
    ) == Path('/hello/world.struct.h.yo')

def test_with_suffixes() -> None:
    assert with_suffixes(
        Path('/hello/world.h'),
        '.dtg.toml',
    ) == Path('/hello/world.dtg.toml')

    assert with_suffixes(
        Path('/hello/world.struct.h'),
        '.yo',
    ) == Path('/hello/world.yo')
