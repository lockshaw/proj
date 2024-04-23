from .spec import (
    VariantSpec,
    Feature,
)
from typing import (
    TextIO,
    Sequence,
)
from proj.dtgen.render_utils import (
    render_namespace_block,
    render_struct_block,
    render_template_abs,
    render_function_definition,
    render_function_declaration,
    render_static_assert,
    lined,
    sepbyd,
    semicolon,
    render_template_app,
    IncludeSpec,
    render_includes,
    sline,
    braces,
    render_switch_block,
    render_case,
    render_default_case,
)
import io
import itertools

def header_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.HASH:
        return [IncludeSpec(path='functional', system=True)]
    elif feature == Feature.JSON:
        return [
            IncludeSpec(path='nlohmann/json.hpp', system=False),
        ]
    elif feature == Feature.FMT:
        return [
            IncludeSpec(path='ostream', system=True),
            IncludeSpec(path='fmt/format.h', system=False),
        ]
    else:
        return []

def source_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.JSON:
        return [
            IncludeSpec(path='fmt/format.h', system=False),
            IncludeSpec(path='stdexcept', system=True),
        ]
    elif feature == Feature.FMT:
        return [
            IncludeSpec(path='sstream', system=True),
        ]
    else:
        return []

def header_includes_for_features(spec: VariantSpec) -> Sequence[IncludeSpec]:
    return list(set(itertools.chain.from_iterable(header_includes_for_feature(feature) for feature in spec.features)))

def infer_header_includes(spec: VariantSpec) -> Sequence[IncludeSpec]:
    return list(set([
        *spec.includes, 
        IncludeSpec(path='variant', system=True),
        IncludeSpec(path='type_traits', system=True),
        IncludeSpec(path='cstddef', system=True),
        *header_includes_for_features(spec=spec),
    ]))

def infer_source_includes(spec: VariantSpec) -> Sequence[IncludeSpec]:
    return list(set(itertools.chain.from_iterable(source_includes_for_feature(feature) for feature in spec.features)))

def render_visit_method(spec: VariantSpec, is_const: bool, f: TextIO) -> None:
    with render_function_definition(
        template_params=['ReturnType', 'Visitor'],
        name='visit',
        return_type='ReturnType',
        args=['Visitor &&v'],
        is_const=is_const,
        f=f,
    ):
        const_modifier = 'const' if is_const else ''
        for value in lined(spec.values, f=f):
            render_static_assert(
                cond=f'std::is_same_v<ReturnType, std::invoke_result_t<Visitor, {value.type_} {const_modifier} &>>',
                message=f'Visitor has incorrect return type when called with parameter type {value.type_}',
                f=f,
            )
        f.write('return std::visit(v, this->raw_variant);')

def render_is_part_of(spec: VariantSpec, f: TextIO) -> None:
    with semicolon(f):
        render_template_abs(['T'], f=f)
        f.write(f'static constexpr bool IsPartOf{spec.name}_v =')
        for value in sepbyd(spec.values, ' || ', f=f):
            f.write(f'std::is_same_v<T, {value.type_}>')

def render_has_method(spec: VariantSpec, f: TextIO) -> None:
    with render_function_definition(
        template_params=['T'],
        name='has',
        return_type='bool',
        args=[],
        is_const=True,
        f=f,
    ):
        type_list = ', '.join(v.type_ for v in spec.values)
        render_static_assert(
            cond=f'IsPartOf{spec.name}_v<T>',
            message=f'{spec.name}::has() expected one of [{type_list}], received T',
            f=f,
        )
        f.write('return std::holds_alternative<T>(this->raw_variant);')

def render_get_method(spec: VariantSpec, is_const: bool, f: TextIO) -> None:
    const_modifier = 'const' if is_const else ''
    with render_function_definition(
        template_params=['T'],
        return_type=f'T {const_modifier} &',
        name='get',
        args=[],
        is_const=is_const,
        f=f,
    ):
        type_list = ', '.join(v.type_ for v in spec.values)
        render_static_assert(
            cond=f'IsPartOf{spec.name}_v<T>',
            message=f'{spec.name}::get() expected one of [{type_list}], received T',
            f=f,
        )
        f.write('return std::get<T>(this->raw_variant);')

def render_binop_decl(spec: VariantSpec, op: str, f: TextIO) -> None:
    f.write(f'bool operator{op}({spec.name} const &) const;')

def render_binop_impl(spec: VariantSpec, op: str, f: TextIO) -> None:
    with render_function_definition(
        return_type='bool',
        name=f'{spec.name}::operator{op}',
        args=[f'{spec.name} const &other'],
        is_const=True,
        f=f,
    ):
        f.write(f'return this->raw_variant {op} other.raw_variant;')

def render_typename(*, spec: VariantSpec, qualified: bool, f: TextIO) -> None:
    if qualified:
        f.write(f'::{spec.namespace}::')
    f.write(spec.name)

def get_typename(*, spec: VariantSpec, qualified: bool) -> str:
    f = io.StringIO() 
    render_typename(spec=spec, qualified=qualified, f=f)
    return f.getvalue()

def render_hash_decl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block('std', f):
        with render_struct_block(
            name=f'hash<{typename}>',
            template_params=[],
            specialization=True,
            f=f,
        ):
            render_function_declaration(
                name='operator()',
                return_type='size_t',
                args=[f'{typename} const &'],
                is_const=True,
                f=f,
            )

def render_hash_impl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block('std', f):
        with render_function_definition(
            name=f'hash<{typename}>::operator()',
            return_type='size_t',
            args=[f'{typename} const &x'],
            is_const=True,
            f=f,
        ):
            with semicolon(f):
                f.write('return ')
                render_template_app(
                    func='std::hash', 
                    params=[get_variant_type(spec=spec)],
                    f=f,
                )
                f.write('{}(x.raw_variant)')

def render_json_decl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block('nlohmann', f):
        with render_struct_block(
            name=f'adl_serializer<{typename}>',
            template_params=[],
            specialization=True,
            f=f,
        ):
            render_function_declaration(
                is_static=True,
                return_type=typename,
                name='from_json',
                args=['json const &'],
                f=f,
            )
            render_function_declaration(
                is_static=True,
                return_type='void',
                name='to_json',
                args=['json &', f'{typename} const &'],
                f=f,
            )

def render_json_impl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block('nlohmann', f):
        with render_function_definition(
            return_type=typename,
            name=f'adl_serializer<{typename}>::from_json',
            args=['json const &j'],
            f=f,
        ):
            with sline(f):
                f.write('std::string key = j.at("type").template get<std::string>()')
            for i, value in enumerate(spec.values):
                if i > 0:
                    f.write(' else ')
                f.write(f'if (key == "{value.json_key}")')
                with braces(f):
                    with sline(f):
                        f.write(f'return {typename}')
                        with braces(f):
                            f.write(f'j.at("value").template get<{value.type_}>()')
            f.write(' else ')
            with braces(f):
                with sline(f):
                    f.write('throw std::runtime_error(fmt::format("Unknown type key {}", key))')

        with render_function_definition(
            return_type='void',
            name=f'adl_serializer<{typename}>::to_json',
            args=['json &j', f'{typename} const &x'],
            f=f,
        ):
            with sline(f):
                f.write(f'j["__type"] = "{spec.name}"')
            with render_switch_block(cond='x.index()', f=f):
                for idx, value in enumerate(spec.values):
                    f.write(f'case {idx}:')
                    with braces(f):
                        with sline(f):
                            f.write(f'j["type"] = "{value.json_key}"')
                        with sline(f):
                            f.write(f'j["value"] = x.get<{value.type_}>()')
                        with sline(f):
                            f.write('break')
                f.write('default:')
                with braces(f):
                    with sline(f):
                        f.write(f'throw std::runtime_error(fmt::format("Unknown index {{}} for type {spec.name}", x.index()))')

def render_fmt_decl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block(spec.namespace, f):
        render_function_declaration(
            return_type='std::string',
            name='format_as',
            args=[f'{typename} const &'],
            f=f,
        )
        render_function_declaration(
            return_type='std::ostream &',
            name='operator<<',
            args=['std::ostream &', f'{typename} const &'],
            f=f,
        )

def render_fmt_impl(spec: VariantSpec, f: TextIO) -> None:
    typename = get_typename(spec=spec, qualified=True)

    with render_namespace_block(spec.namespace, f):
        with render_function_definition(
            return_type='std::string',
            name='format_as',
            args=[f'{typename} const &x'],
            f=f,
        ):
            with sline(f):
                f.write('std::ostringstream oss')
            with render_switch_block(cond='x.index()', f=f):
                for idx, value in enumerate(spec.values):
                    with render_case(cond=str(idx), f=f):
                        with sline(f):
                            f.write(f'oss << "<{spec.name} {value.key}=" << x.get<{value.type_}>() << ">"')
                with render_default_case(f=f):
                    with sline(f):
                        f.write(f'throw std::runtime_error(fmt::format("Unknown index {{}} for type {spec.name}", x.index()))')
            with sline(f):
                f.write("return oss.str()")

        with render_function_definition(
            return_type='std::ostream &',
            name='operator<<',
            args=['std::ostream &s', f'{typename} const &x'],
            f=f,
        ):
            with sline(f):
                f.write('return s << fmt::to_string(x)')

def render_variant_type(spec: VariantSpec, f: TextIO) -> None:
    render_template_app('std::variant', [v.type_ for v in spec.values], f=f)

def get_variant_type(spec: VariantSpec) -> str:
    f = io.StringIO()
    render_variant_type(spec=spec, f=f)
    return f.getvalue()

EQ_OPS = ('==', '!=')
ORD_OPS = ('<', '>', '<=', '>=')

def render_decls(spec: VariantSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        with render_struct_block(
            name=spec.name, 
            template_params=[],
            f=f
        ):
            f.write(f'{spec.name}() = delete;\n')
            explicit_prefix = 'explicit' if spec.explicit_constructors else ''
            for value in lined(spec.values, f=f):
                f.write(f'{explicit_prefix} {spec.name}({value.type_} const &);')

            render_is_part_of(spec=spec, f=f)

            render_visit_method(spec=spec, is_const=True, f=f)
            render_visit_method(spec=spec, is_const=False, f=f)

            render_has_method(spec=spec, f=f)

            render_get_method(spec=spec, is_const=True, f=f)
            render_get_method(spec=spec, is_const=False, f=f)

            f.write('size_t index() const { return this->raw_variant.index(); }\n')

            if Feature.EQ in spec.features:
                for op in EQ_OPS:
                    render_binop_decl(spec=spec, op=op, f=f)

            if Feature.ORD in spec.features:
                for op in ORD_OPS:
                    render_binop_decl(spec=spec, op=op, f=f)

            with semicolon(f):
                render_variant_type(spec=spec, f=f)
                f.write(' raw_variant')

    if Feature.HASH in spec.features:
        render_hash_decl(spec=spec, f=f)

    if Feature.JSON in spec.features:
        render_json_decl(spec=spec, f=f)

    if Feature.FMT in spec.features:
        render_fmt_decl(spec=spec, f=f)

def render_impls(spec: VariantSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        for value in lined(spec.values, f=f):
            f.write(f'{spec.name}::{spec.name}({value.type_} const &v)')
            f.write(' : raw_variant(v) { }')

        if Feature.EQ in spec.features:
            for op in EQ_OPS:
                render_binop_impl(spec=spec, op=op, f=f)

        if Feature.ORD in spec.features:
            for op in ORD_OPS:
                render_binop_impl(spec=spec, op=op, f=f)

    if Feature.HASH in spec.features:
        render_hash_impl(spec=spec, f=f)

    if Feature.JSON in spec.features:
        render_json_impl(spec=spec, f=f)

    if Feature.FMT in spec.features:
        render_fmt_impl(spec=spec, f=f)

def render_header(spec: VariantSpec, f: TextIO) -> None:
    render_includes(infer_header_includes(spec), f)

    f.write('\n')

    render_decls(spec, f)

def render_source(spec: VariantSpec, f: TextIO) -> None:
    render_includes(infer_source_includes(spec), f)

    f.write('\n')

    render_impls(spec, f)
