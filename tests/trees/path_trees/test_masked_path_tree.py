from proj.trees import (
    EmulatedPathTree,
    PathType,
    MaskedPathTree,
    IgnoreMask,
    AllowMask,
)
from pathlib import PurePath

def test_masked_path_tree() -> None:
    example_variant_path = PurePath('include/example/example_variant.dtg.toml')
    cmakelists_path = PurePath('CMakeLists.txt')
    example_struct_toml_path = PurePath('include/example/something/example_struct.dtg.toml')
    example_struct2_toml_path = PurePath('include/example2/example2_struct.dtg.toml')
    example_struct_cc_path = PurePath('src/example/example_struct.cc')

    path_tree = EmulatedPathTree.from_map({
        p: PathType.FILE
        for p in [
            cmakelists_path,
            example_struct_toml_path,
            example_struct_cc_path,
            example_variant_path,
            example_struct2_toml_path,
        ]
    })

    masked_path_tree = MaskedPathTree(
        path_tree, 
        IgnoreMask.from_iter(paths=['include/example']),
    )

    assert path_tree.has_path(example_variant_path)
    assert not masked_path_tree.has_path(example_variant_path)

    assert set(masked_path_tree.ls_dir(PurePath('include'))) == {PurePath('include/example2/')}

    sub_masked_path_tree = masked_path_tree.restrict_to_subdir(PurePath('include'))
    assert set(sub_masked_path_tree.files()) == {example_struct2_toml_path.relative_to(PurePath('include'))}

    sub_masked_path_tree2 = masked_path_tree.restrict_to_subdir(PurePath('include/example/something'))
    assert set(sub_masked_path_tree2.files()) == set()

def test_ignore_mask() -> None:
    mask = IgnoreMask.from_iter(
        paths=[],
        extensions=[
            '.swp',
        ],
    )

    assert mask.is_allowed(PurePath('hello/world/.x.swp')) is False
    assert mask.is_allowed(PurePath('hello/world/.x.swp.hi')) is True
    
def test_allow_mask() -> None:
    mask = AllowMask.from_iter(
        paths=[],
        extensions=[
            '.swp',
        ],
    )

    assert mask.is_allowed(PurePath('hello/world/.x.swp')) is True
    assert mask.is_allowed(PurePath('hello/world/.x.swp.hi')) is False

def test_masked_path_tree_subdir_restriction() -> None:
    path_tree = EmulatedPathTree.from_lists(
        files=[
            'a/b/c.txt',
        ],
        dirs=[],
    )

    masked_path_tree = MaskedPathTree(
        path_tree, 
        IgnoreMask.from_iter(
            paths=[
                'include/example',
                'include/example2',
            ],
            extensions=[],
        ),
    )

    sub_masked_path_tree = masked_path_tree.restrict_to_subdir(PurePath('include'))
    assert sub_masked_path_tree.mask == IgnoreMask.from_iter(paths=[
        'example',
        'example2',
    ])

    sub_masked_path_tree2 = masked_path_tree.restrict_to_subdir(PurePath('include/example'))
    assert sub_masked_path_tree2.mask == IgnoreMask.from_iter(paths=[
        PurePath('.'),
    ])
    assert set(sub_masked_path_tree2.files()) == set()
