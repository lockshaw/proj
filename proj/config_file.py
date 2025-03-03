from pathlib import Path
from dataclasses import dataclass
from typing import (
    Optional,
    Mapping,
    Tuple,
    Iterator,
    Union,
)
from immutables import Map
import string
import re
import io
import proj.toml as toml
from .targets import (
    BuildTarget,
    TestCaseTarget,
    LibTarget,
    TestSuiteTarget,
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
    BinTarget,
    ConfiguredNames,
    parse_generic_test_target,
    parse_generic_benchmark_target,
)
import logging
from .utils import (
    map_optional,
)
from .json import (
    require_str,
    require_bool,
    require_list_of,
    require_dict_of,
)

_l = logging.getLogger(__name__)

@dataclass(frozen=True, order=True)
class LibConfig:
    has_test_suite: bool
    has_benchmark_suite: bool

@dataclass(frozen=True, order=True)
class BinConfig:
    pass

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
    def bin_names(self) -> Tuple[str, ...]:
        return tuple([
            target_name 
            for target_name, target_config 
            in sorted(self._targets.items()) 
            if isinstance(target_config, BinConfig)
        ])

    @property
    def bin_targets(self) -> Tuple[BinTarget, ...]:
        return tuple(BinTarget(n) for n in self.bin_names)

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
    def all_test_targets(self) -> Tuple[TestSuiteTarget, ...]:
        return tuple([lib.test_target for lib in sorted(self.lib_targets)])

    @property
    def default_test_targets(self) -> Tuple[Union[TestSuiteTarget, TestCaseTarget], ...]:
        if self._default_test_targets is None:
            return self.all_test_targets
        else:
            return tuple(parse_generic_test_target(s) for s in self._default_test_targets)

    @property
    def default_benchmark_targets(self) -> Tuple[Union[BenchmarkSuiteTarget, BenchmarkCaseTarget], ...]:
        if self._default_benchmark_targets is None:
            return tuple([lib.benchmark_target for lib in sorted(self.lib_targets)])
        else:
            return tuple(parse_generic_benchmark_target(s) for s in self._default_benchmark_targets)

    @property
    def ifndef_name(self) -> str:
        if self._ifndef_name is None:
            result = self.project_name.upper()
        else:
            result = self._ifndef_name
        allowed = set(string.ascii_uppercase + '_')
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
        assert set(m.keys()) == {'type', 'tests', 'benchmarks'}
        has_test_suite = m["tests"]
        assert isinstance(has_test_suite, bool)
        has_benchmark_suite = m["benchmarks"]
        assert isinstance(has_benchmark_suite, bool)
        return LibConfig(
            has_test_suite=has_test_suite,
            has_benchmark_suite=has_benchmark_suite,
        )
    elif target_type == "bin":
        return BinConfig()
    else:
        raise ValueError

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

    return _load_parsed_config(config_root, raw)

def _load_parsed_config(config_root: Path, raw: object) -> ProjectConfig:
    _l.debug('Loading parsed config: %s', raw)
    assert isinstance(raw, dict)

    return ProjectConfig(
        project_name=require_str(raw['project_name']),
        base=config_root,
        _targets=_load_targets(raw['targets']),
        _default_build_targets=load_str_tuple(raw.get('default_bin_targets')),
        _default_test_targets=load_str_tuple(raw.get('default_test_targets')),
        _default_benchmark_targets=load_str_tuple(raw.get('default_benchmark_targets')),
        _testsuite_macro=map_optional(raw.get('testsuite_macro'), require_str),
        _ifndef_name=map_optional(raw.get('ifndef_name'), require_str),
        _namespace_name=map_optional(raw.get('namespace_name'), require_str),
        _cmake_flags_extra=load_cmake_flags(raw.get('cmake_flags_extra')),
        _cmake_require_shell=map_optional(raw.get('cmake_require_shell'), require_bool),
        _header_extension=map_optional(raw.get('header_extension'), require_str),
        _fix_compile_commands=map_optional(raw.get('fix_compile_commands'), require_bool),
        _test_header_path=load_path(raw.get('test_header_path')),
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

def gen_ifndef_uid(p):
    p = Path(p).absolute()
    config_root = find_config_root(p)
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
    if p.is_relative_to(src_dir):
        return with_project_specific_extension_removed(p.relative_to(src_dir), config=config)
    elif p.is_relative_to(include_dir):
        return with_project_specific_extension_removed(p.relative_to(include_dir), config=config)
    else:
        raise ValueError(f'Path {p} not relative to either src or include')

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

def get_include_path(p: Path) -> str:
    p = Path(p).absolute()
    sublib_root = get_sublib_root(p)
    assert sublib_root is not None
    config = load_config(p)
    subrelpath = get_subrelpath(p)

    include_dir = sublib_root / 'include'
    assert include_dir.is_dir()
    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()

    subrelpath_with_extension = with_suffix_appended(subrelpath, config.header_extension)

    public_include = include_dir / subrelpath_with_extension
    private_include = src_dir / subrelpath_with_extension
    if public_include.exists():
        return str(public_include.relative_to(include_dir))
    if private_include.exists():
        return str(private_include.relative_to(src_dir))
    raise ValueError([public_include, private_include])

def get_source_path(p: Path) -> Path:
    p = Path(p).absolute()
    sublib_root = get_sublib_root(p)
    assert sublib_root is not None
    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()

    return src_dir / with_suffix_appended(get_subrelpath(p), '.cc')
