from .cpp_testing_utils import (
    cpp_tokenize,
)

def test_cpp_tokenize() -> None:
    EXAMPLE = 'std::variant<type_a, type_b> raw_variant;};}// namespace Example'

    result = cpp_tokenize(EXAMPLE)
    correct = [
        'std',
        '::',
        'variant',
        '<',
        'type_a',
        ',',
        'type_b',
        '>',
        'raw_variant',
        ';',
        '}',
        ';',
        '}',
        '//',
        'namespace',
        'Example',
    ]

    assert result == correct
