from proj.checks import (
    is_valid_test_name,
)

def test_is_valid_test_name() -> None:
    assert is_valid_test_name(r'inplace_filter(T, F)<std::unordered_map<int, std::__cxx11::basic_string<char> >>')
    assert not is_valid_test_name(r'get_*')
    assert not is_valid_test_name(r'get_\*')
    assert not is_valid_test_name(r'get_?')
    assert not is_valid_test_name(r'get_\?')
    assert is_valid_test_name(r'add(..., ...)')
    assert is_valid_test_name(r'1 != 2')
    assert is_valid_test_name(r'1 / 2')
    assert is_valid_test_name(r'1 + 2')
    assert is_valid_test_name(r'1 % 2')
    assert is_valid_test_name(r'operator[]')
    assert is_valid_test_name(r'something{int}')
