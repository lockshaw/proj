import pytest

from typing import (
    Union,
    Optional,
)
from proj.config_file import ExtensionConfig
from proj.paths import (
    Repo,
    RepoRelPath,
    File,
    FileGroup,
    RoleInGroup,
    ComponentRelPath,
    Component,
)
from pathlib import PurePath
from proj.parse_project import (
    parse_repo_path,
    parse_file_path,
)

EXTENSION_CONFIG = ExtensionConfig(
    header_extension='.h',
    src_extension='.cc',
)

@pytest.mark.parametrize("input,correct", [
    (
        "my_repo/lib/example/src/example/something",
        "lib/example/src/example/something"
    )
])
def get_parse_repo_path_with_repo_arg(input_str: str, correct_str: str) -> None:
    repo = Repo(PurePath("my_repo"))

    result = parse_repo_path(PurePath(input_str), repo)
    correct = RepoRelPath(PurePath(correct_str), repo)

    assert result == correct

@pytest.mark.parametrize("input,extension_config,correct", [
    (
        RepoRelPath(PurePath('lib/example/include/example/thing.dtg.toml')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.DTGEN_TOML,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/include/example/thing.dtg.h')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.GENERATED_HEADER,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/src/example/thing.dtg.cc')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.GENERATED_SOURCE,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/src/example/thing.cc')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.SOURCE,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/test/src/example/thing.cc')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.TEST,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/benchmark/src/benchmark/example/thing.cc')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.BENCHMARK_SOURCE,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/benchmark/include/benchmark/example/thing.h')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('thing'), Component.library('example')),
            RoleInGroup.BENCHMARK_HEADER,
        ),
    ),
    (
        RepoRelPath(PurePath('lib/example/include/example/')),
        EXTENSION_CONFIG,
        None,
    ),
    (
        RepoRelPath(PurePath('lib/example/src/example/')),
        EXTENSION_CONFIG,
        None,
    ),
    (
        RepoRelPath(PurePath('lib/example/src/')),
        EXTENSION_CONFIG,
        None,
    ),
    (
        RepoRelPath(PurePath('lib/example/src/example/something')),
        EXTENSION_CONFIG,
        None,
    ),
    (
        RepoRelPath(PurePath('bin/mybin/src/mybin/something.cc')),
        EXTENSION_CONFIG,
        File(
            FileGroup(PurePath('something'), Component.executable('mybin')),
            RoleInGroup.SOURCE,
        ),
    ),
])
def test_parse_file_path(
    input: Union[ComponentRelPath, RepoRelPath],
    extension_config: ExtensionConfig,
    correct: Optional[File],
) -> None:
    result = parse_file_path(input, extension_config)

    assert result == correct
