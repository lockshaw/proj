from typing import (
    Mapping, 
    Sequence, 
    Union,
    Callable,
    Tuple,
    TypeVar,
    cast,
    Optional,
)
from typing_extensions import (
    TypeAlias, 
    Protocol,
)
import hashlib
import json
from pathlib import Path
from immutables import Map

Json: TypeAlias = Union[Mapping[str, "Json"], Sequence["Json"], str, int, float, bool, None]

def loads(s: str) -> Json:
    return cast(Json, json.loads(s))

def dumps(j: Json, sort_keys: bool = False, indent: Optional[int] = None) -> str:
    return json.dumps(j, sort_keys=sort_keys, indent=indent)

def require_str(x: object) -> str:
    assert isinstance(x, str)
    return x

def require_bool(x: object) -> bool:
    assert isinstance(x, bool)
    return x

def require_path(x: object) -> Path:
    s = require_str(x)
    return Path(s)

T = TypeVar('T')
def require_list_of(x: object, check_element: Callable[[object], T]) -> Tuple[T, ...]:
    assert isinstance(x, list)
    return tuple(check_element(e) for e in x)

K = TypeVar('K')
V = TypeVar('V')
def require_dict_of(x: object, check_key: Callable[[object], K], check_value: Callable[[object], V]) -> Map[K, V]:
    assert isinstance(x, dict)

    return Map({
        check_key(k): check_value(v) for k, v in x.items()
    })


class SupportsJson(Protocol):
    def json(self) -> Json: ...

def json_hash(j: Json) -> bytes:
    return hashlib.md5(json.dumps(
        j,
        sort_keys=True,
    ).encode('utf-8')).digest()

def hash_by_json(v: SupportsJson) -> bytes:
    return json_hash(v.json())
