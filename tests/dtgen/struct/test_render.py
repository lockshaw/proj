from proj.dtgen.struct.spec import (
  StructSpec,
  FieldSpec,
  Feature,
)
import io
from proj.dtgen.struct.render import (
    render_header,
    render_fmt_decl,
    render_fmt_impl,
)
import proj.toml as toml
from ..cpp_testing_utils import (
    cpp_normalize,
)

def test_dtgen_struct_render_fmt_decl_with_json_enabled() -> None:
    spec = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyStruct',
        fields=[],
        features=frozenset([
            Feature.JSON_SERIALIZE,
            Feature.FMT,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_decl(spec, f)
    result = cpp_normalize(f.getvalue())

    correct = cpp_normalize(
        '''
        namespace Example {

        std::string format_as(MyStruct const &);
        std::ostream &operator<<(std::ostream &, MyStruct const &);

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_struct_render_fmt_impl_with_json_enabled() -> None:
    spec = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyStruct',
        fields=[
            FieldSpec(
                name='aaa',
                type_='int',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
            FieldSpec(
                name='bbb',
                type_='float',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
        ],
        features=frozenset([
            Feature.FMT,
            Feature.JSON_SERIALIZE,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_impl(spec, f)
    result = cpp_normalize(f.getvalue())

    correct = cpp_normalize(
        '''
        namespace Example {

        std::string MyStruct::debug_to_string() const {
            return fmt::to_string(*this);
        }

        void MyStruct::debug_print() const {
            std::cout << this->debug_to_string() << std::endl;
        }

       std::string format_as(MyStruct const &x) {
            ::nlohmann::json j = x;
            return j.dump();
        }

        std::ostream &operator<<(std::ostream &s, MyStruct const &x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )


def test_dtgen_struct_render_fmt_decl_without_json_enabled() -> None:
    spec = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyStruct',
        fields=[],
        features=frozenset([
            Feature.FMT,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_decl(spec, f)
    result = cpp_normalize(f.getvalue())

    correct = cpp_normalize(
        '''
        namespace Example {

        std::string format_as(MyStruct const &);
        std::ostream &operator<<(std::ostream &, MyStruct const &);

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_struct_render_fmt_impl_without_json_enabled() -> None:
    spec = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyStruct',
        fields=[
            FieldSpec(
                name='aaa',
                type_='int',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
            FieldSpec(
                name='bbb',
                type_='float',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
        ],
        features=frozenset([
            Feature.FMT,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_impl(spec, f)
    result = cpp_normalize(f.getvalue())

    correct = cpp_normalize(
        '''
        namespace Example {

        std::string MyStruct::debug_to_string() const {
            return fmt::to_string(*this);
        }

        void MyStruct::debug_print() const {
            std::cout << this->debug_to_string() << std::endl;
        }

        std::string format_as(MyStruct const &x) {
            std::ostringstream oss;
            oss << "<MyStruct";
            oss << " aaa=" << x.aaa;
            oss << " bbb=" << x.bbb;
            oss << ">";
            return oss.str();
        }

        std::ostream &operator<<(std::ostream &s, MyStruct const &x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_struct_header_with_json_and_fmt_enabled() -> None:
    spec = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyStruct',
        fields=[
            FieldSpec(
                name='aaa',
                type_='int',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
            FieldSpec(
                name='bbb',
                type_='float',
                docstring=None,
                indirect=False,
                _json_key=None,
            ),
        ],
        features=frozenset([
            Feature.JSON_SERIALIZE,
            Feature.JSON_DESERIALIZE,
            Feature.FMT,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_header(spec, f)
    result = cpp_normalize(f.getvalue())

    correct = cpp_normalize(
        '''
        #include <ostream>
        #include <nlohmann/json.hpp>
        #include <iostream>
        #include <fmt/format.h>

        namespace Example {

        struct MyStruct {
          MyStruct() = delete;
          explicit MyStruct(int const &aaa, float const &bbb);

          std::string debug_to_string() const;
          void debug_print() const;

          int aaa;
          float bbb;
        };

        } // namespace Example

        namespace nlohmann {

        template <>
        struct adl_serializer<::Example::MyStruct> {
            static ::Example::MyStruct from_json(json const &);
            static void to_json(json &, ::Example::MyStruct const &);
        };

        } // namespace nlohmann

        namespace Example {

        std::string format_as(MyStruct const &);
        std::ostream &operator<<(std::ostream &, MyStruct const &);

        } // namespace Example
        '''
    )

    assert result == correct
