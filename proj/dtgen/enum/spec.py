from dataclasses import dataclass
from typing import (
    Optional,
    Sequence,
    Any,
    Mapping,
    FrozenSet,
)
from enum import Enum, auto
from pathlib import Path
import proj.toml as toml
from proj.json import Json

class Feature(Enum):
    JSON = auto()
    HASH = auto()
    FMT = auto()
    RAPIDCHECK = auto()

    def json(self) -> Json:
        return self.value

@dataclass(frozen=True)
class ValueSpec:
    name: str
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
            'json_key': self.json_key,
        }

@dataclass(frozen=True)
class EnumSpec:
    namespace: Optional[str]
    name: str
    values: Sequence[ValueSpec]
    features: FrozenSet[Feature]

    def json(self) -> Json:
        return {
            'namespace': self.namespace,
            'name': self.name,
            'values': [v.json() for v in self.values],
            'features': [feature.json() for feature in sorted(self.features, key=lambda f: f.name)],
        }

def parse_feature(raw: str) -> Feature:
    if raw == 'json':
        return Feature.JSON
    elif raw == 'rapidcheck':
        return Feature.RAPIDCHECK
    elif raw == 'fmt':
        return Feature.FMT
    elif raw == 'hash':
        return Feature.HASH
    else:
        raise ValueError(f'Unknown feature: {raw}')

def parse_value_spec(raw: Mapping[str, Any]) -> ValueSpec:
    return ValueSpec(
        name=raw['name'],
        _json_key=raw.get('json_key'),
    )

def parse_enum_spec(raw: Mapping[str, Any]) -> EnumSpec:
    return EnumSpec(
        namespace=raw.get('namespace', None),
        name=raw['name'],
        values=[parse_value_spec(value) for value in raw['values']],
        features=frozenset([parse_feature(feature) for feature in raw['features']]),
    )

def load_spec(path: Path) -> EnumSpec:
    try:
        with path.open('r') as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f'Failed to load spec {path}') from e
    try:
        return parse_enum_spec(raw)
    except KeyError as e:
        raise RuntimeError(f'Failed to parse spec {path}') from e
