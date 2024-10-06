#ifndef _JSON_OPTIONAL_H
#define _JSON_OPTIONAL_H

#include <nlohmann/json.hpp>
#include <optional>

namespace nlohmann {

template <typename T>
struct adl_serializer<std::optional<T>> {
  static void to_json(json &j, std::optional<T> const &t) {
    if (t.has_value()) {
      j = t.value();
    } else {
      j = nullptr;
    }
  }

  static void from_json(json const &j, std::optional<T> &t) {
    if (j == nullptr) {
      t = std::nullopt;
    } else {
      t = j.get<T>();
    }
  }
};

} // namespace nlohmann

#endif
