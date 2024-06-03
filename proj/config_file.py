from pathlib import Path
from dataclasses import dataclass
from typing import (
    Optional,
    Mapping,
    Tuple,
    Iterator,
)
import string
import re
import io
import proj.toml as toml

@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    base: Path
    _build_targets: Optional[Tuple[str,...]] = None
    _test_targets: Optional[Tuple[str,...]] = None
    _ifndef_name: Optional[str] = None
    _namespace_name: Optional[str] = None
    _testsuite_macro: Optional[str] = None
    _cmake_flags_extra: Optional[Mapping[str, str]] = None
    _cmake_require_shell: Optional[bool] = None
    _inherit_up: Optional[bool] = None
    _header_extension: Optional[str] = None
    _fix_compile_commands: Optional[bool] = None
    _test_header_path: Optional[Path] = None

    @property
    def build_dir(self) -> Path:
        return self.base / 'build/normal'
    
    @property
    def cov_dir(self) -> Path:
        return self.base / 'build/codecov'

    @property
    def build_targets(self) -> Tuple[str, ...]:
        if self._build_targets is None:
            return tuple([self.project_name])
        else:
            return self._build_targets

    @property
    def test_targets(self) -> Tuple[str, ...]:
        if self._test_targets is None:
            return tuple([f'{self.project_name}-tests'])
        else:
            return self._test_targets

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
    def cmake_flags(self) -> Mapping[str, str]:
        if self._cmake_flags_extra is None:
            extra: Mapping[str, str] = {}
        else:
            extra = self._cmake_flags_extra
        return {
            **extra,
            'CMAKE_CXX_FLAGS': '-ftemplate-backtrace-limit=0',
            'CMAKE_BUILD_TYPE': 'Debug',
            'CMAKE_EXPORT_COMPILE_COMMANDS': 'ON',
            'CMAKE_CXX_COMPILER_LAUNCHER': 'ccache',
        }

    @property
    def cmake_require_shell(self) -> bool:
        if self._cmake_require_shell is None:
            return False
        else:
            return self._cmake_require_shell

    @property
    def inherit_up(self) -> bool:
        if self._inherit_up is None:
            return False
        else:
            return self._inherit_up

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

def _load_config(d: Path) -> Optional[ProjectConfig]:
    config_root = find_config_root(d)
    if config_root is None:
        return None

    with (config_root / '.proj.toml').open('r') as f:
        raw = toml.loads(f.read())
    return ProjectConfig(
        project_name=raw['project_name'],
        base=config_root,
        _build_targets=raw.get('build_targets'),
        _test_targets=raw.get('test_targets'),
        _testsuite_macro=raw.get('testsuite_macro'),
        _ifndef_name=raw.get('ifndef_name'),
        _namespace_name=raw.get('namespace_name'),
        _cmake_flags_extra=raw.get('cmake_flags_extra'),
        _cmake_require_shell=raw.get('cmake_require_shell'),
        _header_extension=raw.get('header_extension'),
        _fix_compile_commands=raw.get('fix_compile_commands'),
        _test_header_path=raw.get('test_header_path'),
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

def get_config(p) -> ProjectConfig:
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

def with_suffixes(p, suffs):
    name = p.name
    while '.' in name:
        name = name[:name.rfind('.')]
    return p.with_name(name + suffs)

def with_suffix_appended(p, suff):
    assert suff.startswith('.')
    return p.with_name(p.name + suff)

def with_suffix_removed(p):
    return p.with_suffix('')

def get_sublib_root(p: Path):
    p = Path(p).resolve()
    assert p.is_absolute()

    while True:
        src_dir = p / 'src'
        include_dir = p / 'include'

        if src_dir.is_dir() and include_dir.is_dir():
            return p

        if p == p.parent:
            return None
        else:
            p = p.parent

def get_src_dir(p: Path) -> Path:
    return get_sublib_root(p) / 'src'

def get_include_dir(p: Path) -> Path:
    return get_sublib_root(p) / 'include'

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
    src_dir = get_src_dir(p)
    for d in [include_dir, src_dir]:
        for ext in ['.struct.toml', '.enum.toml', '.variant.toml']:
            yield d / with_suffix_appended(with_suffix_removed(subrelpath), ext)

def get_include_path(p: Path) -> str:
    p = Path(p).absolute()
    sublib_root = get_sublib_root(p)
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
    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()

    return src_dir / with_suffix_appended(get_subrelpath(p), '.cc')
