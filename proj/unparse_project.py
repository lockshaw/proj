from .paths import (
    File,
    ComponentRelPath,
    Component,
    ComponentType,
    RoleInGroup,
    RepoRelPath,
)
from .config_file import ExtensionConfig
from pathlib import PurePath
from typing import (
    Union,
    Optional,
)

def get_component_rel_path(file: File, extension_config: ExtensionConfig) -> ComponentRelPath:
    group_dir = file.group.group_path.parent
    group_name = file.group.group_path.name

    assert file.group is not None
    assert file.group.component is not None
    component = file.group.component
    component_name = file.group.component.name

    header_extension = extension_config.header_extension
    source_extension = extension_config.src_extension

    rel: PurePath
    if file.role == RoleInGroup.PUBLIC_HEADER:
        rel = PurePath('include') / component_name / group_dir / (group_name + header_extension)
    elif file.role == RoleInGroup.SOURCE:
        rel = PurePath('src') / component_name / group_dir / (group_name + source_extension)
    elif file.role == RoleInGroup.TEST:
        rel = PurePath('test/src') / component_name / group_dir / (group_name + source_extension)
    elif file.role == RoleInGroup.BENCHMARK_HEADER:
        rel = PurePath('benchmark/include/benchmark') / component_name / group_dir / (group_name + header_extension)
    elif file.role == RoleInGroup.BENCHMARK_SOURCE:
        rel = PurePath('benchmark/src/benchmark') / component_name / group_dir / (group_name + source_extension)
    elif file.role == RoleInGroup.DTGEN_TOML:
        rel = PurePath('include') / component_name / group_dir / (group_name + '.dtg.toml')
    elif file.role == RoleInGroup.GENERATED_HEADER:
        rel = PurePath('include') / component_name / group_dir / (group_name + '.dtg' + header_extension)
    elif file.role == RoleInGroup.GENERATED_SOURCE:
        rel = PurePath('src') / component_name / group_dir / (group_name + '.dtg' + source_extension)
    else:
        raise ValueError()

    return ComponentRelPath(rel, component)

def _get_repo_rel_path_for_file(file: File, extension_config: ExtensionConfig) -> RepoRelPath:
    component_rel_path = get_component_rel_path(file, extension_config)

    return _get_repo_rel_path_for_component_rel_path(component_rel_path)

def _get_repo_rel_path_for_component_rel_path(component_rel_path: ComponentRelPath) -> RepoRelPath:
    component = component_rel_path.component
    assert component is not None

    base: PurePath
    if component.component_type == ComponentType.LIBRARY:
        base = PurePath('lib')
    elif component.component_type == ComponentType.EXECUTABLE:
        base = PurePath('bin')
    else:
        raise ValueError(f'Unknown component type {component.component_type}')

    return RepoRelPath(base / component.name / component_rel_path.path, component.repo)

def get_repo_rel_path(x: Union[File, ComponentRelPath, Component], extension_config: Optional[ExtensionConfig] = None) -> RepoRelPath:
    if isinstance(x, File):
        assert extension_config is not None
        return _get_repo_rel_path_for_file(x, extension_config)
    if isinstance(x, ComponentRelPath):
        return _get_repo_rel_path_for_component_rel_path(x)
    else:
        raise NotImplementedError()

def get_fullpath(x: Union[File, ComponentRelPath, Component, RepoRelPath], extension_config: Optional[ExtensionConfig] = None) -> PurePath:
    if isinstance(x, File):
        assert extension_config is not None
        return _get_fullpath_for_file(x, extension_config)
    elif isinstance(x, ComponentRelPath):
        return _get_fullpath_for_component_rel_path(x)
    elif isinstance(x, Component):
        return _get_fullpath_for_component(x)
    elif isinstance(x, RepoRelPath):
        return _get_fullpath_for_repo_rel_path(x)
    else:
        raise TypeError()

def _get_fullpath_for_file(file: File, extension_config: ExtensionConfig) -> PurePath:
    component_rel_path = get_component_rel_path(file, extension_config)
    return _get_fullpath_for_component_rel_path(component_rel_path)

def _get_fullpath_for_component_rel_path(component_rel: ComponentRelPath) -> PurePath:
    assert component_rel.component is not None
    return _get_fullpath_for_component(component_rel.component) / component_rel.path

def _get_fullpath_for_component(component: Component) -> PurePath:
    assert component.repo is not None
    repo_path = component.repo.path
    if component.component_type == ComponentType.LIBRARY:
        return repo_path / 'lib' / component.name
    elif component.component_type == ComponentType.EXECUTABLE:
        return repo_path / 'bin' / component.name
    else:
        raise ValueError(f'Unknown component type {component.component_type}')

def _get_fullpath_for_repo_rel_path(repo_rel: RepoRelPath) -> PurePath:
    assert repo_rel.repo is not None
    return repo_rel.repo.path / repo_rel.path
