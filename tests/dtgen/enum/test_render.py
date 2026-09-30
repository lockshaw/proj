from proj.dtgen.enum.render import (
  render_fmt_decl,
  render_fmt_impl,
)
from proj.dtgen.enum.spec import (
  EnumSpec,
  ValueSpec,
  Feature,
)
from ..cpp_testing_utils import cpp_tokenize
import io

def test_dtgen_enum_render_fmt_decl() -> None:
    spec = EnumSpec(
        namespace='Example',
        name='MyEnum',
        values=[
            ValueSpec(
                name='aaa',
                docstring=None,
                _json_key=None,
            ),
            ValueSpec(
                name='bbb',
                docstring=None,
                _json_key=None,
            ),
        ],
        features=frozenset([
            Feature.FMT,
        ]),
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_decl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        std::string format_as(MyEnum);
        std::ostream &operator<<(std::ostream &, MyEnum);
        '''
    )

    assert result == correct

def test_dtgen_enum_render_fmt_impl() -> None:
    spec = EnumSpec(
        namespace='Example',
        name='MyEnum',
        values=[
            ValueSpec(
                name='AAA',
                docstring=None,
                _json_key=None,
            ),
            ValueSpec(
                name='BBB',
                docstring=None,
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
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string format_as(MyEnum x) {
            switch (x) {
                case MyEnum::AAA:
                    return "AAA";
                case MyEnum::BBB:
                    return "BBB";
                default:
                    std::ostringstream oss;
                    oss << "Unknown MyEnum value " << static_cast<int>(x);
                    throw std::runtime_error(oss.str());
            }
        }

        std::ostream &operator<<(std::ostream &s, MyEnum x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_enum_render_fmt_decl_with_json_enabled() -> None:
    spec = EnumSpec(
        namespace='Example',
        name='MyEnum',
        values=[
            ValueSpec(
                name='aaa',
                docstring=None,
                _json_key=None,
            ),
            ValueSpec(
                name='bbb',
                docstring=None,
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
    render_fmt_decl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        std::string format_as(MyEnum);
        std::ostream &operator<<(std::ostream &, MyEnum);
        '''
    )

    assert result == correct

def test_dtgen_enum_render_fmt_impl_with_json_enabled() -> None:
    spec = EnumSpec(
        namespace='Example',
        name='MyEnum',
        values=[
            ValueSpec(
                name='AAA',
                docstring=None,
                _json_key=None,
            ),
            ValueSpec(
                name='BBB',
                docstring=None,
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
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string format_as(MyEnum x) {
            ::nlohmann::json j = x;
            return j.dump();
        }

        std::ostream &operator<<(std::ostream &s, MyEnum x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )

    assert result == correct
