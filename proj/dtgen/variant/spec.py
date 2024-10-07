from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    FrozenSet,
    Optional,
    Sequence,
    Any,
    Mapping,
)
from proj.dtgen.render_utils import (
    IncludeSpec,
    parse_include_spec,
)
import proj.toml as toml
from pathlib import Path
from proj.json import Json

class Feature(Enum):
    EQ = auto()
    ORD = auto()
    HASH = auto()
    JSON = auto()
    FMT = auto()
    RAPIDCHECK = auto()

    def json(self) -> Json:
        return self.name

@dataclass(frozen=True)
class ValueSpec:
    type_: str
    _key: Optional[str]
    _json_key: Optional[str]
    _fmt_key: Optional[str]

    def json(self) -> Json:
        return {
            'type_': self.type_,
            'key': self.key,
            'json_key': self.json_key,
            'fmt_key': self.fmt_key,
        }

    @property
    def key(self) -> str:
        if self._key is None:
            return self.type_
        else:
            return self._key

    @property
    def method_key(self) -> Optional[str]:
        return self._key

    @property
    def fmt_key(self) -> str:
        if self._fmt_key is None:
            return self.key
        else:
            return self._fmt_key

    @property
    def json_key(self) -> str:
        if self._json_key is None:
            return self.key
        else:
            return self._json_key

@dataclass(frozen=True)
class VariantSpec:
    includes: Sequence[IncludeSpec]
    src_includes: Sequence[IncludeSpec]
    namespace: Optional[str]
    template_params: Sequence[str]
    name: str
    values: Sequence[ValueSpec]
    features: FrozenSet[Feature]
    explicit_constructors: bool

    def json(self) -> Json:
        return {
            'includes': [include.json() for include in self.includes],
            'src_includes': [include.json() for include in self.src_includes],
            'namespace': self.namespace,
            'template_params': list(self.template_params),
            'name': self.name,
            'values': [value.json() for value in self.values],
            'features': [feature.json() for feature in self.features],
            'explicit_constructors': self.explicit_constructors,
        }

def parse_feature(raw: str) -> Feature:
    if raw == 'eq':
        return Feature.EQ
    elif raw == 'ord':
        return Feature.ORD
    elif raw == 'hash':
        return Feature.HASH
    elif raw == 'json':
        return Feature.JSON
    elif raw == 'fmt':
        return Feature.FMT
    elif raw == 'rapidcheck':
        return Feature.RAPIDCHECK
    else:
        raise ValueError(f'Unknown feature: {raw}')

def parse_value_spec(raw: Mapping[str, Any]) -> ValueSpec:
    return ValueSpec(
        type_=raw['type'],
        _key=raw.get('key', None),
        _json_key=raw.get('json_key', None),
        _fmt_key=raw.get('fmt_key', None),
    )

def parse_variant_spec(raw: Mapping[str, Any]) -> VariantSpec:
    return VariantSpec(
        namespace=raw.get('namespace', None),
        includes=[parse_include_spec(include) for include in raw.get('includes', ())],
        src_includes=[parse_include_spec(include) for include in raw.get('src_includes', ())],
        explicit_constructors=raw.get('explicit_constructors', True),
        template_params=raw.get('template_params', ()),
        name=raw['name'],
        values=[parse_value_spec(value) for value in raw['values']],
        features=frozenset([parse_feature(feature) for feature in raw['features']]),
    )

def load_spec(path: Path) -> VariantSpec:
    try:
        with path.open('r') as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f'Failed to load spec {path}') from e
    try:
        spec = parse_variant_spec(raw)
        if any(val.method_key is not None for val in spec.values) and any(val.method_key is None for val in spec.values):
            raise RuntimeError(f'Failed to load spec {path}. Expected either all values to have a key or no values to have a key, but found otherwise.')
        return spec
    except KeyError as e:
        raise RuntimeError(f'Failed to parse spec {path}') from e
