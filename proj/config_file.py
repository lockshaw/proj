from pathlib import Path
from dataclasses import dataclass
from typing import (
    Optional,
    Mapping,
    Tuple,
    Union,
    FrozenSet,
    Dict,
)
import string
import re
import proj.toml as toml
from .targets import (
    BuildTarget,
    CpuTestCaseTarget,
    CpuTestSuiteTarget,
    CudaTestCaseTarget,
    CudaTestSuiteTarget,
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
    LibTarget,
    GenericTestCaseTarget,
    GenericTestSuiteTarget,
    ConfiguredNames,
    CpuBinTarget,
    CudaBinTarget,
    GenericBinTarget,
    MixedTestSuiteTarget,
    CpuRunTarget,
    CudaRunTarget,
    parse_generic_test_target,
    parse_generic_benchmark_target,
)
import logging
from .utils import (
    map_optional,
)
from .json import (
    Json,
    require_str,
    require_bool,
    require_list_of,
    require_dict_of,
    require_int,
    require_not_none,
)
from proj.strenum import StrEnum
from .paths import (
    Repo,
)
from .trees import FileTree

_l = logging.getLogger(__name__)

def load_str_tuple(x: object) -> Optional[Tuple[str, ...]]:
    return map_optional(
        map_optional(x, lambda l: require_list_of(l, require_str)), lambda ll: tuple(ll)
    )

@dataclass(frozen=True)
class ExtensionConfig:
    header_extension: str
    src_extension: str

    def __post_init__(self) -> None:
        assert self.header_extension.startswith('.')
        assert self.src_extension.startswith('.')

@dataclass(frozen=True, order=True)
class LibConfig:
    has_cpu_only_test_suite: bool
    has_cuda_test_suite: bool
    has_cpu_only_benchmark_suite: bool
    has_cuda_benchmark_suite: bool

class BenchmarkConfigKeys(StrEnum):
    NAME = 'name'
    INSTRUCTION_BUDGET = 'budget'

def _load_benchmarks(m: object) -> Mapping[BenchmarkCaseTarget, int]:
    assert isinstance(m, dict)

    result = {}
    for suite, benchmark_cases in m.items():
        assert isinstance(benchmark_cases, list), repr(benchmark_cases)
        for benchmark_case in benchmark_cases:
            assert isinstance(benchmark_case, dict)

            assert set(benchmark_case.keys()) == set(BenchmarkConfigKeys)

            _benchmark_case = BenchmarkCaseTarget(
                benchmark_suite=BenchmarkSuiteTarget(suite),
                case_name=require_str(benchmark_case[BenchmarkConfigKeys.NAME]),
            )

            _budget = require_int(benchmark_case[BenchmarkConfigKeys.INSTRUCTION_BUDGET])

            result[_benchmark_case] = _budget

    return result


def get_test_target(
    lib_name: str, lib_config: LibConfig
) -> Union[CpuTestSuiteTarget, CudaTestSuiteTarget]:
    assert lib_config.has_cpu_only_test_suite or lib_config.has_cuda_test_suite

    if lib_config.has_cuda_test_suite:
        return LibTarget(lib_name).cuda_test_target
    else:
        return LibTarget(lib_name).cpu_test_target


@dataclass(frozen=True, order=True)
class BinConfig:
    requires_cuda: bool

class BuildTool(StrEnum):
    MAKE = 'make'
    NINJA = 'ninja'

@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    base: Path
    _targets: Mapping[str, Union[LibConfig, BinConfig]]
    _doxygen: Optional[bool] = None
    _default_build_targets: Optional[Tuple[str, ...]] = None
    _default_test_targets: Optional[Tuple[str, ...]] = None
    _default_benchmark_targets: Optional[Tuple[str, ...]] = None
    _ifndef_name: Optional[str] = None
    _namespace_name: Optional[str] = None
    _testsuite_macro: Optional[str] = None
    _cmake_flags_extra: Optional[Mapping[str, str]] = None
    _coverage_cmake_flags_extra: Optional[Mapping[str, str]] = None
    _benchmark_cmake_flags_extra: Optional[Mapping[str, str]] = None
    _cmake_require_shell: Optional[bool] = None
    _header_extension: Optional[str] = None
    _fix_compile_commands: Optional[bool] = None
    _test_header_path: Optional[Path] = None
    _cuda_launch_cmd: Optional[Tuple[str, ...]] = None
    _layout_ignore_paths: Optional[Tuple[Path, ...]] = None
    _build_tool: Optional[BuildTool] = None
    _test_case_timeout_seconds: Optional[int] = None
    _benchmark_timeout_seconds: Optional[int] = None
    _benchmark_instruction_budgets: Optional[Mapping[BenchmarkCaseTarget, int]] = None

    @property
    def repo(self) -> Repo:
        return Repo(self.base)

    @property
    def doxygen_enabled(self) -> bool:
        if self._doxygen is None:
            return False
        else:
            return self._doxygen

    @property
    def build_tool(self) -> BuildTool:
        if self._build_tool is None:
            return BuildTool.NINJA
        else:
            return self._build_tool

    @property
    def debug_build_dir(self) -> Path:
        return self.base / "build/normal"

    @property
    def release_build_dir(self) -> Path:
        return self.base / "build/release"

    @property
    def coverage_build_dir(self) -> Path:
        return self.base / "build/coverage"

    @property
    def doxygen_dir(self) -> Path:
        return self.base / "build/doxygen"

    @property
    def bin_names(self) -> Mapping[str, BinConfig]:
        return {
            target_name: target_config
            for target_name, target_config in sorted(self._targets.items())
            if isinstance(target_config, BinConfig)
        }

    @property
    def bin_targets(self) -> FrozenSet[Union[CpuBinTarget, CudaBinTarget]]:
        return frozenset(
            CudaBinTarget(GenericBinTarget(bin_name))
            if conf.requires_cuda
            else CpuBinTarget(GenericBinTarget(bin_name))
            for bin_name, conf in self.bin_names.items()
        )

    @property
    def lib_names(self) -> Mapping[str, LibConfig]:
        return {
            target_name: target_config
            for target_name, target_config in sorted(self._targets.items())
            if isinstance(target_config, LibConfig)
        }

    @property
    def lib_targets(self) -> Mapping[LibTarget, LibConfig]:
        return {LibTarget(k): v for k, v in self.lib_names.items()}

    @property
    def configured_names(self) -> ConfiguredNames:
        return ConfiguredNames(
            bin_names=set(self.bin_names),
            lib_names=set(self.lib_names.keys()),
        )

    @property
    def all_build_targets(self) -> Tuple[BuildTarget, ...]:
        return tuple([
            *[t.build_target for t in self.all_test_targets],
            *[t.build_target for t in self.lib_targets],
            *[t.build_target for t in self.bin_targets],
            *[t.build_target for t in self.all_benchmark_targets],
        ])

    @property
    def default_build_targets(self) -> Tuple[BuildTarget, ...]:
        if self._default_build_targets is None:
            return self.all_build_targets
        else:
            return tuple(
                BuildTarget.from_str(self.configured_names, s)
                for s in self._default_build_targets
            )

    @property
    def all_test_targets(
        self,
    ) -> FrozenSet[
        Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]
    ]:
        return self.all_cpu_test_targets | self.all_cuda_test_targets

    @property
    def all_cpu_test_targets(self) -> FrozenSet[CpuTestSuiteTarget]:
        return frozenset(
            [
                lib.cpu_test_target
                for lib, conf in self.lib_targets.items()
                if conf.has_cpu_only_test_suite
            ]
        )

    @property
    def all_cuda_test_targets(self) -> FrozenSet[CudaTestSuiteTarget]:
        return frozenset(
            [
                lib.cuda_test_target
                for lib, conf in sorted(self.lib_targets.items())
                if conf.has_cuda_test_suite
            ]
        )

    @property
    def default_test_targets(
        self,
    ) -> FrozenSet[
        Union[
            MixedTestSuiteTarget,
            CpuTestSuiteTarget,
            CudaTestSuiteTarget,
            CpuTestCaseTarget,
            CudaTestCaseTarget,
            GenericTestCaseTarget,
        ]
    ]:
        if self._default_test_targets is None:
            return self.all_test_targets
        else:
            return frozenset(
                [
                    resolve_test_target(self, parse_generic_test_target(s))
                    for s in self._default_test_targets
                ]
            )

    def lib_has_cpu_only_test_suite(self, lib: LibTarget) -> bool:
        return self.lib_targets[lib].has_cpu_only_test_suite

    def lib_has_cuda_test_suite(self, lib: LibTarget) -> bool:
        return self.lib_targets[lib].has_cuda_test_suite

    def test_suite_for_lib(
        self, lib: LibTarget
    ) -> Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]:
        lib_config = self.lib_targets[lib]
        assert lib_config.has_cpu_only_test_suite or lib_config.has_cuda_test_suite

        if lib_config.has_cuda_test_suite and lib_config.has_cpu_only_test_suite:
            return lib.mixed_test_target
        elif lib_config.has_cpu_only_test_suite:
            return lib.cpu_test_target
        else:
            assert lib_config.has_cuda_test_suite
            return lib.cuda_test_target

    @property
    def benchmark_instruction_budgets(
        self,
    ) -> Mapping[BenchmarkCaseTarget, int]:
        if self._benchmark_instruction_budgets is None:
            return {}
        else:
            return self._benchmark_instruction_budgets

    def lookup_instruction_budget_for_benchmark(
        self,
        benchmark: BenchmarkCaseTarget,
    ) -> int:
        return self.benchmark_instruction_budgets[benchmark]

    @property
    def all_benchmark_targets(
        self,
    ) -> FrozenSet[BenchmarkSuiteTarget]:
        return frozenset([
            lib.benchmark_target for lib, conf in self.lib_targets.items()
            if conf.has_cpu_only_benchmark_suite
        ])

    @property
    def default_benchmark_targets(
        self,
    ) -> FrozenSet[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]]:
        if self._default_benchmark_targets is None:
            return self.all_benchmark_targets
        else:
            return frozenset(
                [
                    parse_generic_benchmark_target(s)
                    for s in self._default_benchmark_targets
                ]
            )

    @property
    def ifndef_name(self) -> str:
        if self._ifndef_name is None:
            result = re.sub(r"[^a-zA-Z0-9_]", "_", self.project_name).upper()
        else:
            result = self._ifndef_name
        allowed = set(string.ascii_uppercase + string.digits + "_")
        assert all(c in allowed for c in result)
        return result

    @property
    def namespace_name(self) -> str:
        if self._namespace_name is None:
            result = self.project_name
        else:
            result = self._namespace_name
        allowed = set(string.ascii_uppercase + string.ascii_lowercase + "_")
        assert all(c in set(allowed) for c in result)
        return result

    @property
    def testsuite_macro(self) -> str:
        if self._testsuite_macro is None:
            return f"{self.ifndef_name}_TEST_SUITE"
        else:
            return self._testsuite_macro

    @property
    def base_cmake_flags(self) -> Mapping[str, str]:
        if self._cmake_flags_extra is None:
            extra: Mapping[str, str] = {}
        else:
            extra = self._cmake_flags_extra
        return {
            **extra,
            "CMAKE_CXX_COMPILER_LAUNCHER": "ccache",
        }

    @property
    def debug_cmake_flags(self) -> Mapping[str, str]:
        return {
            **self.base_cmake_flags,
            "CMAKE_BUILD_TYPE": "Debug",
            "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
        }

    @property
    def release_cmake_flags(self) -> Mapping[str, str]:
        return {
            **self.base_cmake_flags,
            "CMAKE_BUILD_TYPE": "RelWithDebInfo",
        }

    @property
    def coverage_cmake_flags(self) -> Mapping[str, str]:
        if self._coverage_cmake_flags_extra is None:
            extra: Mapping[str, str] = {}
        else:
            extra = self._coverage_cmake_flags_extra
        return {
            **self.base_cmake_flags,
            **extra,
            "CMAKE_BUILD_TYPE": "Debug",
            "FF_USE_CODE_COVERAGE": "ON",
        }

    @property
    def cmake_require_shell(self) -> bool:
        if self._cmake_require_shell is None:
            return False
        else:
            return self._cmake_require_shell

    @property
    def header_extension(self) -> str:
        if self._header_extension is None:
            return ".hh"
        else:
            assert self._header_extension.startswith(".")
            return self._header_extension

    @property
    def extension_config(self) -> ExtensionConfig:
        return ExtensionConfig(
            header_extension=self.header_extension,
            src_extension='.cc',
        )

    @property
    def fix_compile_commands(self) -> bool:
        if self._fix_compile_commands is None:
            return False
        else:
            return self._fix_compile_commands

    @property
    def test_header_path(self) -> Path:
        if self._test_header_path is None:
            return Path(f"utils/testing{self.header_extension}")
        else:
            return self._test_header_path

    @property
    def test_case_timeout_seconds(self) -> Optional[int]:
        if self._test_case_timeout_seconds is None:
            return 60 * 3
        else:
            return self._test_case_timeout_seconds

    @property
    def benchmark_timeout_seconds(self) -> Optional[int]:
        if self._benchmark_timeout_seconds is None:
            return 60 * 3
        else:
            return self._benchmark_timeout_seconds

    @property
    def cuda_launch_cmd(self) -> Tuple[str, ...]:
        if self._cuda_launch_cmd is None:
            return tuple()
        else:
            return self._cuda_launch_cmd

    def cmd_for_run_target(
        self, run_target: Union[CpuRunTarget, CudaRunTarget]
    ) -> Tuple[str, ...]:
        cmd = tuple(
            [
                f"./{run_target.executable_path.name}",
                "--no-intro",
                "--no-version",
                "--force-colors",
                *run_target.args,
            ]
        )
        if isinstance(run_target, CudaRunTarget):
            cmd = self.cuda_launch_cmd + cmd
        return cmd

    @property
    def layout_ignore_paths(self) -> Tuple[Path, ...]:
        if self._layout_ignore_paths is None:
            return tuple()
        else:
            return self._layout_ignore_paths

def load_repo_config(repo: Repo, file_tree: FileTree) -> ProjectConfig:
    contents = file_tree.get_file_contents(repo.path / ".proj.toml")
    raw = toml.loads(contents)
    return load_parsed_config(repo, raw)


def _load_target_config(m: Mapping[str, object]) -> Union[LibConfig, BinConfig]:
    target_type = m["type"]

    if target_type == "lib":
        assert set(m.keys()) == {
            "type",
            "has-cpu-only-tests",
            "has-cpu-only-benchmarks",
            "has-cuda-tests",
            "has-cuda-benchmarks",
        }
        has_cpu_only_test_suite = require_bool(m["has-cpu-only-tests"])
        has_cuda_test_suite = require_bool(m["has-cuda-tests"])
        has_cpu_only_benchmark_suite = require_bool(m["has-cpu-only-benchmarks"])
        has_cuda_benchmark_suite = require_bool(m["has-cuda-benchmarks"])
        assert not has_cuda_benchmark_suite
        return LibConfig(
            has_cpu_only_test_suite=has_cpu_only_test_suite,
            has_cuda_test_suite=has_cuda_test_suite,
            has_cpu_only_benchmark_suite=has_cpu_only_benchmark_suite,
            has_cuda_benchmark_suite=has_cuda_benchmark_suite,
        )
    elif target_type == "bin":
        assert set(m.keys()) == {"type", "cuda"}
        requires_cuda = require_bool(m["cuda"])
        return BinConfig(requires_cuda)
    else:
        raise ValueError


def resolve_test_case_type_without_build(
    config: ProjectConfig,
    test_case: GenericTestCaseTarget,
) -> Optional[Union[CpuTestCaseTarget, CudaTestCaseTarget]]:
    suite_has_cuda = config.lib_has_cuda_test_suite(test_case.test_suite.lib)
    suite_has_cpu = config.lib_has_cpu_only_test_suite(test_case.test_suite.lib)
    assert suite_has_cpu or suite_has_cuda
    if suite_has_cpu and not suite_has_cuda:
        return test_case.cpu_test_case
    elif suite_has_cuda and not suite_has_cpu:
        return test_case.cuda_test_case
    else:
        return None


def resolve_generic_test_suite_target(
    config: ProjectConfig,
    t: GenericTestSuiteTarget,
) -> Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]:
    return config.test_suite_for_lib(t.lib)


def resolve_generic_test_case_target(
    config: ProjectConfig,
    t: GenericTestCaseTarget,
) -> Union[CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget]:
    result = resolve_test_case_type_without_build(config, t)
    if result is not None:
        return result
    else:
        return t


def resolve_test_target(
    config: ProjectConfig, t: Union[GenericTestSuiteTarget, GenericTestCaseTarget]
) -> Union[
    MixedTestSuiteTarget,
    CpuTestSuiteTarget,
    CudaTestSuiteTarget,
    CpuTestCaseTarget,
    CudaTestCaseTarget,
    GenericTestCaseTarget,
]:
    if isinstance(t, GenericTestSuiteTarget):
        return resolve_generic_test_suite_target(config, t)
    else:
        assert isinstance(t, GenericTestCaseTarget)
        return resolve_generic_test_case_target(config, t)


def resolve_bin_target(
    config: ProjectConfig,
    t: GenericBinTarget,
) -> Union[CpuBinTarget, CudaBinTarget]:
    if CpuBinTarget(t) in config.bin_targets:
        return CpuBinTarget(t)
    else:
        assert CudaBinTarget(t) in config.bin_targets
        return CudaBinTarget(t)


def _load_targets(m: object) -> Mapping[str, Union[LibConfig, BinConfig]]:
    assert isinstance(m, dict)

    return {
        target_name: _load_target_config(target_config)
        for target_name, target_config in m.items()
    }


def load_int(x: object) -> Optional[int]:
    return map_optional(x, require_int)

def load_build_tool(x: object) -> Optional[BuildTool]:
    return map_optional(map_optional(x, require_str), lambda s: BuildTool(s))


def load_bool(x: object) -> Optional[bool]:
    return map_optional(x, require_bool)

def load_path(x: object) -> Optional[Path]:
    return map_optional(map_optional(x, require_str), lambda s: Path(s))

def load_path_tuple(x: object) -> Optional[Tuple[Path, ...]]:
    if x is None:
        return None

    list_ = require_list_of(x, require_str)
    return tuple(Path(l) for l in list_)

def load_cmake_flags(x: object) -> Optional[Mapping[str, str]]:
    return map_optional(x, lambda y: require_dict_of(y, require_str, require_str))


def _load_config(repo: Repo) -> Optional[ProjectConfig]:
    with (Path(repo.path) / ".proj.toml").open("r") as f:
        raw = toml.loads(f.read())

    return load_parsed_config(repo, raw)


class ConfigKey(StrEnum):
    PROJECT_NAME = "project_name"
    TARGETS = "targets"
    DEFAULT_BIN_TARGETS = "default_bin_targets"
    DEFAULT_TEST_TARGETS = "default_test_targets"
    DEFAULT_BENCHMARK_TARGETS = "default_benchmark_targets"
    TESTSUITE_MACRO = "testsuite_macro"
    IFNDEF_NAME = "ifndef_name"
    NAMESPACE_NAME = "namespace_name"
    CMAKE_FLAGS_EXTRA = "cmake_flags_extra"
    CMAKE_REQUIRE_SHELL = "cmake_require_shell"
    HEADER_EXTENSION = "header_extension"
    FIX_COMPILE_COMMANDS = "fix_compile_commands"
    TEST_HEADER_PATH = "test_header_path"
    CUDA_LAUNCH_CMD = "cuda_launch_cmd"
    LAYOUT_IGNORE_PATHS = "layout_ignore_paths"
    DOXYGEN = "doxygen"
    BUILD_TOOL = "build_tool"
    TEST_CASE_TIMEOUT_SECONDS = "test_case_timeout_seconds"
    BENCHMARK_TIMEOUT_SECONDS = "benchmark_timeout_seconds"
    BENCHMARKS = "benchmarks"

def load_parsed_config(repo: Repo, raw: object) -> ProjectConfig:
    _l.debug("Loading parsed config: %s", raw)
    assert isinstance(raw, dict)

    allowed_keys = set(ConfigKey)
    assert allowed_keys.issuperset(raw.keys())

    return ProjectConfig(
        project_name=require_str(raw[ConfigKey.PROJECT_NAME]),
        base=Path(repo.path),
        _targets=_load_targets(raw[ConfigKey.TARGETS]),
        _doxygen=load_bool(raw.get(ConfigKey.DOXYGEN)),
        _default_build_targets=load_str_tuple(raw.get(ConfigKey.DEFAULT_BIN_TARGETS)),
        _default_test_targets=load_str_tuple(raw.get(ConfigKey.DEFAULT_TEST_TARGETS)),
        _default_benchmark_targets=load_str_tuple(
            raw.get(ConfigKey.DEFAULT_BENCHMARK_TARGETS)
        ),
        _testsuite_macro=map_optional(raw.get(ConfigKey.TESTSUITE_MACRO), require_str),
        _ifndef_name=map_optional(raw.get(ConfigKey.IFNDEF_NAME), require_str),
        _namespace_name=map_optional(raw.get(ConfigKey.NAMESPACE_NAME), require_str),
        _cmake_flags_extra=load_cmake_flags(raw.get(ConfigKey.CMAKE_FLAGS_EXTRA)),
        _cmake_require_shell=map_optional(
            raw.get(ConfigKey.CMAKE_REQUIRE_SHELL), require_bool
        ),
        _header_extension=map_optional(
            raw.get(ConfigKey.HEADER_EXTENSION), require_str
        ),
        _fix_compile_commands=map_optional(
            raw.get(ConfigKey.FIX_COMPILE_COMMANDS), require_bool
        ),
        _test_header_path=load_path(raw.get(ConfigKey.TEST_HEADER_PATH)),
        _cuda_launch_cmd=load_str_tuple(raw.get(ConfigKey.CUDA_LAUNCH_CMD)),
        _layout_ignore_paths=load_path_tuple(raw.get(ConfigKey.LAYOUT_IGNORE_PATHS)),
        _build_tool=load_build_tool(raw.get(ConfigKey.BUILD_TOOL)),
        _test_case_timeout_seconds=load_int(raw.get(ConfigKey.TEST_CASE_TIMEOUT_SECONDS)),
        _benchmark_timeout_seconds=load_int(raw.get(ConfigKey.BENCHMARK_TIMEOUT_SECONDS)),
        _benchmark_instruction_budgets=_load_benchmarks(raw.get(ConfigKey.BENCHMARKS, dict())),
    )

def dump_config(cfg: ProjectConfig) -> Json:
    return {
        "namespace_name": cfg.namespace_name,
        "testsuite_macro": cfg.testsuite_macro,
        "header_extension": cfg.header_extension,
    }
