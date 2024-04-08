from dataclasses import dataclass
from contextlib import contextmanager
from typing import (
    Iterator,
    TextIO,
    Sequence,
    Optional,
    TypeVar,
)

@contextmanager
def semicolon(f: TextIO) -> Iterator[None]:
    yield
    f.write(';')

@contextmanager
def nlblock(f: TextIO) -> Iterator[None]:
    f.write('\n')
    yield
    f.write('\n')

@contextmanager
def braces(f: TextIO) -> Iterator[None]:
    f.write('{')
    yield
    f.write('}')

@contextmanager
def parens(f: TextIO) -> Iterator[None]:
    f.write('(')
    yield
    f.write(')')

@contextmanager
def angles(f: TextIO) -> Iterator[None]:
    f.write('<')
    yield
    f.write('>')

@dataclass(frozen=True)
class IncludeSpec:
    path: str
    system: bool

def render_includes(includes: Sequence[IncludeSpec], f: TextIO) -> None:
    for inc in includes:
        if inc.system:
            f.write(f'#include <{inc.path}>\n')
        else:
            f.write(f'#include "{inc.path}"\n')

@contextmanager
def render_namespace_block(name: Optional[str], f: TextIO) -> Iterator[None]:
    if name is not None:
        f.write(f'namespace {name}')
        with braces(f):
            yield
        f.write('// namespace {name}\n')
    else:
        yield

T = TypeVar('T')

def commad(ss: Sequence[T], f: TextIO) -> Iterator[T]:
    i = 0
    for s in ss:
        if i > 0:
            f.write(', ')
        yield s
        i += 1
