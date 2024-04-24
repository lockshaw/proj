from typing import Mapping, Sequence, Union
from typing_extensions import TypeAlias, Protocol
import hashlib
import json

Json: TypeAlias = Union[Mapping[str, "Json"], Sequence["Json"], str, int, float, bool, None]

class SupportsJson(Protocol):
    def json(self) -> Json: ...

def json_hash(j: Json) -> bytes:
    return hashlib.md5(json.dumps(
        j,
        sort_keys=True,
    ).encode('utf-8')).digest()

def hash_by_json(v: SupportsJson) -> bytes:
    return json_hash(v.json())
