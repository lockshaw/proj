#ifndef _FMT_OPTIONAL_H
#define _FMT_OPTIONAL_H

#include <fmt/format.h>
#include <optional>

namespace fmt {

template <typename T, typename Char>
struct formatter<
    ::std::optional<T>,
    Char,
    std::enable_if_t<!detail::has_format_as<::std::optional<T>>::value>>
    : formatter<::std::string> {
  template <typename FormatContext>
  auto format(::std::optional<T> const &m, FormatContext &ctx)
      -> decltype(ctx.out()) {
    std::string result;
    if (m.has_value()) {
      result = fmt::to_string(m.value());
    } else {
      result = "nullopt";
    }

    return formatter<std::string>::format(result, ctx);
  }
};

} // namespace fmt

namespace FlexFlow {

template <typename T>
std::ostream &operator<<(std::ostream &s, std::optional<T> const &t) {
  return s << fmt::to_string(t);
}

} // namespace FlexFlow

#endif
