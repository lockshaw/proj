import sys
from typing import (
    Dict,
)

if sys.version_info[:2] >= (3, 11): 
    from tomllib import (
        loads as _loads, 
        TOMLDecodeError as TOMLDecodeError,
    )
else:
    from toml import (
        loads as _loads, 
        TOMLDecodeError as TOMLDecodeError,
    )

def loads(s: str) -> Dict[str, object]:
    return _loads(s)
