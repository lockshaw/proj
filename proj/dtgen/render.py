from enum import Enum, auto
from typing import (
    TextIO,
    Optional,
    Sequence,
    Iterator,
    TypeVar,
)
from .spec import (
    StructSpec,
    Feature,
    IncludeSpec,
)
from contextlib import contextmanager

class FileType(Enum):
    HEADER = auto()
    SOURCE = auto()

def includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.HASH:
        return [IncludeSpec(path='functional', system=True)]
    elif feature in [Feature.ORD, Feature.EQ]:
        return [IncludeSpec(path='tuple', system=True)]
    elif feature == Feature.JSON:
        return [IncludeSpec(path='nlohmann/json.hpp', system=False)]
    elif feature == Feature.FMT:
        raise NotImplementedError()
    else:
        return []

def infer_includes(struct_spec: StructSpec) -> Sequence[IncludeSpec]:
    result = list(struct_spec.includes)
    for feature in struct_spec.features:
        for include in includes_for_feature(feature):
            if include not in result:
                result.append(include)
    return result

def render_delete_default_constructor(spec: StructSpec, f: TextIO) -> None:
    f.write(f'{spec.name}() = delete;\n')

def render_includes(includes: Sequence[IncludeSpec], f: TextIO) -> None:
    for inc in includes:
        if inc.system:
            f.write(f'#include <{inc.path}>\n')
        else:
            f.write(f'#include "{inc.path}"\n')

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

def render_field_decls(spec: StructSpec, f: TextIO) -> None:
    for field in spec.fields:
        f.write(f'{field.type_} {field.name};\n')

def render_typename(spec: StructSpec, f: TextIO) -> None:
    if len(spec.template_params) == 0:
        f.write(spec.name)
    else:
        f.write(spec.name + '<' + ', '.join(spec.template_params) + '>')

def render_namespaced_typename(spec: StructSpec, f: TextIO) -> None:
    f.write(f'{spec.namespace}::')
    render_typename(spec, f)

@contextmanager
def render_struct_block(spec: StructSpec, f: TextIO) -> Iterator[None]:
    if len(spec.template_params) > 0:
        render_template_abs(spec.template_params, f)
    f.write(f'struct {spec.name}')
    with semicolon(f):
        with braces(f):
            yield 

def render_template_abs(params: Sequence[str], f: TextIO) -> None:
    f.write(''.join([
        'template <',
        ', '.join([f'typename {p}' for p in params]),
        '>\n'
    ]))

def render_template_args(params: Sequence[str], f: TextIO) -> None:
    f.write(''.join([
        '<',
        ', '.join(params),
        '>'
    ]))

def render_template_app(spec: StructSpec, f: TextIO, with_namespace: bool = False) -> None:
    if with_namespace:
        f.write(f'{spec.namespace}::')
    f.write(spec.name)
    if len(spec.template_params) > 0:
        render_template_args(spec.template_params, f)

def render_struct_impl_scope(spec: StructSpec, f: TextIO, return_type: Optional[str] = None) -> None:
    if len(spec.template_params) > 0:
        render_template_abs(spec.template_params, f)
    if return_type is not None:
        f.write(return_type + ' ')
    render_template_app(spec, f)
    f.write('::')

def render_constructor_sig(spec: StructSpec, f: TextIO) -> None:
    f.write(''.join([
        spec.name,
        '(',
        ', '.join([
            f'{field.type_} const &{field.name}'
            for field in spec.fields
        ]),
        ')',
    ]))

def render_constructor_decl(spec: StructSpec, f: TextIO) -> None:
    render_constructor_sig(spec, f)
    f.write(';\n')

def render_constructor_impl(spec: StructSpec, f: TextIO) -> None:
    render_struct_impl_scope(spec, f)
    render_constructor_sig(spec, f)
    f.write(' '.join([
        ':',
        ', '.join([
            f'{field.name}({field.name})'
            for field in spec.fields
        ]),
        '{}'
    ]))

def render_binop_decl(spec: StructSpec, op: str, f: TextIO) -> None:
    f.write(f'bool operator{op}({spec.name} const &) const;')

T = TypeVar('T')

def commad(ss: Sequence[T], f: TextIO) -> Iterator[T]:
    i = 0
    for s in ss:
        if i > 0:
            f.write(', ')
        yield s
        i += 1

def render_binop_impl(spec: StructSpec, op: str, f: TextIO) -> None:
    render_struct_impl_scope(spec, f, return_type='bool')
    f.write(f'operator{op}')
    with parens(f):
        render_template_app(spec, f)
        f.write(' const &other')
    f.write(' const')


    def render_tie(prefix: str):
        f.write('std::tie')
        with parens(f):
            for field in commad(spec.fields, f):
                f.write(prefix)
                f.write(field.name)

    with braces(f):
        with nlblock(f):
            f.write('return ')
            render_tie('this->')
            f.write(f' {op} ')
            render_tie('other.')
            f.write(';')

@contextmanager
def render_namespace_block(name: Optional[str], f: TextIO) -> Iterator[None]:
    if name is not None:
        f.write(f'namespace {name}')
        with braces(f):
            yield
        f.write('// namespace {name}\n')
    else:
        yield

def render_hash_decl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('std', f):
        render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('struct hash')
            with angles(f):
                render_namespaced_typename(spec, f)
            with braces(f):
                with semicolon(f):
                    f.write('size_t operator()')
                    with parens(f):
                        render_namespaced_typename(spec, f)
                        f.write(' const &')
                    f.write('const')

def render_hash_impl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('std', f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('size_t ')
        f.write('hash')
        with angles(f):
            render_template_app(spec, f, with_namespace=True)
        f.write('::operator()')
        with parens(f):
            render_namespaced_typename(spec, f)
            f.write(' const &x')
        f.write('const')
        with braces(f):
            f.write('size_t result = 0;\n')
            for field in spec.fields:
                f.write(f'result ^= std::hash<{field.type_}>{{}}(x.{field.name}) + 0x9e3779b9 + (result << 6) + (result >> 2);')
                # f.write(f'hash_combine(result, x.{field.name});\n')
            f.write('return result;\n')

def render_json_decl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('nlohmann', f):
        render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('struct adl_serializer')
            with angles(f):
                render_namespaced_typename(spec, f)
            with braces(f):
                f.write('static ')
                render_namespaced_typename(spec, f)
                f.write(' from_json(json const &);\n')
                f.write('static void to_json(json &, ')
                render_namespaced_typename(spec, f)
                f.write(' const &);\n')

def render_json_impl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('nlohmann', f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        render_namespaced_typename(spec, f)
        f.write(' adl_serializer')
        with angles(f):
            render_namespaced_typename(spec, f)
        f.write('::from_json(json const &j) ')
        with braces(f):
            with semicolon(f):
                f.write('return ')
                with braces(f):
                    for field in commad(spec.fields, f):
                        f.write(f'j.at("{field.json_key}").template get<{field.type_}>()')
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('void adl_serializer')
        with angles(f):
            render_namespaced_typename(spec, f)
        f.write('::to_json(json &j, ')
        render_namespaced_typename(spec, f)
        f.write(' const &v) ')
        with braces(f):
            f.write(f'j["__type"] = "{spec.name}";\n')
            for field in spec.fields:
                f.write(f'j["{field.json_key}"] = v.{field.name};\n')

def render_eq_function_decls(spec: StructSpec, f: TextIO) -> None:
    for op in ['==', '!=']:
        render_binop_decl(spec, op, f)

def render_eq_function_impls(spec: StructSpec, f: TextIO) -> None:
    for op in ['==', '!=']:
        render_binop_impl(spec, op, f)
    
def render_ord_function_decls(spec: StructSpec, f: TextIO) -> None:
    for op in ['<', '>', '<=', '>=']:
        render_binop_decl(spec, op, f)

def render_ord_function_impls(spec: StructSpec, f: TextIO) -> None:
    for op in ['<', '>', '<=', '>=']:
        render_binop_impl(spec, op, f)

def render_decls(spec: StructSpec, f: TextIO) -> None:
    # render_includes(infer_includes(spec), f)
    with render_namespace_block(spec.namespace, f):
        with render_struct_block(spec, f):
            render_delete_default_constructor(spec, f)
            render_constructor_decl(spec, f)
            if Feature.EQ in spec.features:
                f.write('\n')
                render_eq_function_decls(spec, f)
            if Feature.ORD in spec.features:
                f.write('\n')
                render_ord_function_decls(spec, f)
            f.write('\n')
            render_field_decls(spec, f)

def render_impls(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        render_constructor_impl(spec, f)
        if Feature.EQ in spec.features:
            render_eq_function_impls(spec, f)
        if Feature.ORD in spec.features:
            render_ord_function_impls(spec, f)
    if Feature.HASH in spec.features:
        f.write('\n')
        render_hash_impl(spec, f)
    if Feature.JSON in spec.features:
        f.write('\n')
        render_json_impl(spec, f)

def render_header(spec: StructSpec, f: TextIO) -> None:
    render_includes(infer_includes(spec), f)
    f.write('\n')
    render_decls(spec, f)

    if Feature.HASH in spec.features:
        f.write('\n')
        render_hash_decl(spec, f)

    if Feature.JSON in spec.features:
        f.write('\n')
        render_json_decl(spec, f)

    if len(spec.template_params) > 0:
        f.write('\n')
        render_impls(spec, f)

def render_source(spec: StructSpec, f: TextIO) -> None:
    if len(spec.template_params) == 0:
        render_impls(spec, f)

# @contextmanager
# def configure_output(p: Optional[Path]) -> Iterator[TextIO]:
#     if p is None:
#         f = io.StringIO()
#         yield f
#         sys.stdout.write(f.getvalue())
#     else:
#         with p.open('w') as f:
#             yield f

# def main(args: Args) -> None:
#     struct_spec = load_spec(args.input_path)
#     with configure_output(args.output_path) as f:
#         if args.file_type == FileType.HEADER:
#             render_header(struct_spec, f)
#         else:
#             render_source(struct_spec, f)

# if __name__ == '__main__':
#     import argparse

#     p = argparse.ArgumentParser()
#     p.add_argument('input_path', type=Path)
#     p.add_argument('-o', '--output-path', type=Path)
#     p.add_argument('-t', '--type', choices=['hdr', 'src'])
#     raw_args = p.parse_args()

#     file_type: FileType
#     if raw_args.type == 'hdr':
#         file_type = FileType.HEADER
#     elif raw_args.type == 'src':
#         file_type = FileType.SOURCE
#     else:
#         raise ValueError(f'Unknown file type {raw_args.type}')

#     file_type
#     args = Args(
#         input_path=raw_args.input_path,
#         output_path=raw_args.output_path,
#         file_type=file_type,
#     )
#     main(args)
