from dataclasses import dataclass
from proj.strenum import StrEnum
from enum import (
    Enum,
    auto,
)
from typing import (
    Sequence,
    Optional,
    FrozenSet,
    Any,
    Mapping,
    List,
)
from proj.includes import (
    IncludeSpec,
    parse_include_spec,
)
from proj.json import Json
import itertools


class Feature(Enum):
    JSON_SERIALIZE = auto()
    JSON_DESERIALIZE = auto()
    EQ = auto()
    ORD = auto()
    HASH = auto()
    FMT = auto()
    RAPIDCHECK = auto()

    def json(self) -> Json:
        return self.name


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_: str
    docstring: Optional[str]
    indirect: bool
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
            "type_": self.type_,
            "docstring": self.docstring,
            "indirect": self.indirect,
            "json_key": self.json_key,
        }


@dataclass(frozen=True)
class StructSpec:
    includes: Sequence[IncludeSpec]
    src_includes: Sequence[IncludeSpec]
    post_includes: Sequence[IncludeSpec]
    fwd_decls: Sequence[str]
    namespace: Optional[str]
    template_params: Sequence[str]
    name: str
    fields: Sequence[FieldSpec]
    features: FrozenSet[Feature]
    docstring: Optional[str]

    def json(self) -> Json:
        return {
            "includes": [inc.json() for inc in self.includes],
            "src_includes": [inc.json() for inc in self.src_includes],
            "post_includes": [inc.json() for inc in self.post_includes],
            "fwd_decls": self.fwd_decls,
            "namespace": self.namespace,
            "template_params": list(self.template_params),
            "name": self.name,
            "fields": [field.json() for field in self.fields],
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
    elif raw == "eq":
        return [Feature.EQ]
    elif raw == "ord":
        return [Feature.ORD]
    elif raw == "hash":
        return [Feature.HASH]
    elif raw == "rapidcheck":
        return [Feature.RAPIDCHECK]
    elif raw == "fmt":
        return [Feature.FMT]
    else:
        raise ValueError(f"Unknown feature: {raw}")

class FieldSpecKeys(StrEnum):
    NAME = 'name'
    TYPE = 'type'
    DOCSTRING = 'docstring'
    INDIRECT = 'indirect'
    JSON_KEY = 'json_key'

def parse_field_spec(raw: Mapping[str, Any]) -> FieldSpec:
    invalid_keys = set(raw.keys()) - set(FieldSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return FieldSpec(
        name=raw[FieldSpecKeys.NAME],
        type_=raw[FieldSpecKeys.TYPE],
        docstring=raw.get(FieldSpecKeys.DOCSTRING, None),
        indirect=raw.get(FieldSpecKeys.INDIRECT, False),
        _json_key=raw.get(FieldSpecKeys.JSON_KEY, None),
    )

class StructSpecKeys(StrEnum):
    NAMESPACE = 'namespace'
    INCLUDES = 'includes'
    SRC_INCLUDES = 'src_includes'
    POST_INCLUDES = 'post_includes'
    FWD_DECLS = 'fwd_decls'
    TEMPLATE_PARAMS = 'template_params'
    NAME = 'name'
    FIELDS = 'fields'
    FEATURES = 'features'
    DOCSTRING = 'docstring'

def parse_struct_spec(raw: Mapping[str, Any]) -> StructSpec:
    invalid_keys = set(raw.keys()) - set(StructSpecKeys)
    if len(invalid_keys) > 0:
        invalid_keys_str = ', '.join(map(repr, invalid_keys))
        raise ValueError(f'Unexpected keys encountered: {invalid_keys_str}')

    return StructSpec(
        namespace=raw.get(StructSpecKeys.NAMESPACE, None),
        includes=[parse_include_spec(include) for include in raw.get(StructSpecKeys.INCLUDES, ())],
        src_includes=[
            parse_include_spec(src_include)
            for src_include in raw.get(StructSpecKeys.SRC_INCLUDES, ())
        ],
        post_includes=[
            parse_include_spec(post_include)
            for post_include in raw.get(StructSpecKeys.POST_INCLUDES, ())
        ],
        fwd_decls=raw.get(StructSpecKeys.FWD_DECLS, ()),
        template_params=raw.get(StructSpecKeys.TEMPLATE_PARAMS, ()),
        name=raw[StructSpecKeys.NAME],
        fields=[parse_field_spec(field) for field in raw[StructSpecKeys.FIELDS]],
        features=frozenset(itertools.chain(*[parse_feature(feature) for feature in raw[StructSpecKeys.FEATURES]])),
        docstring=raw.get(StructSpecKeys.DOCSTRING, None),
    )


# def load_spec(raw: Json) -> StructSpec:
#     try:
#         spec = parse_struct_spec(raw)
#         if Feature.RAPIDCHECK in spec.features and any(
#             field.indirect for field in spec.fields
#         ):
#             raise RuntimeError(
#                 f"rapidcheck not supported for indirect fields, found in spec"
#             )
#         return spec
#     except KeyError as e:
#         raise RuntimeError(f"Failed to parse spec {path}") from e
