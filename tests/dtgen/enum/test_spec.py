import pytest
from proj.dtgen.enum.spec import (
  EnumSpec,
  ValueSpec,
  parse_enum_spec,
)
import proj.toml as toml

def test_parse_enum_spec_basic() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyEnum"
        features = []

        [[values]]
        name = "AAA"

        [[values]]
        name = "BBB"
        '''
    )

    result = parse_enum_spec(INPUT)
    correct = EnumSpec(
        namespace='FlexFlow',
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
        features=frozenset(),
        docstring=None,
    )

    assert result == correct

def test_parse_enum_spec_raises_on_invalid_key() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyEnum"
        features = []

        abc = []
        def = []

        [[values]]
        name = "AAA"

        [[values]]
        name = "BBB"
        '''
    )

    with pytest.raises(ValueError) as excinfo:
        parse_enum_spec(INPUT)

    assert "abc" in str(excinfo.value)
    assert "def" in str(excinfo.value)

def test_parse_enum_spec_raises_on_value_key() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyEnum"
        features = []

        abc = []

        [[values]]
        key = "AAA"

        [[values]]
        name = "BBB"
        '''
    )

    with pytest.raises(ValueError) as excinfo:
        parse_enum_spec(INPUT)

    assert "key" in str(excinfo.value)
