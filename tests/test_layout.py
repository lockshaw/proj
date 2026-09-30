from proj.layout import (
    scan_component_for_files,
    KnownFile,
    UnrecognizedFile,
    run_layout_check,
    IncompleteGroup,
    scan_repo_for_components,
    detect_missing_roles,
    detect_incomplete_groups,
)
from proj.paths import (
    Component,
    FileGroup,
    RoleInGroup,
    ComponentRelPath,
    RepoRelPath,
)
from proj.trees import (
    EmulatedPathTree,
    PathType,
)
from pathlib import (
    PurePath,
)
from proj.config_file import ExtensionConfig
from typing import Set

def test_scan_component_for_files() -> None:
    component = Component.library('example')

    struct_toml = 'include/example/example_struct.dtg.toml'
    header = 'include/example/example_struct.h'
    src_f = 'src/example/example_struct.cc'
    test_src = 'test/src/example/example_struct.cc'
    benchmark_src = 'benchmark/src/benchmark/example/example_struct.cc'
    benchmark_hdr = 'benchmark/include/benchmark/example/example_struct.h'

    extension_config = ExtensionConfig(
        '.h', '.cc',
    )

    component_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'CMakeLists.txt',
            'include/example/example_variant.dtg.toml',
            struct_toml,
            header,
            src_f,
            test_src,
            benchmark_src,
            benchmark_hdr,
            'src/bad.cc'
        ]
    })

    result = set(scan_component_for_files(component, component_path_tree, extension_config))

    group = FileGroup(PurePath('example_struct'), component)

    correct = {
        KnownFile(ComponentRelPath(PurePath('CMakeLists.txt'), component)),
        group.dtgen_toml,
        group.public_header,
        group.source,
        group.test,
        group.benchmark_source,
        group.benchmark_header,
        FileGroup(PurePath('example_variant'), component).dtgen_toml,
        UnrecognizedFile(ComponentRelPath(PurePath('src/bad.cc'), component))
    }

    assert result == correct

def test_scan_repo_for_components() -> None:
    extension_config = ExtensionConfig(
        '.h', '.cc',
    )

    repo_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'lib/example/CMakeLists.txt',
            'lib/example/include/example/example_variant.dtg.toml',
            'lib/example/include/example/example_struct.dtg.toml',
            'lib/example/src/example/example_struct.cc',
            'lib/example/test/src/example/example_struct.cc',
            'lib/example/benchmark/include/benchmark/example/example_struct.h',
            'lib/example/benchmark/src/benchmark/example/example_struct.cc',
            'lib/example/src/bad.cc',
        ]
    })

    lib_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'CMakeLists.txt',
            'include/example/example_variant.dtg.toml',
            'include/example/example_struct.dtg.toml',
            'src/example/example_struct.cc',
            'test/src/example/example_struct.cc',
            'benchmark/include/benchmark/example/example_struct.h',
            'benchmark/src/benchmark/example/example_struct.cc',
            'src/bad.cc',
        ]
    })

    result = {
        k: v for k, v in scan_repo_for_components(repo_path_tree, extension_config)
    }

    correct = {
        Component.library('example'): lib_path_tree,
    }

    assert set(result.keys()) == set(correct.keys())
    assert result[Component.library('example')] == lib_path_tree

def test_detect_incomplete_groups_detects_missing_header() -> None:
    file_group = FileGroup(PurePath('a'), Component.library('d'))

    present = [
            RoleInGroup.SOURCE,
            RoleInGroup.DTGEN_TOML,
            RoleInGroup.TEST,
            RoleInGroup.BENCHMARK_SOURCE,
            RoleInGroup.BENCHMARK_HEADER,
        ]

    input = {
        file_group: present,
    }

    result = set(detect_incomplete_groups(input))

    correct = {
        IncompleteGroup(
            file_group,
            present=frozenset(present),
            missing=frozenset([RoleInGroup.PUBLIC_HEADER]),
        ),
    }

    assert result == correct

def test_detect_incomplete_groups_ignores_main_file() -> None:
    file_group = FileGroup(PurePath('main'), Component.library('d'))

    input = {
        file_group: [
            RoleInGroup.SOURCE,
        ]
    }

    result = set(detect_incomplete_groups(input))

    correct: Set[IncompleteGroup] = set()

    assert result == correct


def test_detect_missing_roles() -> None:
    result = detect_missing_roles({
        RoleInGroup.SOURCE,
        RoleInGroup.DTGEN_TOML,
        RoleInGroup.TEST,
        RoleInGroup.BENCHMARK_SOURCE,
    })

    correct = {RoleInGroup.PUBLIC_HEADER, RoleInGroup.BENCHMARK_HEADER}

    assert correct == result

def test_run_layout_check() -> None:
    component = Component.library('example')

    struct_toml = 'lib/example/include/example/example_struct.dtg.toml'
    src_f = 'lib/example/src/example/example_struct.cc'
    test_src = 'lib/example/test/src/example/example_struct.cc'
    benchmark_src = 'lib/example/benchmark/src/benchmark/example/example_struct.cc'

    extension_config = ExtensionConfig(
        '.h', '.cc',
    )

    component_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'lib/example/CMakeLists.txt',
            'lib/example/include/example/example_variant.dtg.toml',
            struct_toml,
            src_f,
            test_src,
            benchmark_src,
            'lib/example/src/bad.cc',
            'lib/example/src/extra/extra_bad.cc',
            'lib/example/src/extra_bad.cc',
        ]
    })

    result = set(run_layout_check(component_path_tree, extension_config, ignore_paths=[
        RepoRelPath(PurePath('lib/example/src/extra_bad.cc')),
        RepoRelPath(PurePath('lib/example/src/extra/extra_bad.cc')),
    ]))

    group = FileGroup(PurePath('example_struct'), component)

    correct = {
        IncompleteGroup(
            group,
            present=frozenset({
                RoleInGroup.DTGEN_TOML,
                RoleInGroup.SOURCE,
                RoleInGroup.TEST,
                RoleInGroup.BENCHMARK_SOURCE,
            }),
            missing=frozenset({RoleInGroup.PUBLIC_HEADER, RoleInGroup.BENCHMARK_HEADER}),
        ),
        UnrecognizedFile(ComponentRelPath(PurePath('src/bad.cc'), component))
    }

    assert result == correct
