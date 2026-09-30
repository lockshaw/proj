from proj.tags import (
    tags_for_dtgen_struct,
    tags_for_dtgen_enum,
    tags_for_dtgen_variant,
    Tag,
    TagType,
)
from proj.dtgen.struct.spec import (
    StructSpec,
    FieldSpec,
    Feature as StructFeature,
)
from proj.dtgen.variant.spec import (
    VariantSpec,
    ValueSpec,
    Feature as VariantFeature,
)
from proj.dtgen.enum.spec import (
    EnumSpec,
    ValueSpec as EnumValueSpec,
    Feature as EnumFeature,
)
from proj.includes import IncludeSpec
from pathlib import PurePath

def test_tags_for_dtgen_struct() -> None:
    spec = StructSpec(
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

    path = PurePath('lib/hello.dtg.toml')

    result = tags_for_dtgen_struct(spec, path)
    correct = {
        Tag(
            tag_name='MyStruct',
            file_path=path,
            ex_cmd='/^name = "MyStruct"$/',
            tag_type=TagType.CLASS,
        ),
    }

    assert result == correct

def test_tags_for_dtgen_enum() -> None:
    spec = EnumSpec(
        namespace='FlexFlow',
        name='MyEnum',
        values=[
            EnumValueSpec(
                name='AAA',
                docstring=None,
                _json_key=None,
            ),
            EnumValueSpec(
                name='BBB',
                docstring=None,
                _json_key=None,
            ),
        ],
        features=frozenset(),
        docstring=None,
    )

    path = PurePath('lib/hello.dtg.toml')

    result = tags_for_dtgen_enum(spec, path)
    correct = {
        Tag(
            tag_name='MyEnum',
            file_path=path,
            ex_cmd='/^name = "MyEnum"$/',
            tag_type=TagType.ENUM,
        ),
    }

    assert result == correct

def test_tags_for_dtgen_variant() -> None:
    spec = VariantSpec(
        includes=[
            IncludeSpec(PurePath('string'), system=True),
        ],
        src_includes=[],
        post_includes=[],
        fwd_decls=(),
        namespace='FlexFlow',
        template_params=(),
        name='MyVariant',
        values=[
            ValueSpec(
                type_='int',
                docstring=None,
                _key='num',
                _json_key=None,
                _fmt_key=None,
                _indirect=None,
            ),
            ValueSpec(
                type_='std::string',
                docstring=None,
                _key='str',
                _json_key=None,
                _fmt_key=None,
                _indirect=None,
            ),
        ],
        features=frozenset([
            VariantFeature.EQ,
            VariantFeature.ORD,
            VariantFeature.HASH,
            VariantFeature.JSON_SERIALIZE,
            VariantFeature.JSON_DESERIALIZE,
            VariantFeature.FMT,
        ]),
        explicit_constructors=True,
        docstring=None,
    )

    path = PurePath('lib/hello.dtg.toml')

    result = tags_for_dtgen_variant(spec, path)
    correct = {
        Tag(
            tag_name='MyVariant',
            file_path=path,
            ex_cmd='/^name = "MyVariant"$/',
            tag_type=TagType.CLASS,
        ),
    }

    assert result == correct
