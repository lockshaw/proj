from proj.move import (
    get_move_plan,
    ConcreteMove,
    perform_file_group_move,
    perform_file_group_move_with_include_and_ifndef_update,
)
from proj.trees import (
    PathType,
    EmulatedPathTree,
    EmulatedFileTree,
)
from proj.paths import (
    RepoRelPath,
    Component,
    FileGroup,
    File,
    RoleInGroup,
)
from proj.config_file import (
    ExtensionConfig,
)
from pathlib import PurePath
import copy

EXTENSION_CONFIG = ExtensionConfig(
    '.h',
    '.cc',
)

def test_get_move_plan() -> None:
    struct_toml = 'lib/person/include/person/example_struct.dtg.toml'
    header = 'lib/person/include/person/example_struct.h'
    src_f = 'lib/person/src/person/example_struct.cc'
    test_src = 'lib/person/test/src/person/example_struct.cc'
    benchmark_hdr = 'lib/person/benchmark/include/benchmark/person/example_struct.h'
    benchmark_src = 'lib/person/benchmark/src/benchmark/person/example_struct.cc'

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
            struct_toml,
            header,
            src_f,
            test_src,
            benchmark_hdr,
            benchmark_src,
        ]
    })

    src_library = Component.library('person')

    src = File(
        FileGroup(PurePath('example_struct'), src_library),
        RoleInGroup.SOURCE,
    )

    dst_library = Component.library('airplane')

    dst = File(
        FileGroup(PurePath('my_other_airplane'), dst_library),
        RoleInGroup.SOURCE,
    )

    def move(s: str, d: str) -> ConcreteMove:
        return ConcreteMove(
            RepoRelPath(PurePath(s)),
            RepoRelPath(PurePath(d)),
        )

    result = get_move_plan(repo_path_tree, src, dst, EXTENSION_CONFIG)
    correct = {
        move(struct_toml, 'lib/airplane/include/airplane/my_other_airplane.dtg.toml'),
        move(header, 'lib/airplane/include/airplane/my_other_airplane.h'),
        move(src_f, 'lib/airplane/src/airplane/my_other_airplane.cc'),
        move(test_src, 'lib/airplane/test/src/airplane/my_other_airplane.cc'),
        move(benchmark_src, 'lib/airplane/benchmark/src/benchmark/airplane/my_other_airplane.cc'),
        move(benchmark_hdr, 'lib/airplane/benchmark/include/benchmark/airplane/my_other_airplane.h'),
    }

    assert result == correct

def test_perform_file_group_move() -> None:
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

    src = RepoRelPath(PurePath('lib/person/src/person/example_struct.cc'))
    dst = RepoRelPath(PurePath('lib/airplane/src/airplane/example_airplane.cc'))

    perform_file_group_move(
        repo_path_tree,
        src,
        dst,
        EXTENSION_CONFIG,
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
            'lib/airplane/include/airplane/example_airplane.dtg.toml',
            'lib/airplane/include/airplane/example_airplane.h',
            'lib/airplane/src/airplane/example_airplane.cc',
            'lib/airplane/test/src/airplane/example_airplane.cc',
            'lib/airplane/benchmark/include/benchmark/airplane/example_airplane.h',
            'lib/airplane/benchmark/src/benchmark/airplane/example_airplane.cc',
        ],
        dirs=[
            'lib/person/include/person/',
            'lib/person/src/person/',
            'lib/person/test/src/person/',
            'lib/person/benchmark/src/benchmark/person/',
            'lib/person/benchmark/include/benchmark/person/',
        ]
    )

    assert repo_path_tree == correct

def test_perform_file_group_move_to_directory() -> None:
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

    src = RepoRelPath(PurePath('lib/person/src/person/example_struct.cc'))
    dst = RepoRelPath(PurePath('lib/airplane/src/airplane/'))

    perform_file_group_move(
        repo_path_tree,
        src,
        dst,
        EXTENSION_CONFIG,
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
            'lib/airplane/include/airplane/example_struct.dtg.toml',
            'lib/airplane/include/airplane/example_struct.h',
            'lib/airplane/src/airplane/example_struct.cc',
            'lib/airplane/test/src/airplane/example_struct.cc',
            'lib/airplane/benchmark/include/benchmark/airplane/example_struct.h',
            'lib/airplane/benchmark/src/benchmark/airplane/example_struct.cc',
        ],
        dirs=[
            'lib/person/include/person/',
            'lib/person/src/person/',
            'lib/person/test/src/person/',
            'lib/person/benchmark/src/benchmark/person/',
            'lib/person/benchmark/include/benchmark/person/',
        ]
    )

    assert repo_path_tree == correct

def test_perform_file_group_move_to_existing_directory() -> None:
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

    src = RepoRelPath(PurePath('lib/person/include/person/example_struct.h'))
    dst = RepoRelPath(PurePath('lib/airplane/include/airplane/'))

    perform_file_group_move(
        repo_path_tree,
        src,
        dst,
        EXTENSION_CONFIG,
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
            'lib/airplane/include/airplane/example_struct.dtg.toml',
            'lib/airplane/include/airplane/example_struct.h',
            'lib/airplane/src/airplane/example_struct.cc',
            'lib/airplane/test/src/airplane/example_struct.cc',
            'lib/airplane/benchmark/include/benchmark/airplane/example_struct.h',
            'lib/airplane/benchmark/src/benchmark/airplane/example_struct.cc',
        ],
        dirs=[
            'lib/person/include/person/',
            'lib/person/src/person/',
            'lib/person/test/src/person/',
            'lib/person/benchmark/src/benchmark/person/',
            'lib/person/benchmark/include/benchmark/person/',
        ]
    )

    assert repo_path_tree == correct


def test_perform_file_group_move_to_current_location() -> None:
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
            'lib/person/benchmark/src/benchmark/include/person/example_struct.cc',
        ]
    })

    correct = copy.deepcopy(repo_path_tree)

    src = RepoRelPath(PurePath('lib/person/src/person/example_struct.cc'))
    dst = src

    perform_file_group_move(
        repo_path_tree,
        src,
        dst,
        EXTENSION_CONFIG,
    )

    assert repo_path_tree == correct

def test_perform_file_group_move_with_include_and_ifndef_update() -> None:
    file_tree = EmulatedFileTree.from_lists(
        files=[
            (
                'lib/example/include/example/coordinate.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyCoordinate"',
                    'type = "struct"',
                    'features = []',
                    'includes = [',
                    '  "example/integer.dtg.h",',
                    ']',
                    '',
                    '[[fields]]',
                    'name = x_coord',
                    'type = ::FlexFlow::MyInteger',
                    '',
                    '[[fields]]',
                    'name = y_coord',
                    'type = ::FlexFlow::MyInteger',
                ]),
            ),
            (
                'lib/example/include/example/integer.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyInteger"',
                    'type = "struct"',
                    'features = []',
                    'includes = []',
                    '',
                    '[[fields]]',
                    'name = raw',
                    'type = int',
                ]),
            )
        ],
        dirs=[]
    )

    src = RepoRelPath(PurePath('lib/example/include/example/integer.dtg.toml'))
    dst = RepoRelPath(PurePath('lib/example/include/example/my_integer.dtg.toml'))

    extension_config = ExtensionConfig(
        header_extension='.h',
        src_extension='.cc',
    )

    ifndef_base = '_BASE_'

    perform_file_group_move_with_include_and_ifndef_update(
        repo_file_tree=file_tree,
        src=src,
        dst=dst,
        extension_config=extension_config,
        ifndef_base=ifndef_base,
        update_includes=True,
        update_ifndefs=True,
        dry_run=False,
    )

    correct = EmulatedFileTree.from_lists(
        files=[
            (
                'lib/example/include/example/coordinate.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyCoordinate"',
                    'type = "struct"',
                    'features = []',
                    'includes = [',
                    '  "example/my_integer.dtg.h",',
                    ']',
                    '',
                    '[[fields]]',
                    'name = x_coord',
                    'type = ::FlexFlow::MyInteger',
                    '',
                    '[[fields]]',
                    'name = y_coord',
                    'type = ::FlexFlow::MyInteger',
                ]),
            ),
            (
                'lib/example/include/example/my_integer.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyInteger"',
                    'type = "struct"',
                    'features = []',
                    'includes = []',
                    '',
                    '[[fields]]',
                    'name = raw',
                    'type = int',
                ]),
            )
        ],
        dirs=[]
    )

    assert file_tree == correct

def test_perform_file_group_move_with_include_and_ifndef_update_is_atomic() -> None:
    file_tree = EmulatedFileTree.from_lists(
        files=[
            (
                'lib/example/include/example/coordinate.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyCoordinate"',
                    'type = "struct"',
                    'features = []',
                    'includes = [',
                    '  "example/integer.dtg.h",',
                    ']',
                    '',
                    '[[fields]]',
                    'name = x_coord',
                    'type = ::FlexFlow::MyInteger',
                    '',
                    '[[fields]]',
                    'name = y_coord',
                    'type = ::FlexFlow::MyInteger',
                ]),
            ),
            (
                'lib/example/include/example/integer.dtg.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "MyInteger"',
                    'type = "struct"',
                    'features = []',
                    'includes = []',
                    '',
                    '[[fields]]',
                    'name = raw',
                    'type = int',
                ]),
            ),
            (
                'lib/example/include/example/something_invalid.struct.toml',
                '\n'.join([
                    'namespace = "FlexFlow"',
                    'name = "SomethingInvalid"',
                    'type = "struct"',
                    'features = []',
                    'includes = []',
                    '',
                    '[[fields]]',
                    'name = raw',
                    'type = int',
                ]),
            )
        ],
        dirs=[]
    )

    src = RepoRelPath(PurePath('lib/example/include/example/integer.dtg.toml'))
    dst = RepoRelPath(PurePath('lib/example/include/example/my_integer.dtg.toml'))

    extension_config = ExtensionConfig(
        header_extension='.h',
        src_extension='.cc',
    )

    ifndef_base = '_BASE_'

    correct = copy.deepcopy(file_tree)

    try:
        perform_file_group_move_with_include_and_ifndef_update(
            repo_file_tree=file_tree,
            src=src,
            dst=dst,
            extension_config=extension_config,
            ifndef_base=ifndef_base,
            update_includes=True,
            update_ifndefs=True,
            dry_run=False,
        )
    except Exception:
        pass

    assert file_tree == correct
