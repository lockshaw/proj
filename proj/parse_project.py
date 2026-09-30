from .trees.path_tree import PathTree
from pathlib import PurePath
from typing import (
    Iterator,
    Optional,
    TYPE_CHECKING,
    Union,
)
from .paths import (
    Repo,
    RepoRelPath,
    Component,
    ComponentRelPath,
    File,
    RoleInGroup,
    FileGroup,
)
from .utils import map_optional
from proj.utils import is_relative_to

if TYPE_CHECKING:
    from .config_file import ExtensionConfig

def _possible_config_paths(d: PurePath) -> Iterator[PurePath]:
    for _d in [d, *d.parents]:
        config_path = _d / ".proj.toml"
        yield config_path

def find_repo(p: PurePath, path_tree: PathTree) -> Optional[Repo]:
    return map_optional(parse_repo_path(p, path_tree), lambda repo_rel: repo_rel.repo)

def parse_repo_path(p: PurePath, path_tree_or_repo: Union[PathTree, Repo]) -> Optional[RepoRelPath]:
    if isinstance(path_tree_or_repo, Repo):
        return RepoRelPath(p.relative_to(path_tree_or_repo.path), path_tree_or_repo)
    for possible_config in _possible_config_paths(p):
        if path_tree_or_repo.has_file(possible_config):
            repo_root = possible_config.parent
            return RepoRelPath(p.relative_to(repo_root), Repo(repo_root))
    return None

def parse_library_path(repo_rel: RepoRelPath) -> ComponentRelPath:
    assert repo_rel.path.parts[0] == 'lib', repo_rel.path
    library = Component.library(repo_rel.path.parts[1], repo_rel.repo)
    library_path = PurePath('lib') / library.name
    return ComponentRelPath(repo_rel.path.relative_to(library_path), library)

def parse_executable_path(repo_rel: RepoRelPath) -> ComponentRelPath:
    assert repo_rel.path.parts[0] == 'bin', repo_rel.path
    executable = Component.executable(repo_rel.path.parts[1], repo_rel.repo)
    executable_path = PurePath('bin') / executable.name
    return ComponentRelPath(repo_rel.path.relative_to(executable_path), executable)

def parse_component_path(repo_rel: RepoRelPath) -> ComponentRelPath:
    leading = repo_rel.path.parts[0]
    if leading == 'lib':
        return parse_library_path(repo_rel)
    elif leading == 'bin':
        return parse_executable_path(repo_rel)
    else:
        raise ValueError(f'Invalid component path {repo_rel}')

def find_libraries_in_repo(repo: Repo, path_tree: PathTree) -> Iterator[Component]:
    for lib_name in path_tree.ls_dir(repo.path / 'lib'):
        yield Component.library(lib_name.name, repo=repo)

def find_executables_in_repo(repo: Repo, path_tree: PathTree) -> Iterator[Component]:
    for bin_name in path_tree.ls_dir(repo.path / 'bin'):
        yield Component.executable(bin_name.name, repo=repo)


def parse_file_path(
    rel: Union[ComponentRelPath, RepoRelPath],
    extension_config: 'ExtensionConfig',
) -> Optional[File]:
    component_rel: ComponentRelPath
    if isinstance(rel, ComponentRelPath):
        component_rel = rel
    else:
        component_rel = parse_component_path(rel)

    assert component_rel.component is not None
    component = component_rel.component
    p = component_rel.path

    header_extension = extension_config.header_extension

    public_include_dir = PurePath('include') / component.name
    src_dir = PurePath('src') / component.name
    test_dir = PurePath('test/src') / component.name
    benchmark_include_dir = PurePath('benchmark/include/benchmark') / component.name
    benchmark_src_dir = PurePath('benchmark/src/benchmark') / component.name

    file_type: RoleInGroup
    group: FileGroup
    if is_relative_to(p, public_include_dir) and p.suffix == '.toml':
        pp = PurePath(p.stem)
        assert pp.suffix == '.dtg', pp
        file_type = RoleInGroup.DTGEN_TOML
        group = FileGroup(
            p.parent.relative_to(public_include_dir) / pp.stem,
            component,
        )
    elif is_relative_to(p, public_include_dir) and p.suffix == header_extension:
        pp = p.parent / p.stem
        if pp.suffix == '.dtg':
            file_type = RoleInGroup.GENERATED_HEADER
            group = FileGroup(
                p.parent.relative_to(public_include_dir) / pp.stem,
                component,
            )
        else:
            file_type = RoleInGroup.PUBLIC_HEADER
            group = FileGroup(
                p.parent.relative_to(public_include_dir) / p.stem,
                component,
            )

    elif is_relative_to(p, src_dir) and p != src_dir:
        pp = p.parent / p.stem
        if pp.suffix == '.dtg':
            file_type = RoleInGroup.GENERATED_SOURCE
            group = FileGroup(
                p.parent.relative_to(src_dir) / pp.stem,
                component,
            )
        elif p.suffix == extension_config.src_extension:
            file_type = RoleInGroup.SOURCE
            group = FileGroup(
                p.parent.relative_to(src_dir) / p.stem,
                component,
            )
        else:
            return None
    elif is_relative_to(p, test_dir):
        group=FileGroup(
            p.parent.relative_to(test_dir) / p.stem,
            component,
        )
        file_type=RoleInGroup.TEST
    elif is_relative_to(p, benchmark_include_dir):
        group=FileGroup(
            p.parent.relative_to(benchmark_include_dir) / p.stem,
            component,
        )
        file_type=RoleInGroup.BENCHMARK_HEADER
    elif is_relative_to(p, benchmark_src_dir):
        group=FileGroup(
            p.parent.relative_to(benchmark_src_dir) / p.stem,
            component,
        )
        file_type=RoleInGroup.BENCHMARK_SOURCE
    else:
        return None

    return File(
        group=group,
        role=file_type,
    )
