from pathlib import Path
from dataclasses import dataclass
try:
    import tomllib as toml
except ImportError:
    import toml
from typing import (
    Optional,
    Mapping,
    Dict,
    Tuple,
)
import string

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

    @property
    def build_dir(self) -> Path:
        return self.base / 'build'

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
            extra: Dict[str, str] = {}
        else:
            extra = self._cmake_flags_extra
        return {
            **extra,
            'CMAKE_CXX_FLAGS': '-ftemplate-backtrace-limit=0',
            'CMAKE_BUILD_TYPE': 'Debug',
            'CMAKE_EXPORT_COMPILE_COMMANDS': 'ON',
            'CMAKE_CXX_COMPILER_LAUNCHER': 'ccache',
            'CMAKE_CXX_COMPILER': 'clang++',
            'CMAKE_C_COMPILER': 'clang',
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

def find_config_root(d: Path) -> Optional[Path]:
    d = Path(d).resolve()
    assert d.is_absolute()

    while True:
        config_path = d / '.lockshaw.toml'

        if config_path.is_file():
            return d

        if d == d.parent:
            return None
        else:
            d = d.parent

def _load_config(d: Path) -> Optional[ProjectConfig]:
    config_root = find_config_root(d)
    if config_root is None:
        return None

    with (config_root / '.lockshaw.toml').open('r') as f:
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
        _header_extension=raw.get('header_extension'),
    )

def gen_ifndef_uid(p):
    p = Path(p).absolute()
    config_root = find_config_root(p)
    relpath = p.relative_to(config_root)
    config = _load_config(p)
    return f'_{config.ifndef_name}_' + str(relpath).upper().replace('/', '_').replace('.', '_')

def get_config(p) -> Optional[ProjectConfig]:
    p = Path(p).absolute()
    config = _load_config(p)
    return config

def get_lib_root(p: Path) -> Path:
    config_root = find_config_root(p)
    assert config_root is not None
    return config_root / 'lib'


def with_suffixes(p, suffs):
    name = p.name
    while '.' in name:
        name = name[:name.rfind('.')]
    return p.with_name(name + suffs)

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

def get_include_path(p: Path):
    p = Path(p).absolute()
    sublib_root = get_sublib_root(p)
    config = _load_config(p)
    assert config is not None
    subrelpath = p.relative_to(sublib_root / 'src')
    include_dir = sublib_root / 'include'
    assert include_dir.is_dir()
    src_dir = sublib_root / 'src'
    assert src_dir.is_dir()
    public_include = include_dir / with_suffixes(subrelpath, config.header_extension)
    private_include = src_dir / with_suffixes(subrelpath, config.header_extension)
    if public_include.exists():
        return str(public_include.relative_to(include_dir))
    if private_include.exists():
        return str(private_include.relative_to(src_dir))
    raise ValueError([public_include, private_include])
