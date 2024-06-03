from .spec import (
    EnumSpec,
    Feature,
)
from proj.dtgen.render_utils import (
    IncludeSpec,
    render_includes,
    semicolon,
    braces,
    render_namespace_block,
    commad,
    parens,
)
from contextlib import contextmanager
from typing import (
    Iterator,
    Sequence,
    TextIO,
)

def header_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature == Feature.HASH:
        return [IncludeSpec(path='functional', system=True)]
    elif feature == Feature.JSON:
        return [IncludeSpec(path='nlohmann/json.hpp', system=False)]
    elif feature == Feature.RAPIDCHECK:
        return [IncludeSpec(path='rapidcheck.h', system=False)]
    elif feature == Feature.FMT:
        return [
            IncludeSpec(path='string', system=True),
            IncludeSpec(path='ostream', system=True),
            IncludeSpec(path='fmt/format.h', system=False),
        ]
    else:
        return []

def source_includes_for_feature(feature: Feature) -> Sequence[IncludeSpec]:
    if feature in [Feature.FMT, Feature.JSON]:
        return [
            IncludeSpec(path='stdexcept', system=True), 
            IncludeSpec(path='sstream', system=True),
        ]
    else:
        return []

def infer_header_includes(spec: EnumSpec) -> Sequence[IncludeSpec]:
    result = []
    for feature in spec.features:
        for include in header_includes_for_feature(feature):
            if include not in result:
                result.append(include)
    return result

def infer_source_includes(spec: EnumSpec) -> Sequence[IncludeSpec]:
    result = []
    for feature in spec.features:
        for include in source_includes_for_feature(feature):
            if include not in result:
                result.append(include)
    return result


@contextmanager
def render_enum_block(name: str, f: TextIO) -> Iterator[None]:
    f.write(f'enum class {name}')
    with semicolon(f):
        with braces(f):
            yield

def render_fmt_decl(name: str, f: TextIO) -> None:
    f.write(f'std::string format_as({name});\n')
    f.write(f'std::ostream &operator<<(std::ostream &, {name});\n')

def render_fmt_impl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        f.write(f'std::string format_as({spec.name} x)')
        with braces(f):
            f.write('switch (x)')
            with braces(f):
                for value in spec.values:
                    f.write(f'case {spec.name}::{value.name}:\n')
                    f.write(f'return "{value.name}";\n')
                f.write('default:\n')
                f.write('std::ostringstream oss;\n')
                f.write(f'oss << "Unknown {spec.name} value " << static_cast<int>(x);\n')
                f.write('throw std::runtime_error(oss.str());\n')
        f.write(f'std::ostream &operator<<(std::ostream &s, {spec.name} x)')
        with braces(f):
            f.write('return s << fmt::to_string(x);')

def render_json_decl(name: str, f: TextIO) -> None:
    f.write(f'void to_json(::nlohmann::json &, {name});\n')
    f.write(f'void from_json(::nlohmann::json const &, {name} &);\n')

def render_json_impl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block(spec.namespace, f):
        f.write(f'void to_json(::nlohmann::json &j, {spec.name} x)')
        with braces(f):
            f.write('switch (x)')
            with braces(f):
                for value in spec.values:
                    f.write(f'case {spec.name}::{value.name}:\n')
                    f.write(f'j = "{value.json_key}";\n')
                    f.write('break;\n')
                f.write('default:\n')
                f.write('std::ostringstream oss;\n')
                f.write(f'oss << "Unknown {spec.name} value " << static_cast<int>(x);\n')
                f.write('throw std::runtime_error(oss.str());\n')
        f.write(f'void from_json(::nlohmann::json const &j, {spec.name} &x)')
        with braces(f):
            f.write('std::string as_str = j.get<std::string>();\n')
            for value in spec.values:
                f.write(f'if (as_str == "{value.json_key}")')
                with braces(f):
                    f.write(f'x = {spec.name}::{value.name};\n')
                f.write('else ')
            with braces(f):
                f.write('std::ostringstream oss;\n')
                f.write(f'oss << "Unknown {spec.name} value " << as_str;\n')
                f.write('throw std::runtime_error(oss.str());\n')

def render_rapidcheck_decl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block('rc', f):
        with semicolon(f):
            f.write('template <>\n')
            f.write(f'struct Arbitrary<{spec.namespace}::{spec.name}> ')
            with braces(f):
                f.write(f'static Gen<{spec.namespace}::{spec.name}> arbitrary();\n')

def render_rapidcheck_impl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block('rc', f):
        f.write(f'Gen<{spec.namespace}::{spec.name}> Arbitrary<{spec.namespace}::{spec.name}>::arbitrary()')
        with braces(f):
            with semicolon(f):
                f.write(f'return gen::element<{spec.namespace}::{spec.name}>')
                with parens(f):
                    for value in commad(spec.values, f):
                        f.write(f'{spec.namespace}::{spec.name}::{value.name}')

def render_hash_decl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block('std', f):
        with semicolon(f):
            f.write('template <>\n')
            f.write(f'struct hash<{spec.namespace}::{spec.name}> ')
            with braces(f):
                f.write(f'size_t operator()({spec.namespace}::{spec.name}) const;\n')


def render_hash_impl(spec: EnumSpec, f: TextIO) -> None:
    with render_namespace_block('std', f):
        f.write(f'size_t hash<{spec.namespace}::{spec.name}>::operator()({spec.namespace}::{spec.name} x) const')
        with braces(f):
            f.write('return std::hash<int>{}(static_cast<int>(x));\n')

def render_header(spec: EnumSpec, f: TextIO) -> None:
    render_includes(infer_header_includes(spec), f)
    f.write('\n')

    with render_namespace_block(spec.namespace, f):
        with render_enum_block(spec.name, f):
            for value in commad(spec.values, f):
                f.write(value.name)
        if Feature.FMT in spec.features:
            render_fmt_decl(spec.name, f)
        if Feature.JSON in spec.features:
            render_json_decl(spec.name, f)
    if Feature.HASH in spec.features:
        render_hash_decl(spec, f)
    if Feature.RAPIDCHECK in spec.features:
        render_rapidcheck_decl(spec, f)

def render_source(spec: EnumSpec, f: TextIO) -> None:
    render_includes(infer_source_includes(spec), f)
    f.write('\n')
    
    if Feature.HASH in spec.features:
        render_hash_impl(spec, f)
    if Feature.FMT in spec.features:
        render_fmt_impl(spec, f)
    if Feature.JSON in spec.features:
        render_json_impl(spec, f)
    if Feature.RAPIDCHECK in spec.features:
        render_rapidcheck_impl(spec, f)
