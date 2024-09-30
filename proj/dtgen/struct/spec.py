from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Sequence,
    Optional,
    FrozenSet,
    Any,
    Mapping,
)
from pathlib import Path
from proj.dtgen.render_utils import (
    IncludeSpec,
    parse_include_spec,
)
import proj.toml as toml
from proj.json import Json

class Feature(Enum):
    JSON = auto()
    EQ = auto()
    ORD = auto()
    HASH = auto()
    FMT = auto()
    RAPIDCHECK = auto()
    # SERIALIZE = auto()

    def json(self) -> Json:
        return self.name

@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_: str
    _json_key: Optional[str]

    @property
    def json_key(self) -> str:
        if self._json_key is None:
            return self.name
        else:
            return self._json_key

    def json(self) -> Json:
        return {
            'name': self.name,
            'type_': self.type_,
            'json_key': self.json_key,
        }

@dataclass(frozen=True)
class StructSpec:
    includes: Sequence[IncludeSpec]
    src_includes: Sequence[IncludeSpec]
    namespace: Optional[str]
    template_params: Sequence[str]
    name: str
    fields: Sequence[FieldSpec]
    features: FrozenSet[Feature]

    def json(self) -> Json:
        return {
            'includes': [inc.json() for inc in self.includes],
            'src_includes': [inc.json() for inc in self.src_includes],
            'namespace': self.namespace,
            'template_params': list(self.template_params),
            'name': self.name,
            'fields': [field.json() for field in self.fields],
            'features': [feature.json() for feature in sorted(self.features, key=lambda f: f.name)]
        }


def parse_feature(raw: str) -> Feature:
    if raw == 'json':
        return Feature.JSON
    elif raw == 'eq':
        return Feature.EQ
    elif raw == 'ord':
        return Feature.ORD
    elif raw == 'hash':
        return Feature.HASH
    elif raw == 'rapidcheck':
        return Feature.RAPIDCHECK
    elif raw == 'fmt':
        return Feature.FMT
    # elif raw == 'serialize':
    #     return Feature.SERIALIZE
    else:
        raise ValueError(f'Unknown feature: {raw}')

def parse_field_spec(raw: Mapping[str, Any]) -> FieldSpec:
    return FieldSpec(
        name=raw['name'],
        type_=raw['type'],
        _json_key=raw.get('json_key'),
    )

def parse_struct_spec(raw: Mapping[str, Any]) -> StructSpec:
    return StructSpec(
        namespace=raw.get('namespace', None),
        includes=[parse_include_spec(include) for include in raw.get('includes', ())],
        src_includes=[parse_include_spec(src_include) for src_include in raw.get('src_includes', ())],
        template_params=raw.get('template_params', ()),
        name=raw['name'],
        fields=[parse_field_spec(field) for field in raw['fields']],
        features=frozenset([parse_feature(feature) for feature in raw['features']]),
    )

def load_spec(path: Path) -> StructSpec:
    try:
        with path.open('r') as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f'Failed to load spec {path}') from e
    try:
        return parse_struct_spec(raw)
    except KeyError as e:
        raise RuntimeError(f'Failed to parse spec {path}') from e
