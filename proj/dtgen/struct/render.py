from typing import (
    TextIO,
    Optional,
    Sequence,
    Iterator,
    Callable,
)
from .spec import (
    StructSpec,
    Feature,
)
from contextlib import contextmanager
from proj.dtgen.render_utils import (
    IncludeSpec,
    render_includes,
    render_namespace_block,
    semicolon,
    nlblock,
    braces,
    parens,
    angles,
    commad,
    render_template_abs,
)
import proj.dtgen.render_utils as render_utils
import io
import itertools

def header_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.HASH:
        return [IncludeSpec(path='functional', system=True)]
    elif feature in [Feature.ORD, Feature.EQ]:
        return [IncludeSpec(path='tuple', system=True)]
    elif feature == Feature.JSON:
        return [IncludeSpec(path='nlohmann/json.hpp', system=False)]
    elif feature == Feature.RAPIDCHECK:
        return [IncludeSpec(path='rapidcheck.h', system=False)]
    elif feature == Feature.FMT:
        return [
            IncludeSpec(path='ostream', system=True),
            IncludeSpec(path='fmt/format.h', system=False),
        ]
    else:
        return []

def impl_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.FMT:
        return [
            IncludeSpec(path='sstream', system=True),
            # IncludeSpec(path='utils/fmt.h', system=False),
        ]
    else:
        return []

def header_includes_for_features(spec: StructSpec) -> Sequence[IncludeSpec]:
    return list(set(itertools.chain.from_iterable(header_includes_for_feature(feature) for feature in spec.features)))

def infer_header_includes(spec: StructSpec) -> Sequence[IncludeSpec]:
    return list(set([
        *spec.includes, 
        *header_includes_for_features(spec=spec),
    ]))

def impl_includes_for_features(spec: StructSpec) -> Sequence[IncludeSpec]:
    return list(set(itertools.chain.from_iterable(impl_includes_for_feature(feature) for feature in spec.features)))


def infer_impl_includes(spec: StructSpec) -> Sequence[IncludeSpec]:
    return list(set([
        *spec.src_includes, 
        *impl_includes_for_features(spec=spec),
    ]))

def render_delete_default_constructor(spec: StructSpec, f: TextIO) -> None:
    f.write(f'{spec.name}() = delete;\n')

def render_field_decls(spec: StructSpec, f: TextIO) -> None:
    for field in spec.fields:
        f.write(f'{field.type_} {field.name};\n')

@contextmanager
def render_struct_block(spec: StructSpec, f: TextIO) -> Iterator[None]:
    with render_utils.render_struct_block(name=spec.name, template_params=spec.template_params, f=f):
        yield

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

def render_constructor_decl(spec: StructSpec, f: TextIO) -> None:
    render_utils.render_function_declaration(
        template_params=[],
        is_static=False,
        is_explicit=True,
        return_type=None,
        name=spec.name,
        args=[
            f'{field.type_} const &{field.name}'
            for field in spec.fields
        ],
        is_const=False,
        f=f,
    )

def render_typename(*, spec: StructSpec, qualified: bool, f: TextIO) -> None:
    if qualified:
        f.write(f'::{spec.namespace}::')
    if len(spec.template_params) > 0:
        render_utils.render_template_app(spec.name, params=spec.template_params, f=f)
    else:
        f.write(spec.name)

def get_typename(*, spec: StructSpec, qualified: bool) -> str:
    f = io.StringIO() 
    render_typename(spec=spec, qualified=qualified, f=f)
    return f.getvalue()

def render_constructor_impl(spec: StructSpec, f: TextIO) -> None:
    with render_utils.render_function_definition(
        template_params=spec.template_params,
        return_type=None,
        name=f'{get_typename(spec=spec, qualified=False)}::{spec.name}',
        args=[
            f'{field.type_} const &{field.name}'
            for field in spec.fields
        ],
        is_const=False,
        initializer_list=[
            f'{field.name}({field.name})'
            for field in spec.fields
        ],
        f=f,
    ):
        pass # no function body

def render_binop_decl(spec: StructSpec, op: str, f: TextIO) -> None:
    f.write(f'bool operator{op}({spec.name} const &) const;')

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

def render_hash_decl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('std', f):
        render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('struct hash')
            with angles(f):
                render_typename(spec=spec, qualified=True, f=f)
            with braces(f):
                with semicolon(f):
                    f.write('size_t operator()')
                    with parens(f):
                        render_typename(spec=spec, qualified=True, f=f)
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
            render_typename(spec=spec, qualified=True, f=f)
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
                render_typename(spec=spec, qualified=True, f=f)
            with braces(f):
                f.write('static ')
                render_typename(spec=spec, qualified=True, f=f)
                f.write(' from_json(json const &);\n')
                f.write('static void to_json(json &, ')
                render_typename(spec=spec, qualified=True, f=f)
                f.write(' const &);\n')

def render_json_checks(spec: StructSpec, f: TextIO) -> None:
    assert len(spec.template_params) == 0

    with render_namespace_block('nlohmann', f):
        with semicolon(f):
            for field in spec.fields:
                f.write('static_assert')
                with parens(f):
                    f.write('::FlexFlow::is_json_serializable_v')
                    with angles(f):
                        f.write(field.type_)
                    f.write(f', "Field {field.name} of type {field.type_} should be json-serializeable, but is not"')
    # with render_namespace_block('nlohmann', f):
    #     with semicolon(f):
    #         for field in spec.fields:
    #             f.write('static_assert')

def render_json_impl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('nlohmann', f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        render_typename(spec=spec, qualified=True, f=f)
        f.write(' adl_serializer')
        with angles(f):
            render_typename(spec=spec, qualified=True, f=f)
        f.write('::from_json(json const &j) ')
        with braces(f):
            with semicolon(f):
                f.write('return ')
                render_typename(spec=spec, qualified=True, f=f)
                with braces(f):
                    for field in commad(spec.fields, f):
                        f.write(f'j.at("{field.json_key}").template get<{field.type_}>()')
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('void adl_serializer')
        with angles(f):
            render_typename(spec=spec, qualified=True, f=f)
        f.write('::to_json(json &j, ')
        render_typename(spec=spec, qualified=True, f=f)
        f.write(' const &v) ')
        with braces(f):
            f.write(f'j["__type"] = "{spec.name}";\n')
            for field in spec.fields:
                f.write(f'j["{field.json_key}"] = v.{field.name};\n')

def render_fmt_decl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('std::string format_as')
            with parens(f):
                render_typename(spec=spec, qualified=False, f=f)
                f.write(' const &')

        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('std::ostream &operator<<')
            with parens(f):
                f.write('std::ostream &, ')
                render_typename(spec=spec, qualified=False, f=f)
                f.write(' const &')


def render_fmt_impl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('std::string format_as')
        with parens(f):
            render_typename(spec=spec, qualified=False, f=f)
            f.write(' const &x')
        with braces(f):
            f.write('std::ostringstream oss;\n')
            f.write(f'oss << "<{spec.name}";\n')
            for field in spec.fields:
                f.write(f'oss << " {field.name}=" << x.{field.name};\n')
            f.write('oss << ">";\n')
            f.write('return oss.str();')
        
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('std::ostream &operator<<(std::ostream &s, ')
        render_typename(spec=spec, qualified=False, f=f)
        f.write(' const &x')
        f.write(') ')
        with braces(f):
            f.write('return s << fmt::to_string(x);')

def render_rapidcheck_decl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('rc', f):
        render_template_abs(spec.template_params, f)
        with semicolon(f):
            f.write('struct Arbitrary')
            with angles(f):
                render_typename(spec=spec, qualified=True, f=f)
            with braces(f):
                f.write('static Gen')
                with angles(f):
                    render_typename(spec=spec, qualified=True, f=f)
                f.write(' arbitrary();\n')

def render_rapidcheck_impl(spec: StructSpec, f: TextIO) -> None:
    with render_namespace_block('rc', f):
        if len(spec.template_params) > 0:
            render_template_abs(spec.template_params, f)
        f.write('Gen')
        with angles(f):
            render_typename(spec=spec, qualified=True, f=f)
        f.write(' Arbitrary')
        with angles(f):
            render_typename(spec=spec, qualified=True, f=f)
        f.write('::arbitrary() ')
        with braces(f):
            with semicolon(f):
                f.write('return gen::construct')
                with angles(f):
                    render_typename(spec=spec, qualified=True, f=f)
                with parens(f):
                    for field in commad(spec.fields, f):
                        f.write(f'gen::arbitrary<{field.type_}>()')

# def render_serialize_impl(spec: StructSpec, f: TextIO) -> None:
#     with render_namespace_block('FlexFlow', f):
#         if len(spec.template_params) > 0:
#             render_template_abs(spec.template_params, f)
#         f.write('Gen')
#         with angles(f):
#             render_typename(spec=spec, qualified=True, f=f)
#         f.write(' Arbitrary')
#         with angles(f):
#             render_typename(spec=spec, qualified=True, f=f)
#         f.write('::arbitrary() ')
#         with braces(f):
#             with semicolon(f):
#                 f.write('return gen::construct')
#                 with angles(f):
#                     render_typename(spec=spec, qualified=True, f=f)
#                 with parens(f):
#                     for field in commad(spec.fields, f):
#                         f.write(f'gen::arbitrary<{field.type_}>()')

# def render_serialize_fwd_decls(f: TextIO) -> None:
#     with render_namespace_block('FlexFlow', f):
#         f.write('struct Serializer;')
#         f.write('struct Deserializer;')

# def render_serialize_decls(spec: StructSpec, f: TextIO) -> None:
#     with render_namespace_block(spec.namespace, f):
#         if len(spec.template_params) > 0:
#             render_template_abs(spec.template_params, f)
#         with semicolon(f):
#             f.write('void serialize')
#             with parens(f):
#                 f.write('Serializer &, ')
#                 render_typename(spec, f)
#                 f.write(' const &')
#         with 

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
            if len(spec.fields) > 0:
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
        if len(spec.fields) > 0:
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
    if Feature.RAPIDCHECK in spec.features:
        f.write('\n')
        render_rapidcheck_impl(spec, f)
    if Feature.FMT in spec.features:
        f.write('\n')
        render_fmt_impl(spec, f)

def render_header(spec: StructSpec, f: TextIO) -> None:
    render_includes(infer_header_includes(spec), f)
    if len(spec.template_params) > 0:
        render_includes(infer_impl_includes(spec), f)

    f.write('\n')
    
    render_decls(spec, f)

    # if Feature.SERIALIZE in spec.features:
    #     f.write('\n')
    #     render_serialize_fwd_decls(f)

    if Feature.HASH in spec.features:
        f.write('\n')
        render_hash_decl(spec, f)

    if Feature.JSON in spec.features:
        f.write('\n')
        render_json_decl(spec, f)

    if Feature.RAPIDCHECK in spec.features:
        f.write('\n')
        render_rapidcheck_decl(spec, f)

    if Feature.FMT in spec.features:
        f.write('\n')
        render_fmt_decl(spec, f)

    if len(spec.template_params) > 0:
        f.write('\n')
        render_impls(spec, f)

def render_source(spec: StructSpec, f: TextIO) -> None:
    if len(spec.template_params) == 0:
        render_includes(infer_impl_includes(spec), f)
        f.write('\n')

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
