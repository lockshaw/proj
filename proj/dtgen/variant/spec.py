from dataclasses import dataclass
from proj.strenum import StrEnum
from enum import (
    Enum,
    auto,
)
from typing import (
    FrozenSet,
    Optional,
    Sequence,
    Any,
    Mapping,
    List,
)
from proj.includes import (
    IncludeSpec,
    parse_include_spec,
)
import proj.toml as toml
from pathlib import Path
from proj.json import Json
import itertools


class Feature(Enum):
    EQ = auto()
    ORD = auto()
    HASH = auto()
    JSON_SERIALIZE = auto()
    JSON_DESERIALIZE = auto()
    FMT = auto()
    RAPIDCHECK = auto()

    def json(self) -> Json:
        return self.name

@dataclass(frozen=True)
class ValueSpec:
    type_: str
    docstring: Optional[str]
    _key: Optional[str]
    _json_key: Optional[str]
    _fmt_key: Optional[str]
    _indirect: Optional[bool]

    def json(self) -> Json:
        return {
            "type_": self.type_,
            "docstring": self.docstring,
            "key": self.key,
            "json_key": self.json_key,
            "fmt_key": self.fmt_key,
        }

    @property
    def key(self) -> str:
        if self._key is None:
            return self.type_
        else:
            return self._key

    @property
    def indirect(self) -> bool:
        if self._indirect is None:
            return False
        else:
            return self._indirect


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
    post_includes: Sequence[IncludeSpec]
    fwd_decls: Sequence[str]
    namespace: Optional[str]
    template_params: Sequence[str]
    name: str
    values: Sequence[ValueSpec]
    features: FrozenSet[Feature]
    explicit_constructors: bool
    docstring: Optional[str]

    def json(self) -> Json:
        return {
            "includes": [include.json() for include in self.includes],
            "src_includes": [include.json() for include in self.src_includes],
            "post_includes": [include.json() for include in self.post_includes],
            "fwd_decls": self.fwd_decls,
            "namespace": self.namespace,
            "template_params": list(self.template_params),
            "name": self.name,
            "values": [value.json() for value in self.values],
            "features": [feature.json() for feature in self.features],
            "explicit_constructors": self.explicit_constructors,
            "docstring": self.docstring,
        }


def parse_feature(raw: str) -> List[Feature]:
    if raw == "eq":
        return [Feature.EQ]
    elif raw == "ord":
        return [Feature.ORD]
    elif raw == "hash":
        return [Feature.HASH]
    elif raw == "json":
        return [Feature.JSON_SERIALIZE, Feature.JSON_DESERIALIZE]
    elif raw == "json_serialize":
        return [Feature.JSON_SERIALIZE]
    elif raw == "fmt":
        return [Feature.FMT]
    elif raw == "rapidcheck":
        return [Feature.RAPIDCHECK]
    else:
        raise ValueError(f"Unknown feature: {raw}")

class ValueSpecKeys(StrEnum):
    TYPE = 'type'
    DOCSTRING = 'docstring'
    KEY = 'key'
    JSON_KEY = 'json_key'
    FMT_KEY = 'fmt_key'
    INDIRECT = 'indirect'

def parse_value_spec(raw: Mapping[str, Any]) -> ValueSpec:
    invalid_keys = set(raw.keys()) - set(ValueSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return ValueSpec(
        type_=raw[ValueSpecKeys.TYPE],
        docstring=raw.get(ValueSpecKeys.DOCSTRING, None),
        _key=raw.get(ValueSpecKeys.KEY, None),
        _json_key=raw.get(ValueSpecKeys.JSON_KEY, None),
        _fmt_key=raw.get(ValueSpecKeys.FMT_KEY, None),
        _indirect=raw.get(ValueSpecKeys.INDIRECT, None),
    )


class VariantSpecKeys(StrEnum):
    NAMESPACE = 'namespace'
    INCLUDES = 'includes'
    SRC_INCLUDES = 'src_includes'
    POST_INCLUDES = 'post_includes'
    FWD_DECLS = 'fwd_decls'
    EXPLICIT_CONSTRUCTORS = 'explicit_constructors'
    TEMPLATE_PARAMS = 'template_params'
    NAME = 'name'
    VALUES = 'values'
    FEATURES = 'features'
    DOCSTRING = 'docstring'

def parse_variant_spec(raw: Mapping[str, Any]) -> VariantSpec:
    invalid_keys = set(raw.keys()) - set(VariantSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return VariantSpec(
        namespace=raw.get(VariantSpecKeys.NAMESPACE, None),
        includes=[parse_include_spec(include) for include in raw.get(VariantSpecKeys.INCLUDES, ())],
        src_includes=[
            parse_include_spec(include) for include in raw.get(VariantSpecKeys.SRC_INCLUDES, ())
        ],
        post_includes=[
            parse_include_spec(post_include)
            for post_include in raw.get(VariantSpecKeys.POST_INCLUDES, ())
        ],
        fwd_decls=raw.get(VariantSpecKeys.FWD_DECLS, ()),
        explicit_constructors=raw.get(VariantSpecKeys.EXPLICIT_CONSTRUCTORS, True),
        template_params=raw.get(VariantSpecKeys.TEMPLATE_PARAMS, ()),
        name=raw[VariantSpecKeys.NAME],
        values=[parse_value_spec(value) for value in raw[VariantSpecKeys.VALUES]],
        features=frozenset(itertools.chain(*[parse_feature(feature) for feature in raw[VariantSpecKeys.FEATURES]])),
        docstring=raw.get(VariantSpecKeys.DOCSTRING, None),
    )


def load_spec(path: Path) -> VariantSpec:
    try:
        with path.open("r") as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f"Failed to load spec {path}") from e
    try:
        spec = parse_variant_spec(raw)
        if any(val.method_key is not None for val in spec.values) and any(
            val.method_key is None for val in spec.values
        ):
            raise RuntimeError(
                f"Failed to load spec {path}. Expected either all values to have a key or no values to have a key, but found otherwise."
            )
        return spec
    except KeyError as e:
        raise RuntimeError(f"Failed to parse spec {path}") from e
    except ValueError as e:
        raise RuntimeError(f"Failed to parse spec {path}") from e
