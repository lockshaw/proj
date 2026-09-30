from proj.rm import (
    rm_file_group,
)
from proj.config_file import (
    ExtensionConfig,
)
from pathlib import PurePath
from proj.trees import (
    EmulatedPathTree,
    PathType,
)
from proj.paths import (
    RepoRelPath,
)
import copy

EXTENSION_CONFIG = ExtensionConfig(
    '.h',
    '.cc',
)

def test_rm_file_group() -> None:
    repo_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'CMakeLists.txt',
            '.proj.toml',
            'lib/CMakeLists.txt',
            'lib/person/CMakeLists.txt',
            'lib/person/include/person/example_variant.dtg.toml',
            'lib/person/src/person/out_of_date2.dtg.cc',
            'lib/airplane/include/airplane/my_airplane.dtg.toml',
            'lib/person/include/person/example_struct.dtg.toml',
            'lib/person/include/person/example_struct.h',
            'lib/person/src/person/example_struct.cc',
            'lib/person/test/src/person/example_struct.cc',
            'lib/person/benchmark/include/benchmark/person/example_struct.h',
            'lib/person/benchmark/src/benchmark/person/example_struct.cc',
        ]
    })

    target = RepoRelPath(PurePath('lib/person/src/person/example_struct.cc'))

    rm_file_group(
        repo_path_tree,
        target,
        EXTENSION_CONFIG,
        dry_run=False,
    )

    correct = EmulatedPathTree.from_lists(
        files=[
            'CMakeLists.txt',
            '.proj.toml',
            'lib/CMakeLists.txt',
            'lib/person/CMakeLists.txt',
            'lib/person/include/person/example_variant.dtg.toml',
            'lib/person/src/person/out_of_date2.dtg.cc',
            'lib/airplane/include/airplane/my_airplane.dtg.toml',
        ],
        dirs=[
            'lib/person/include/person/',
            'lib/person/src/person/',
            'lib/person/test/src/person/',
            'lib/person/benchmark/include/benchmark/person/',
            'lib/person/benchmark/src/benchmark/person/',
        ]
    )

    assert repo_path_tree == correct

def test_dry_run_rm_file_group() -> None:
    repo_path_tree = EmulatedPathTree.from_map({
        PurePath(p): PathType.FILE
        for p in [
            'CMakeLists.txt',
            '.proj.toml',
            'lib/CMakeLists.txt',
            'lib/person/CMakeLists.txt',
            'lib/person/include/person/example_variant.dtg.toml',
            'lib/person/src/person/out_of_date2.dtg.cc',
            'lib/airplane/include/airplane/my_airplane.dtg.toml',
            'lib/person/include/person/example_struct.dtg.toml',
            'lib/person/include/person/example_struct.h',
            'lib/person/src/person/example_struct.cc',
            'lib/person/test/src/person/example_struct.cc',
            'lib/person/benchmark/include/benchmark/person/example_struct.h',
            'lib/person/benchmark/src/benchmark/person/example_struct.cc',
        ]
    })

    original_path_tree = copy.deepcopy(repo_path_tree)

    target = RepoRelPath(PurePath('lib/person/src/person/example_struct.cc'))

    rm_file_group(
        repo_path_tree,
        target,
        EXTENSION_CONFIG,
        dry_run=True,
    )

    correct = original_path_tree

    assert repo_path_tree == correct
