import pytest
from proj.dtgen.struct.spec import (
  StructSpec,
  FieldSpec,
  parse_struct_spec,
  Feature,
)
import proj.toml as toml

def test_parse_struct_spec_basic() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyStruct"
        features = []

        [[fields]]
        name = "aaa"
        type = "int"

        [[fields]]
        name = "bbb"
        type = "float"
        '''
    )

    result = parse_struct_spec(INPUT)
    correct = StructSpec(
        includes=[],
        src_includes=[],
        post_includes=[],
        fwd_decls=(),
        namespace='FlexFlow',
        template_params=(),
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
        features=frozenset(),
        docstring=None,
    )

    assert result == correct

def test_parse_struct_spec_raises_on_invalid_key() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyStruct"
        features = []

        abc = []
        def = []

        [[fields]]
        name = "aaa"
        type = "int"

        [[fields]]
        name = "bbb"
        type = "float"
        '''
    )

    with pytest.raises(ValueError) as excinfo:
        parse_struct_spec(INPUT)

    assert "abc" in str(excinfo.value)
    assert "def" in str(excinfo.value)

def test_parse_struct_spec_raises_on_field_key() -> None:
    INPUT = toml.loads(
        '''
        namespace = "FlexFlow"
        name = "MyStruct"
        features = []

        [[fields]]
        name = "aaa"
        type = "int"
        abc = []
        def = []

        [[fields]]
        name = "bbb"
        type = "float"
        '''
    )

    with pytest.raises(ValueError) as excinfo:
        parse_struct_spec(INPUT)

    assert "abc" in str(excinfo.value)
    assert "def" in str(excinfo.value)

