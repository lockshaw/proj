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
def sline(f: TextIO) -> Iterator[None]:
    yield
    f.write(';\n')

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

def parse_include_spec(raw: str) -> IncludeSpec:
    if raw.startswith('<') and raw.endswith('>'):
        return IncludeSpec(path=raw[1:-1], system=True)
    else:
        return IncludeSpec(path=raw, system=False)

def render_includes(includes: Sequence[IncludeSpec], f: TextIO) -> None:
    for inc in includes:
        if inc.system:
            f.write(f'#include <{inc.path}>\n')
        else:
            f.write(f'#include "{inc.path}"\n')

@contextmanager
def render_switch_block(cond: str, f: TextIO) -> Iterator[None]:
    f.write(f'switch ({cond})')
    with braces(f):
        yield

@contextmanager
def render_namespace_block(name: Optional[str], f: TextIO) -> Iterator[None]:
    if name is not None:
        f.write(f'namespace {name}')
        with braces(f):
            yield
        f.write('// namespace {name}\n')
    else:
        yield

def render_template_abs(params: Sequence[str], f: TextIO) -> None:
    f.write(''.join([
        'template <',
        ', '.join([f'typename {p}' for p in params]),
        '>\n'
    ]))

def render_template_app(func: str, params: Sequence[str], f: TextIO) -> None:
    f.write(func)
    with angles(f):
        for p in commad(params, f):
            f.write(p)

@contextmanager
def render_struct_block(name: str, template_params: Sequence[str], f: TextIO, specialization: bool = False) -> Iterator[None]:
    if len(template_params) > 0 or specialization:
        render_template_abs(template_params, f)
    f.write(f'struct {name}')
    with semicolon(f):
        with braces(f):
            yield 

def render_function_declaration(*, template_params: Sequence[str] = tuple(), is_static: bool = False, name: str, return_type: str, args: Sequence[str], is_const: bool=False, f: TextIO) -> None:
    if len(template_params) > 0:
        render_template_abs(template_params, f)
    if is_static:
        f.write('static ')
    f.write(f'{return_type} {name}')
    with parens(f):
        for arg in commad(args, f):
            f.write(arg)
    if is_const:
        f.write(' const')
    f.write(';\n')

@contextmanager
def render_function_definition(*, template_params: Sequence[str] = tuple(), return_type: str, name: str, args: Sequence[str], is_const: bool = False, f: TextIO) -> Iterator[None]:
    if len(template_params) > 0:
        render_template_abs(template_params, f)
    f.write(f'{return_type} {name}')
    with parens(f):
        for arg in commad(args, f):
            f.write(arg)
    if is_const:
        f.write(' const')
    with braces(f):
        yield
    f.write('\n')

def render_static_assert(cond: str, message: str, f: TextIO):
    f.write(f'static_assert({cond}, "{message}");')

T = TypeVar('T')

def sepbyd(ss: Sequence[T], sep: str, f: TextIO) -> Iterator[T]:
    i = 0
    for s in ss:
        if i > 0:
            f.write(sep)
        yield s
        i += 1

def commad(ss: Sequence[T], f: TextIO) -> Iterator[T]:
    return sepbyd(ss, ', ', f)

def slined(ss: Sequence[T], f: TextIO) -> Iterator[T]:
    return sepbyd(ss, ';\n', f)

def lined(ss: Sequence[T], f: TextIO) -> Iterator[T]:
    return sepbyd(ss, '\n', f)
