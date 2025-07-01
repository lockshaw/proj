from pathlib import Path
from dataclasses import dataclass
from typing import (
    Optional,
    Mapping,
    Tuple,
    Iterator,
    Union,
    FrozenSet,
)
from immutables import Map
import string
import re
import io
import proj.toml as toml
from .targets import (
    BuildTarget,
    CpuTestCaseTarget,
    CpuTestSuiteTarget,
    CudaTestCaseTarget,
    CudaTestSuiteTarget,
    LibTarget,
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
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
)
from enum import (
    StrEnum,
)

_l = logging.getLogger(__name__)

@dataclass(frozen=True, order=True)
class LibConfig:
    has_cpu_only_test_suite: bool
    has_cuda_test_suite: bool
    has_cpu_only_benchmark_suite: bool
    has_cuda_benchmark_suite: bool

def get_test_target(lib_name: str, lib_config: LibConfig) -> Union[CpuTestSuiteTarget, CudaTestSuiteTarget]:
    assert lib_config.has_cpu_only_test_suite or lib_config.has_cuda_test_suite

    if lib_config.has_cuda_test_suite:
        return LibTarget(lib_name).cuda_test_target
    else:
        return LibTarget(lib_name).cpu_test_target

@dataclass(frozen=True, order=True)
class BinConfig:
    requires_cuda: bool

@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    base: Path
    _targets: Mapping[str, Union[LibConfig, BinConfig]]
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

    @property
    def debug_build_dir(self) -> Path:
        return self.base / 'build/normal'
    
    @property
    def release_build_dir(self) -> Path:
        return self.base / 'build/release'

    @property
    def coverage_build_dir(self) -> Path:
        return self.base / 'build/coverage'

    @property
    def benchmark_html_dir(self) -> Path:
        return self.release_build_dir / 'bencher'

    @property
    def doxygen_dir(self) -> Path:
        return self.base / 'build/doxygen'

    @property
    def bin_names(self) -> Mapping[str, BinConfig]:
        return {
            target_name: target_config
            for target_name, target_config 
            in sorted(self._targets.items()) 
            if isinstance(target_config, BinConfig)
        }

    @property
    def bin_targets(self) -> FrozenSet[Union[CpuBinTarget, CudaBinTarget]]:
        return frozenset(
            CudaBinTarget(GenericBinTarget(bin_name))
            if conf.requires_cuda else
            CpuBinTarget(GenericBinTarget(bin_name))
            for bin_name, conf in self.bin_names.items()
        )

    @property
    def lib_names(self) -> Mapping[str, LibConfig]:
        return {
            target_name: target_config 
            for target_name, target_config 
            in sorted(self._targets.items())
            if isinstance(target_config, LibConfig)
        }

    @property
    def lib_targets(self) -> Mapping[LibTarget, LibConfig]:
        return {
            LibTarget(k): v for k, v in self.lib_names.items()
        }

    @property
    def configured_names(self) -> ConfiguredNames:
        return ConfiguredNames(
            bin_names=set(self.bin_names),
            lib_names=set(self.lib_names.keys()),
        )


    @property
    def all_build_targets(self) -> Tuple[BuildTarget, ...]:
        return tuple([
            *[lib.build_target for lib in sorted(self.lib_targets)],
            *[bin.build_target for bin in sorted(self.bin_targets)],
        ])

    @property
    def default_build_targets(self) -> Tuple[BuildTarget, ...]:
        if self._default_build_targets is None: 
            return self.all_build_targets
        else:
            return tuple(BuildTarget.from_str(self.configured_names, s) for s in self._default_build_targets)

    @property
    def all_test_targets(self) -> FrozenSet[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]]:
        return frozenset([self.test_suite_for_lib(lib) for lib in sorted(self.lib_targets)])

    @property
    def all_cpu_test_targets(self) -> FrozenSet[CpuTestSuiteTarget]:
        return frozenset([lib.cpu_test_target for lib, conf in sorted(self.lib_targets.items()) if conf.has_cpu_only_test_suite])

    @property
    def all_cuda_test_targets(self) -> FrozenSet[CudaTestSuiteTarget]:
        return frozenset([lib.cuda_test_target for lib, conf in sorted(self.lib_targets.items()) if conf.has_cuda_test_suite])

    @property
    def default_test_targets(self) -> FrozenSet[Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget, CpuTestCaseTarget, CudaTestCaseTarget, GenericTestCaseTarget]]:
        if self._default_test_targets is None:
            return self.all_test_targets
        else:
            return frozenset([resolve_test_target(self, parse_generic_test_target(s)) for s in self._default_test_targets])

    def lib_has_cpu_only_test_suite(self, lib: LibTarget) -> bool:
        return self.lib_targets[lib].has_cpu_only_test_suite

    def lib_has_cuda_test_suite(self, lib: LibTarget) -> bool:
        return self.lib_targets[lib].has_cuda_test_suite

    def test_suite_for_lib(self, lib: LibTarget) -> Union[MixedTestSuiteTarget, CpuTestSuiteTarget, CudaTestSuiteTarget]:
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
    def default_benchmark_targets(self) -> Tuple[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget], ...]:
        if self._default_benchmark_targets is None:
            return tuple([lib.benchmark_target for lib in sorted(self.lib_targets)])
        else:
            return tuple(parse_generic_benchmark_target(s) for s in self._default_benchmark_targets)

    @property
    def ifndef_name(self) -> str:
        if self._ifndef_name is None:
            result = re.sub(r'[^a-zA-Z0-9_]', '_', self.project_name).upper()
        else:
            result = self._ifndef_name
        allowed = set(string.ascii_uppercase + string.digits + '_')
        assert all(c in allowed for c in result)
        return result

    @property
    def namespace_name(self) -> str:
        if self._namespace_name is None:
            result = self.project_name
        else:
            result = self._namespace_name
        allowed = set(string.ascii_uppercase + string.ascii_lowercase + '_')
        assert all(c in set(allowed) for c in result)
        return result

    @property
    def testsuite_macro(self) -> str:
        if self._testsuite_macro is None:
            return f'{self.ifndef_name}_TEST_SUITE'
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
            'CMAKE_CXX_COMPILER_LAUNCHER': 'ccache',
        }

    @property
    def debug_cmake_flags(self) -> Mapping[str, str]:
        return {
            **self.base_cmake_flags,
            'CMAKE_BUILD_TYPE': 'Debug',
            'CMAKE_EXPORT_COMPILE_COMMANDS': 'ON',
        }

    @property
    def release_cmake_flags(self) -> Mapping[str, str]:
        return {
            **self.base_cmake_flags,
            'CMAKE_BUILD_TYPE': 'RelWithDebInfo',
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
            'CMAKE_BUILD_TYPE': 'Debug',
            'FF_USE_CODE_COVERAGE': 'ON',
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
            return '.hh'
        else:
            assert self._header_extension.startswith('.')
            return self._header_extension

    @property
    def fix_compile_commands(self) -> bool:
        if self._fix_compile_commands is None:
            return False
        else:
            return self._fix_compile_commands

    @property
    def test_header_path(self) -> Path:
        if self._test_header_path is None:
            return Path(f'utils/testing{self.header_extension}')
        else:
            return self._test_header_path

    @property
    def cuda_launch_cmd(self) -> Tuple[str, ...]:
        if self._cuda_launch_cmd is None:
            return tuple()
        else:
            return self._cuda_launch_cmd

    def cmd_for_run_target(self, run_target: Union[CpuRunTarget, CudaRunTarget]) -> Tuple[str, ...]:
        cmd = tuple([f'./{run_target.executable_path.name}', '--no-intro', '--no-version', '--force-colors', *run_target.args])
        if isinstance(run_target, CudaRunTarget):
            cmd = self.cuda_launch_cmd + cmd
        return cmd

def _possible_config_paths(d: Path) -> Iterator[Path]:
    d = Path(d).resolve()
    assert d.is_absolute()

    for _d in [d, *d.parents]:
        config_path = _d / '.proj.toml'
        yield config_path

def find_config_root(d: Path) -> Optional[Path]:
    for possible_config in _possible_config_paths(d):
        if possible_config.is_file():
            return possible_config.parent

    return None

def _load_target_config(m: Mapping[str, object]) -> Union[LibConfig, BinConfig]:
    target_type = m["type"]

    if target_type == "lib":
        assert set(m.keys()) == {'type', 'has-cpu-only-tests', 'has-cpu-only-benchmarks', 'has-cuda-tests', 'has-cuda-benchmarks'}
        has_cpu_only_test_suite = require_bool(m["has-cpu-only-tests"])
        has_cuda_test_suite = require_bool(m["has-cuda-tests"])
        has_cpu_only_benchmark_suite = require_bool(m["has-cpu-only-benchmarks"])
        has_cuda_benchmark_suite = require_bool(m["has-cuda-benchmarks"])
        return LibConfig(
            has_cpu_only_test_suite=has_cpu_only_test_suite,
            has_cuda_test_suite=has_cuda_test_suite,
            has_cpu_only_benchmark_suite=has_cpu_only_benchmark_suite,
            has_cuda_benchmark_suite=has_cuda_benchmark_suite,
        )
    elif target_type == "bin":
        assert set(m.keys()) == {'type', 'cuda'}
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
    config: ProjectConfig,
    t: Union[GenericTestSuiteTarget, GenericTestCaseTarget]
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

def _load_targets(m: object) -> Map[str, Union[LibConfig, BinConfig]]:
    assert isinstance(m, dict)

    return Map({
        target_name: _load_target_config(target_config)
        for target_name, target_config
        in m.items()
    })

def load_str_tuple(x: object) -> Optional[Tuple[str, ...]]:
    return map_optional(map_optional(x, lambda l: require_list_of(l, require_str)), lambda ll: tuple(ll))

def load_path(x: object) -> Optional[Path]:
    return map_optional(map_optional(x, require_str), lambda s: Path(s))

def load_cmake_flags(x: object) -> Optional[Map[str, str]]:
    return map_optional(x, lambda y: require_dict_of(y, require_str, require_str))

def _load_config(d: Path) -> Optional[ProjectConfig]:
    config_root = find_config_root(d)
    if config_root is None:
        return None

    with (config_root / '.proj.toml').open('r') as f:
        raw = toml.loads(f.read())

    return load_parsed_config(config_root, raw)

class ConfigKey(StrEnum):
    PROJECT_NAME = 'project_name'
    TARGETS = 'targets'
    DEFAULT_BIN_TARGETS = 'default_bin_targets'
    DEFAULT_TEST_TARGETS = 'default_test_targets'
    DEFAULT_BENCHMARK_TARGETS = 'default_benchmark_targets'
    TESTSUITE_MACRO = 'testsuite_macro'
    IFNDEF_NAME = 'ifndef_name'
    NAMESPACE_NAME = 'namespace_name'
    CMAKE_FLAGS_EXTRA = 'cmake_flags_extra'
    CMAKE_REQUIRE_SHELL = 'cmake_require_shell'
    HEADER_EXTENSION = 'header_extension'
    FIX_COMPILE_COMMANDS = 'fix_compile_commands'
    TEST_HEADER_PATH = 'test_header_path'
    CUDA_LAUNCH_CMD = 'cuda_launch_cmd'

def load_parsed_config(config_root: Path, raw: object) -> ProjectConfig:
    _l.debug('Loading parsed config: %s', raw)
    assert isinstance(raw, dict)

    allowed_keys = set(ConfigKey)
    assert allowed_keys.issuperset(raw.keys())

    return ProjectConfig(
        project_name=require_str(raw[ConfigKey.PROJECT_NAME]),
        base=config_root,
        _targets=_load_targets(raw[ConfigKey.TARGETS]),
        _default_build_targets=load_str_tuple(raw.get(ConfigKey.DEFAULT_BIN_TARGETS)),
        _default_test_targets=load_str_tuple(raw.get(ConfigKey.DEFAULT_TEST_TARGETS)),
        _default_benchmark_targets=load_str_tuple(raw.get(ConfigKey.DEFAULT_BENCHMARK_TARGETS)),
        _testsuite_macro=map_optional(raw.get(ConfigKey.TESTSUITE_MACRO), require_str),
        _ifndef_name=map_optional(raw.get(ConfigKey.IFNDEF_NAME), require_str),
        _namespace_name=map_optional(raw.get(ConfigKey.NAMESPACE_NAME), require_str),
        _cmake_flags_extra=load_cmake_flags(raw.get(ConfigKey.CMAKE_FLAGS_EXTRA)),
        _cmake_require_shell=map_optional(raw.get(ConfigKey.CMAKE_REQUIRE_SHELL), require_bool),
        _header_extension=map_optional(raw.get(ConfigKey.HEADER_EXTENSION), require_str),
        _fix_compile_commands=map_optional(raw.get(ConfigKey.FIX_COMPILE_COMMANDS), require_bool),
        _test_header_path=load_path(raw.get(ConfigKey.TEST_HEADER_PATH)),
        _cuda_launch_cmd=load_str_tuple(raw.get(ConfigKey.CUDA_LAUNCH_CMD)),
    )



def get_config_root(d: Path) -> Path:
    config_root = find_config_root(d)

    if config_root is None:
        s = io.StringIO()
        s.write('Could not find config file at any of the following paths:\n')
        for searched_path in _possible_config_paths(d):
            s.write(f'- {searched_path}\n')

        raise FileNotFoundError(s.getvalue())
    else:
        return config_root

def load_config(d: Path) -> ProjectConfig:
    config = _load_config(d)

    if config is None:
        s = io.StringIO()
        s.write('Could not find config file at any of the following paths:\n')
        for searched_path in _possible_config_paths(d):
            s.write(f'- {searched_path}\n')

        raise FileNotFoundError(s.getvalue())
    else:
        return config

def gen_ifndef_uid(p: Union[Path, str]) -> str:
    p = Path(p).absolute()
    config_root = find_config_root(p)
    assert config_root is not None
    relpath = p.relative_to(config_root)
    config = load_config(p)
    unfixed = f'_{config.ifndef_name}_' + str(relpath)
    return re.sub(r'[^a-zA-Z0-9_]', '_', unfixed).upper()

def try_get_config(p: Union[Path, str]) -> Optional[ProjectConfig]:
    try:
        return get_config(p)
    except FileNotFoundError:
        return None

def get_config(p: Union[Path, str]) -> ProjectConfig:
    p = Path(p).absolute()
    config = load_config(p)
    return config

def get_lib_root(p: Path) -> Path:
    config_root = find_config_root(p)
    assert config_root is not None
    return config_root / 'lib'

def get_test_header_path(p: Path) -> Path:
    config = load_config(p)
    return config.test_header_path

def with_suffixes(p: Path, suffs: str) -> Path:
    name = p.name
    while '.' in name:
        name = name[:name.rfind('.')]
    return p.with_name(name + suffs)

def with_suffix_appended(p: Path, suff: str) -> Path:
    assert suff.startswith('.')
    return p.with_name(p.name + suff)

def with_suffix_removed(p: Path) -> Path:
    return p.with_suffix('')

def get_sublib_root(p: Path) -> Optional[Path]:
    p = Path(p).resolve()
    assert p.is_absolute()

    while True:
        src_dir = p / 'src'
        include_dir = p / 'include'

        src_exists = src_dir.is_dir()
        include_exists = include_dir.is_dir()

        _l.debug('get_sublib_root checking %s for %s is dir (%s) and %s is dir (%s)', p, src_dir, src_exists, include_dir, include_exists)

        if src_exists and include_exists:
            return p

        if p == p.parent:
            return None
        else:
            p = p.parent

def get_src_dir(p: Path) -> Optional[Path]:
    return map_optional(get_sublib_root(p), lambda pp: pp / 'src')

def get_include_dir(p: Path) -> Optional[Path]:
    return map_optional(get_sublib_root(p), lambda pp: pp / 'include')

def with_project_specific_extension_removed(p: Path, config: ProjectConfig) -> Path:
    project_specific = [
        '.struct.toml',
        '.variant.toml',
        '.enum.toml',
        '.test.cc',
        '.cc',
        '.cu',
        '.cpp',
        config.header_extension,
    ]

    suffixes = ''.join(p.suffixes)

    for extension in project_specific:
        if suffixes.endswith(extension):
            return with_suffixes(p, suffixes[:-len(extension)])

    raise ValueError(f'Could not find project-specific extension for path {p}')

@dataclass(frozen=True, order=True)
class HeaderInfo:
    path: Path
    ifndef: str

    def json(self) -> Json:
        return {
            'path': str(self.path),
            'ifndef': self.ifndef,
        }

@dataclass(frozen=True, order=True)
class PathInfo:
    include: Path
    public_header: HeaderInfo
    private_header: HeaderInfo
    header: Optional[Path]
    source: Path
    test_source: Optional[Path]
    benchmark_source: Optional[Path]

    def json(self) -> Json:
        return {
            'include': str(self.include),
            'public_header': self.public_header.json(),
            'private_header': self.private_header.json(),
            'header': map_optional(self.header, str),
            'source': str(self.source),
            'test_source': map_optional(self.test_source, str),
            'benchmark_source': map_optional(self.benchmark_source, str),
        }

def get_path_info(p: Path) -> PathInfo:
    public_header_info = get_public_header_info(p)
    private_header_info = get_private_header_info(p)
    return PathInfo(
        include=get_include_path(p),
        public_header=public_header_info,
        private_header=private_header_info,
        header=try_get_header_path(p),
        source=get_source_path(p),
        test_source=get_test_source_path(p),
        benchmark_source=get_benchmark_source_path(p),
    )

def get_subrelpath(p: Path, config: Optional[ProjectConfig] = None) -> Path:
    p = Path(p).absolute()
    if config is None:
        config = load_config(p)

    sublib_root = get_sublib_root(p)
    assert sublib_root is not None

    include_dir = sublib_root / 'include'
    assert include_dir.is_dir()

    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()

    test_src_dir = sublib_root / 'test/src'
    if test_src_dir.exists():
        assert test_src_dir.is_dir()

    base_dir: Path
    if p.is_relative_to(src_dir):
        base_dir = src_dir
    elif p.is_relative_to(include_dir):
        base_dir = include_dir
    elif p.is_relative_to(test_src_dir):
        base_dir = test_src_dir
    else:
        raise ValueError(f'Path {p} not relative to either src or include')

    return with_project_specific_extension_removed(p.relative_to(base_dir), config=config)

def get_possible_spec_paths(p: Path) -> Iterator[Path]:
    p = Path(p).absolute()
    config = get_config(p)
    assert p.name.endswith('.dtg.cc') or p.name.endswith('.dtg' + config.header_extension)
    subrelpath = get_subrelpath(p)
    include_dir = get_include_dir(p)
    assert include_dir is not None
    src_dir = get_src_dir(p)
    assert src_dir is not None
    for d in [include_dir, src_dir]:
        for ext in ['.struct.toml', '.enum.toml', '.variant.toml']:
            yield d / with_suffix_appended(with_suffix_removed(subrelpath), ext)

@dataclass(frozen=True, order=True)
class LibInfo:
    include_dir: Path
    src_dir: Path
    test_dir: Optional[Path]
    benchmark_dir: Optional[Path]

def get_lib_info(p: Path) -> LibInfo:
    p = Path(p).absolute()
    sublib_root = get_sublib_root(p)
    assert sublib_root is not None
    config_root = get_config_root(p)

    include_dir = sublib_root / 'include'
    assert include_dir.is_dir()

    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()

    test_dir = sublib_root / 'test'
    rel_test_dir: Optional[Path]
    if test_dir.is_dir():
        rel_test_dir = test_dir.relative_to(config_root)
    else:
        rel_test_dir = None

    benchmark_dir = sublib_root / 'benchmark'
    rel_benchmark_dir: Optional[Path]
    if benchmark_dir.is_dir():
        rel_benchmark_dir = benchmark_dir.relative_to(config_root)
    else:
        rel_benchmark_dir = None

    return LibInfo(
        include_dir=include_dir.relative_to(config_root),
        src_dir=src_dir.relative_to(config_root),
        test_dir=rel_test_dir,
        benchmark_dir=rel_benchmark_dir,
    )

def get_public_header_path(p: Path) -> Path:
    config = get_config(p)

    lib_info = get_lib_info(p)

    subrelpath = get_subrelpath(p)
    subrelpath_with_extension = with_suffix_appended(subrelpath, config.header_extension)

    return lib_info.include_dir / subrelpath_with_extension

def get_public_header_info(p: Path) -> HeaderInfo:
    path = get_public_header_path(p)
    return HeaderInfo(
        path=path,
        ifndef=gen_ifndef_uid(path),
    )

def get_private_header_path(p: Path) -> Path:
    config = get_config(p)

    lib_info = get_lib_info(p)

    subrelpath = get_subrelpath(p)
    subrelpath_with_extension = with_suffix_appended(subrelpath, config.header_extension)

    return lib_info.src_dir / subrelpath_with_extension

def get_private_header_info(p: Path) -> HeaderInfo:
    path = get_private_header_path(p)
    return HeaderInfo(
        path=path,
        ifndef=gen_ifndef_uid(path),
    )

def try_get_header_path(p: Path) -> Optional[Path]:
    try:
        return get_header_path(p)
    except RuntimeError:
        return None

def get_header_path(p: Path) -> Path:
    config = get_config(p)

    lib_info = get_lib_info(p)

    subrelpath = get_subrelpath(p)
    subrelpath_with_extension = with_suffix_appended(subrelpath, config.header_extension)

    public_include = lib_info.include_dir / subrelpath_with_extension
    private_include = lib_info.src_dir / subrelpath_with_extension
    if public_include.exists():
        return public_include
    elif private_include.exists():
        return private_include
    else:
        raise RuntimeError([public_include, private_include])

def get_include_path(p: Path) -> Path:
    lib_info = get_lib_info(p)
    header_path = get_public_header_path(p)
    return header_path.relative_to(lib_info.include_dir)

def get_source_path(p: Path) -> Path:
    p = Path(p).absolute()

    lib_info = get_lib_info(p)

    return lib_info.src_dir / with_suffix_appended(get_subrelpath(p), '.cc')

def get_test_source_path(p: Path) -> Optional[Path]:
    p = Path(p).absolute()

    lib_info = get_lib_info(p)

    if lib_info.test_dir is None:
        return None
    else:
        return lib_info.test_dir / 'src' / with_suffix_appended(get_subrelpath(p), '.cc')

def get_benchmark_source_path(p: Path) -> Optional[Path]:
    p = Path(p).absolute()

    lib_info = get_lib_info(p)

    if lib_info.benchmark_dir is None:
        return None
    else:
        return lib_info.benchmark_dir / 'src' / with_suffix_appended(get_subrelpath(p), '.cc')

def dump_config(cfg: ProjectConfig) -> Json:
    return {
        'namespace_name': cfg.namespace_name,
        'testsuite_macro': cfg.testsuite_macro,
        'header_extension': cfg.header_extension,
    }
