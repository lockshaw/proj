from typing import (
    TypeVar,
    Optional,
    Callable,
    Collection,
    FrozenSet,
    Iterable,
    Iterator,
)
from functools import reduce
from pathlib import PurePath, Path
import re
import logging

_l = logging.getLogger(__name__)

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")


def concatmap(c: Iterable[T1], f: Callable[[T1], Iterable[T2]]) -> Iterable[T2]:
    for e in c:
        f_result = f(e)
        yield from f_result


def filtermap(c: Iterable[T1], f: Callable[[T1], Optional[T2]]) -> Iterable[T2]:
    for e in c:
        f_result = f(e)
        if f_result is None:
            continue
        yield f_result


def union_all(c: Iterable[FrozenSet[T]]) -> FrozenSet[T]:
    return reduce(lambda accum, x: accum.union(x), c, frozenset())


def get_only(c: Collection[T]) -> T:
    assert len(c) == 1
    return next(iter(c))


def require_nonnull(x: Optional[T]) -> T:
    assert x is not None
    return x


def map_optional(x: Optional[T1], f: Callable[[T1], T2]) -> Optional[T2]:
    if x is None:
        return x
    else:
        return f(x)

def default_to(x: Optional[T], y: T) -> T:
    if x is None:
        return y
    else:
        return x

def common_ancestors(lhs: PurePath, rhs: PurePath) -> Iterator[PurePath]:
    for l, r in zip(list(lhs.parents)[::-1], list(rhs.parents)[::-1]):
        if l == r:
            yield l
        else:
            break

def nearest_common_ancestor(lhs: PurePath, rhs: PurePath) -> PurePath:
    for anc in common_ancestors(lhs, rhs):
        pass
    assert isinstance(anc, PurePath)
    return anc


def num_true(c: Iterable[bool]) -> int:
    return sum(int(b) for b in c)

P = TypeVar('P', PurePath, Path)

def with_suffixes(p: P, suffs: str) -> P:
    name = p.name
    while "." in name:
        name = name[: name.rfind(".")]
    return p.with_name(name + suffs)

def with_suffix_appended(p: P, suff: str) -> P:
    assert suff.startswith(".")
    return p.with_name(p.name + suff)

def with_suffix_removed(p: P, n: int = 1) -> P:
    for _ in range(n):
        p = p.with_suffix("")
    return p

def saturating_relative_to(child: PurePath, parent: PurePath) -> Optional[PurePath]:
    result: Optional[PurePath]
    if is_relative_to(parent, child):
        result = PurePath('.')
    elif is_relative_to(child, parent):
        result = child.relative_to(parent)
    else:
        result = None
    _l.debug('saturating_relative_to(%s, %s) -> %s', child, parent, result)
    return result

def is_relative_to(child: PurePath, parent: PurePath) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False
