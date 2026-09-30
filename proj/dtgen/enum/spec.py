from dataclasses import dataclass
from typing import (
    Optional,
    Sequence,
    Any,
    Mapping,
    FrozenSet,
    List,
)
from proj.strenum import StrEnum
from enum import (
    Enum,
    auto,
)
from pathlib import Path
import proj.toml as toml
from proj.json import Json
import itertools

class Feature(Enum):
    JSON_DESERIALIZE = auto()
    JSON_SERIALIZE = auto()
    HASH = auto()
    FMT = auto()
    RAPIDCHECK = auto()

    def json(self) -> Json:
        return self.value


@dataclass(frozen=True)
class ValueSpec:
    name: str
    docstring: Optional[str]
    _json_key: Optional[str]

    @property
    def json_key(self) -> str:
        if self._json_key is None:
            return self.name
        else:
            return self._json_key

    def json(self) -> Json:
        return {
            "name": self.name,
            "docstring": self.docstring,
            "json_key": self.json_key,
        }


@dataclass(frozen=True)
class EnumSpec:
    namespace: Optional[str]
    name: str
    values: Sequence[ValueSpec]
    features: FrozenSet[Feature]
    docstring: Optional[str]

    def json(self) -> Json:
        return {
            "namespace": self.namespace,
            "name": self.name,
            "values": [v.json() for v in self.values],
            "features": [
                feature.json()
                for feature in sorted(self.features, key=lambda f: f.name)
            ],
            "docstring": self.docstring,
        }


def parse_feature(raw: str) -> List[Feature]:
    if raw == "json":
        return [Feature.JSON_SERIALIZE, Feature.JSON_DESERIALIZE]
    elif raw == "json_serialize":
        return [Feature.JSON_SERIALIZE]
    elif raw == "rapidcheck":
        return [Feature.RAPIDCHECK]
    elif raw == "fmt":
        return [Feature.FMT]
    elif raw == "hash":
        return [Feature.HASH]
    else:
        raise ValueError(f"Unknown feature: {raw}")

class ValueSpecKeys(StrEnum):
    NAME = 'name'
    DOCSTRING = 'docstring'
    JSON_KEY = 'json_key'

def parse_value_spec(raw: Mapping[str, Any]) -> ValueSpec:
    invalid_keys = set(raw.keys()) - set(ValueSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return ValueSpec(
        name=raw[ValueSpecKeys.NAME],
        docstring=raw.get(ValueSpecKeys.DOCSTRING, None),
        _json_key=raw.get(ValueSpecKeys.JSON_KEY, None),
    )

class EnumSpecKeys(StrEnum):
    NAMESPACE = 'namespace'
    NAME = 'name'
    VALUES = 'values'
    FEATURES = 'features'
    DOCSTRING = 'docstring'

def parse_enum_spec(raw: Mapping[str, Any]) -> EnumSpec:
    invalid_keys = set(raw.keys()) - set(EnumSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return EnumSpec(
        namespace=raw.get(EnumSpecKeys.NAMESPACE, None),
        name=raw[EnumSpecKeys.NAME],
        values=[parse_value_spec(value) for value in raw[EnumSpecKeys.VALUES]],
        features=frozenset(itertools.chain(*[parse_feature(feature) for feature in raw[EnumSpecKeys.FEATURES]])),
        docstring=raw.get(EnumSpecKeys.DOCSTRING, None),
    )

def load_spec(path: Path) -> EnumSpec:
    try:
        with path.open("r") as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f"Failed to load spec {path}") from e

    try:
        return parse_enum_spec(raw)
    except KeyError as e:
        raise RuntimeError(f"Failed to parse spec {path}") from e
    except ValueError as e:
        raise RuntimeError(f"Failed to parse spec {path}") from e
