from typing import (
    TypeVar,
    Optional,
    Callable,
)

T1 = TypeVar('T1')
T2 = TypeVar('T2')
def map_optional(x: Optional[T1], f: Callable[[T1], T2]) -> Optional[T2]:
    if x is None:
        return x
    else:
        return f(x)

