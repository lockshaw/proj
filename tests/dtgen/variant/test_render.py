import pytest
from proj.dtgen.variant.render import (
  render_header,
  render_source,
  render_fmt_decl,
  render_fmt_impl,
)
from proj.dtgen.variant.spec import (
  VariantSpec,
  ValueSpec,
  Feature,
)
from proj.includes import (
    IncludeSpec,
)
import io
from pathlib import PurePath
from ..cpp_testing_utils import cpp_tokenize

def test_dtgen_variant_render_fmt_decl() -> None:
    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset([
            Feature.FMT,
        ]),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_decl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string format_as(::Example::MyVariant const &);
        std::ostream &operator<<(std::ostream &, ::Example::MyVariant const &);

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_variant_render_fmt_impl() -> None:
    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset([
            Feature.FMT,
        ]),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_impl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string MyVariant::debug_to_string() const {
            return fmt::to_string(*this);
        }

        void MyVariant::debug_print() const {
            std::cout << this->debug_to_string() << std::endl;
        }

        std::string format_as(::Example::MyVariant const &x) {
            std::ostringstream oss;
            switch (x.index()) {
                case 0: {
                    oss << "<MyVariant a=" << x.template get<type_a>() << ">";
                    break;
                }
                case 1: {
                    oss << "<MyVariant b=" << x.template get<type_b>() << ">";
                    break;
                }
                default: {
                    throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", x.index()));
                    break;
                }
            }
            return oss.str();
        }

        std::ostream &operator<<(std::ostream &s, ::Example::MyVariant const &x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_variant_render_fmt_decl_with_json_enabled() -> None:
    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset([
            Feature.FMT,
            Feature.JSON_SERIALIZE,
        ]),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_decl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string format_as(::Example::MyVariant const &);
        std::ostream &operator<<(std::ostream &, ::Example::MyVariant const &);

        } // namespace Example
        '''
    )

    assert result == correct

def test_dtgen_variant_render_fmt_impl_with_json_enabled() -> None:
    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset([
            Feature.FMT,
            Feature.JSON_SERIALIZE,
        ]),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_fmt_impl(spec, f)
    result = cpp_tokenize(f.getvalue())

    correct = cpp_tokenize(
        '''
        namespace Example {

        std::string MyVariant::debug_to_string() const {
            return fmt::to_string(*this);
        }

        void MyVariant::debug_print() const {
            std::cout << this->debug_to_string() << std::endl;
        }

        std::string format_as(::Example::MyVariant const &x) {
            ::nlohmann::json j = x;
            return j.dump();
        }

        std::ostream &operator<<(std::ostream &s, ::Example::MyVariant const &x) {
            return s << fmt::to_string(x);
        }

        } // namespace Example
        '''
    )

    assert result == correct


def test_dtgen_variant_render_header() -> None:
    CORRECT_HDR = '''
    #include <cstddef>
    #include <fmt/format.h>
    #include <libassert/assert.hpp>
    #include <optional>
    #include <stdexcept>
    #include <type_traits>
    #include <variant>

    namespace Example{

    struct MyVariant{
      MyVariant() = delete;
      explicit MyVariant(type_a const &);
      explicit MyVariant(type_b const &);

      template <typename T>
      static constexpr bool IsPartOfMyVariant_v =std::is_same_v<T, type_a> || std::is_same_v<T, type_b>;

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) const {
        switch (this->index()) {
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) {
        switch (this->index()){
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename T>
      bool has() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::has() expected one of [type_a, type_b], received T");
        return std::holds_alternative<T>(this->raw_variant);
      }

      template <typename T>
      T const & get() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");
        bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      template <typename T>
      T &get(){
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      size_t index() const {
        return this->raw_variant.index();
      }

      type_a const & require_a() const;
      type_a & require_a();
      type_b const & require_b() const;
      type_b & require_b();
      std::optional<type_a> try_require_a() const;
      std::optional<type_b> try_require_b() const;
      bool is_a() const;
      bool is_b() const;

      std::variant<type_a, type_b> raw_variant;
    };

    } // namespace Example
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_header(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_HDR)

def test_dtgen_variant_render_source() -> None:
    CORRECT_SRC = '''
    namespace Example{

    MyVariant::MyVariant(type_a const &v) : raw_variant(v) { }
    MyVariant::MyVariant(type_b const &v) : raw_variant(v) { }

    type_a const &MyVariant::require_a() const {
      bool holds_expected = std::holds_alternative<type_a>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_a");
      return std::get<type_a>(this->raw_variant);
    }

    type_a &MyVariant::require_a() {
      bool holds_expected = std::holds_alternative<type_a>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_a");
      return std::get<type_a>(this->raw_variant);
    }

    type_b const &MyVariant::require_b() const {
      bool holds_expected = std::holds_alternative<type_b>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_b");
      return std::get<type_b>(this->raw_variant);
    }

    type_b &MyVariant::require_b() {
      bool holds_expected = std::holds_alternative<type_b>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_b");
      return std::get<type_b>(this->raw_variant);
    }

    std::optional<type_a> MyVariant::try_require_a() const {
      if (this->is_a()) {
        return this->require_a();
      } else {
        return std::nullopt;
      }
    }

    std::optional<type_b> MyVariant::try_require_b() const {
      if (this->is_b()) {
        return this->require_b();
      } else {
        return std::nullopt;
      }
    }

    bool MyVariant::is_a() const {
      return std::holds_alternative<type_a>(this->raw_variant);
    }

    bool MyVariant::is_b() const {
      return std::holds_alternative<type_b>(this->raw_variant);
    }

    } // namespace Example
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_source(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_SRC)

def test_render_indirect_variant_header() -> None:
    CORRECT_HDR = '''
    #include <cstddef>
    #include <fmt/format.h>
    #include <libassert/assert.hpp>
    #include <memory>
    #include <optional>
    #include <stdexcept>
    #include <type_traits>
    #include <variant>

    namespace Example {

    struct MyVariant{
      MyVariant() = delete;
      explicit MyVariant(type_a const &);
      explicit MyVariant(type_b const &);

      template <typename T>
      static constexpr bool IsPartOfMyVariant_v = std::is_same_v<T, type_a> || std::is_same_v<T, type_b>;

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) const {
        switch (this->index()) {
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v){
        switch (this->index()){
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename T>
      bool has() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::has() expected one of [type_a, type_b], received T");
        return std::holds_alternative<T>(this->raw_variant);
      }

      template <typename T>
      T const &get() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");
        bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      template <typename T>
      T &get() {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");
        bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      size_t index() const {
        return this->raw_variant.index();
      }

      type_a const & require_a() const;
      type_a & require_a();
      type_b const & require_b() const;
      type_b & require_b();
      std::optional<type_a> try_require_a() const;
      std::optional<type_b> try_require_b() const;
      bool is_a() const;
      bool is_b() const;

      std::variant<type_a, std::shared_ptr<type_b>> raw_variant;
    };

    template <>
    bool MyVariant::has<type_b>() const;

    template <>
    type_b const &MyVariant::get<type_b>() const;

    template <>
    type_b &MyVariant::get<type_b>();

    } // namespace Example
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=[],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=True,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_header(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_HDR)

def test_render_indirect_variant_source() -> None:
    CORRECT_SRC = '''
    namespace Example {

    MyVariant::MyVariant(type_a const &v) : raw_variant(v) { }

    MyVariant::MyVariant(type_b const &v) : raw_variant(std::make_shared<type_b>(v)) { }

    type_a const &MyVariant::require_a() const {
      bool holds_expected = std::holds_alternative<type_a>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_a");
      return std::get<type_a>(this->raw_variant);
    }

    type_a &MyVariant::require_a() {
      bool holds_expected = std::holds_alternative<type_a>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_a");
      return std::get<type_a>(this->raw_variant);
    }

    type_b const &MyVariant::require_b() const {
      bool holds_expected = std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_b");
      return *std::get<std::shared_ptr<type_b>>(this->raw_variant);
    }

    type_b &MyVariant::require_b() {
      bool holds_expected = std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
      ASSERT(holds_expected, "Expected type_b");
      return *std::get<std::shared_ptr<type_b>>(this->raw_variant);
    }

    std::optional<type_a> MyVariant::try_require_a() const {
      if (this->is_a()) {
        return this->require_a();
      } else {
        return std::nullopt;
      }
    }

    std::optional<type_b> MyVariant::try_require_b() const {
      if (this->is_b()) {
        return this->require_b();
      } else {
        return std::nullopt;
      }
    }

    bool MyVariant::is_a() const {
      return std::holds_alternative<type_a>(this->raw_variant);
    }

    bool MyVariant::is_b() const {
      return std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
    }

    template <>
    bool MyVariant::has<type_b>() const {
      return std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
    }

    template <>
    type_b const &MyVariant::get<type_b>() const {
      bool holds_expected = std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
      ASSERT(holds_expected);
      return *std::get<std::shared_ptr<type_b>>(this->raw_variant);
    }

    template <>
    type_b &MyVariant::get<type_b>() {
      bool holds_expected = std::holds_alternative<std::shared_ptr<type_b>>(this->raw_variant);
      ASSERT(holds_expected);
      return *std::get<std::shared_ptr<type_b>>(this->raw_variant);
    }

    } // namespace Example
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=True,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_source(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_SRC)

def test_render_fwd_decl_variant_header() -> None:
    CORRECT_HDR = '''
    #include <cstddef>
    #include <fmt/format.h>
    #include <libassert/assert.hpp>
    #include <optional>
    #include <stdexcept>
    #include <type_traits>
    #include <variant>

    namespace Example{

    struct MyFwdDecl;

    struct MyVariant{
      MyVariant() = delete;
      explicit MyVariant(type_a const &);
      explicit MyVariant(type_b const &);

      template <typename T>
      static constexpr bool IsPartOfMyVariant_v =std::is_same_v<T, type_a> || std::is_same_v<T, type_b>;

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) const {
        switch (this->index()) {
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) {
        switch (this->index()){
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename T>
      bool has() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::has() expected one of [type_a, type_b], received T");
        return std::holds_alternative<T>(this->raw_variant);
      }

      template <typename T>
      T const & get() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");
        bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      template <typename T>
      T &get(){
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      size_t index() const {
        return this->raw_variant.index();
      }

      type_a const & require_a() const;
      type_a & require_a();
      type_b const & require_b() const;
      type_b & require_b();
      std::optional<type_a> try_require_a() const;
      std::optional<type_b> try_require_b() const;
      bool is_a() const;
      bool is_b() const;

      std::variant<type_a, type_b> raw_variant;
    };

    } // namespace Example
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        namespace='Example',
        fwd_decls=["struct MyFwdDecl"],
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_header(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_HDR)

def test_render_post_include_variant_header() -> None:
    CORRECT_HDR = '''
    #include <cstddef>
    #include <fmt/format.h>
    #include <libassert/assert.hpp>
    #include <optional>
    #include <stdexcept>
    #include <type_traits>
    #include <variant>

    namespace Example{

    struct MyVariant{
      MyVariant() = delete;
      explicit MyVariant(type_a const &);
      explicit MyVariant(type_b const &);

      template <typename T>
      static constexpr bool IsPartOfMyVariant_v =std::is_same_v<T, type_a> || std::is_same_v<T, type_b>;

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) const {
        switch (this->index()) {
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename ReturnType, typename Visitor>
      ReturnType visit(Visitor &&v) {
        switch (this->index()){
          case 0: {
            ReturnType result = v(this->get<type_a>());
            return result;
          }
          case 1: {
            ReturnType result = v(this->get<type_b>());
            return result;
          }
          default: {
            throw std::runtime_error(fmt::format("Unknown index {} for type MyVariant", this->index()));
          }
        }
      }

      template <typename T>
      bool has() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::has() expected one of [type_a, type_b], received T");
        return std::holds_alternative<T>(this->raw_variant);
      }

      template <typename T>
      T const & get() const {
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");
        bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      template <typename T>
      T &get(){
        static_assert(IsPartOfMyVariant_v<T>, "MyVariant::get() expected one of [type_a, type_b], received T");bool holds_expected = std::holds_alternative<T>(this->raw_variant);
        ASSERT(holds_expected);
        return std::get<T>(this->raw_variant);
      }

      size_t index() const {
        return this->raw_variant.index();
      }

      type_a const & require_a() const;
      type_a & require_a();
      type_b const & require_b() const;
      type_b & require_b();
      std::optional<type_a> try_require_a() const;
      std::optional<type_b> try_require_b() const;
      bool is_a() const;
      bool is_b() const;

      std::variant<type_a, type_b> raw_variant;
    };

    } // namespace Example

    #include "hello/world.h"
    '''

    spec = VariantSpec(
        includes=[],
        src_includes=[],
        post_includes=[
            IncludeSpec(path=PurePath("hello/world.h"), system=False),
        ],
        fwd_decls=[],
        namespace='Example',
        template_params=[],
        name='MyVariant',
        values=[
            ValueSpec(
                type_='type_a',
                docstring=None,
                _key='a',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
            ValueSpec(
                type_='type_b',
                docstring=None,
                _key='b',
                _json_key=None,
                _fmt_key=None,
                _indirect=False,
            ),
        ],
        features=frozenset(),
        explicit_constructors=True,
        docstring=None,
    )

    f = io.StringIO()
    render_header(spec, f)
    result = cpp_tokenize(f.getvalue())

    assert result == cpp_tokenize(CORRECT_HDR)
