import pytest

from proj.unparse_project import (
    get_repo_rel_path,
    get_fullpath,
)
from proj.paths import (
    RoleInGroup,
    Repo,
    ComponentRelPath,
    RepoRelPath,
    Component,
    FileGroup,
    File,
)
from pathlib import PurePath
from typing import (
    Any,
)
from proj.config_file import (
    ExtensionConfig,
)

# def test_get_component_rel_path() -> None:
#     p = File(FileGroup(PurePath('a/b')), Component('c'))
#

EXTENSION_CONFIG = ExtensionConfig(
    header_extension='.h',
    src_extension='.cc',
)

@pytest.mark.parametrize("input,correct", [
    # (
    #     ComponentRelPath(PurePath('a/b'), Component('c')),
    #     RepoRelPath(PurePath('lib/c/a/b'))
    # ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.DTGEN_TOML),
        RepoRelPath(PurePath('lib/c/include/c/a/b.dtg.toml'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.PUBLIC_HEADER),
        RepoRelPath(PurePath('lib/c/include/c/a/b.h'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.SOURCE),
        RepoRelPath(PurePath('lib/c/src/c/a/b.cc'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.GENERATED_HEADER),
        RepoRelPath(PurePath('lib/c/include/c/a/b.dtg.h'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.GENERATED_SOURCE),
        RepoRelPath(PurePath('lib/c/src/c/a/b.dtg.cc'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.TEST),
        RepoRelPath(PurePath('lib/c/test/src/c/a/b.cc'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.BENCHMARK_SOURCE),
        RepoRelPath(PurePath('lib/c/benchmark/src/benchmark/c/a/b.cc'))
    ),
    (
        File(FileGroup(PurePath('a/b'), Component.library('c')), RoleInGroup.BENCHMARK_HEADER),
        RepoRelPath(PurePath('lib/c/benchmark/include/benchmark/c/a/b.h'))
    ),
    (
        ComponentRelPath(PurePath('include/c/a/b.h'), Component.library('c')),
        RepoRelPath(PurePath('lib/c/include/c/a/b.h'))
    ),
])
def test_get_repo_rel_path(input: Any, correct: RepoRelPath) -> None:
    result = get_repo_rel_path(input, EXTENSION_CONFIG)

    assert result == correct

@pytest.mark.parametrize("input,extension_config,correct", [
    (
        File(FileGroup(PurePath('a/b'), Component.library('c', Repo(PurePath('d')))), RoleInGroup.SOURCE),
        EXTENSION_CONFIG,
        PurePath('d/lib/c/src/c/a/b.cc'),
    )
])
def test_get_fullpath(input: Any, extension_config: ExtensionConfig, correct: PurePath) -> None:
    result = get_fullpath(input, extension_config)

    assert result == correct

