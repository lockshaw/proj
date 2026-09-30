from proj.paths import (
    Repo,
    FileGroup,
    Component,
)
from proj.config_file import ExtensionConfig
from pathlib import PurePath
from proj.file_group_info import (
    get_file_group_info,
    FileGroupInfo,
)

EXTENSION_CONFIG = ExtensionConfig(
    '.h',
    '.cc',
)

def test_get_file_group_info() -> None:
    file_group = FileGroup(
        PurePath('a/b'),
        Component.library(
            'c',
            Repo(PurePath('d')),
        ),
    )

    ifndef_base = '_BASE__'
    extension_config = ExtensionConfig(
        header_extension='.hhh',
        src_extension='.cpp',
    )

    result = get_file_group_info(file_group, ifndef_base, extension_config)

    correct = FileGroupInfo(
        public_header=PurePath('lib/c/include/c/a/b.hhh'),
        generated_header=PurePath('lib/c/include/c/a/b.dtg.hhh'),
        generated_source=PurePath('lib/c/src/c/a/b.dtg.cpp'),
        source=PurePath('lib/c/src/c/a/b.cpp'),
        test_source=PurePath('lib/c/test/src/c/a/b.cpp'),
        benchmark_header=PurePath('lib/c/benchmark/include/benchmark/c/a/b.hhh'),
        benchmark_source=PurePath('lib/c/benchmark/src/benchmark/c/a/b.cpp'),
        toml_path=PurePath('lib/c/include/c/a/b.dtg.toml'),
        ifndef='__BASE___LIB_C_INCLUDE_C_A_B_HHH',
        generated_include=PurePath('c/a/b.dtg.hhh'),
        include=PurePath('c/a/b.hhh'),
    )

    assert result == correct
