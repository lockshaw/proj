from pathlib import PurePath
from .paths import (
    FileGroup,
    Component,
    File,
    RoleInGroup,
)
from typing import (
    Optional,
    Sequence,
    List,
    Iterator,
    Set,
    Union,
)
from .utils import (
    with_suffix_removed,
)
import re
from dataclasses import dataclass
from .json import Json
from .trees import FileTree
from .layout import scan_repo_for_files
import proj.toml as toml
from .config_file import ExtensionConfig
import itertools
from .unparse_project import get_repo_rel_path

@dataclass(frozen=True, order=True)
class IncludeSpec:
    path: PurePath
    system: bool

    def json(self) -> Json:
        return {
            "path": str(self.path),
            "system": self.system,
        }

def parse_include_spec(raw: str) -> IncludeSpec:
    if raw.startswith("<") and raw.endswith(">"):
        return IncludeSpec(path=PurePath(raw[1:-1]), system=True)
    else:
        return IncludeSpec(path=PurePath(raw), system=False)

@dataclass(frozen=True, order=True)
class SystemInclude:
    path: PurePath

@dataclass(frozen=True, order=True)
class UnknownInclude:
    path: PurePath


def get_include_path(file_group: FileGroup, header_extension: str) -> PurePath:
    assert file_group.component is not None
    return (
        file_group.component.name
        / file_group.group_path.parent
        / (file_group.group_path.name + header_extension)
    )

def get_generated_include_path(file_group: FileGroup, header_extension: str) -> PurePath:
    assert file_group.component is not None
    return (
        file_group.component.name
        / file_group.group_path.parent
        / (file_group.group_path.name + '.dtg' + header_extension)
    )

def get_include_path_for_file(file: File, header_extension: str) -> PurePath:
    if file.role == RoleInGroup.PUBLIC_HEADER:
        return get_include_path(file.group, header_extension)
    elif file.role == RoleInGroup.GENERATED_HEADER:
        return get_generated_include_path(file.group, header_extension)
    else:
        raise ValueError()

def get_file_for_include_path(include_path: PurePath, header_extension: str) -> Optional[File]:
    if len(include_path.parts) <= 1:
        return None

    component_name = include_path.parts[0]
    component = Component(component_name, component_type=None)

    file_rel_path = include_path.relative_to(PurePath(component_name))

    if file_rel_path.name.endswith('.dtg' + header_extension):
        return FileGroup(
            with_suffix_removed(file_rel_path, n=2),
            component,
        ).generated_header
    elif file_rel_path.name.endswith(header_extension):
        return FileGroup(
            with_suffix_removed(file_rel_path, n=1),
            component,
        ).public_header
    else:
        return None

def find_include_specs_in_cpp_file_contents(contents: str) -> Sequence[IncludeSpec]:
    def delimiter_is_system(delim: str) -> bool:
        assert delim in ['<', '"']
        return delim == '<'

    return [
        IncludeSpec(
            path=PurePath(m.group('include_path')),
            system=delimiter_is_system(m.group('delimiter')),
        )
        for m in re.finditer(r'#include\s+(?P<delimiter>[<"])(?P<include_path>\S+)[>"]', contents)
    ]

def recognize_include_spec_as_file(
    include_spec: IncludeSpec, header_extension: str,
) -> Union[File, SystemInclude, UnknownInclude]:
    if include_spec.system is False:
        file = get_file_for_include_path(include_spec.path, header_extension)
        if file is None:
            return UnknownInclude(include_spec.path)
        else:
            return file
    else:
        return SystemInclude(include_spec.path)

def find_includes_in_cpp_file_contents(contents: str, header_extension: str) -> Sequence[Union[File, SystemInclude, UnknownInclude]]:
    result: List[Union[File, SystemInclude, UnknownInclude]] = []
    for include_spec in find_include_specs_in_cpp_file_contents(contents):
        result.append(recognize_include_spec_as_file(include_spec, header_extension))
    return result

def _find_include_specs_in_dtgen_toml_file_contents(contents: str) -> Iterator[IncludeSpec]:
    try:
        raw = toml.loads(contents)
    except toml.TOMLDecodeError as e:
        raise RuntimeError("Failed to load toml") from e

    includes = raw.get('includes', tuple())
    src_includes = raw.get('src_includes', tuple())

    assert isinstance(includes, (list, tuple))
    assert isinstance(src_includes, (list, tuple))

    for include in itertools.chain(includes, src_includes):
        assert isinstance(include, str)
        yield parse_include_spec(include)

def find_include_specs_in_dtgen_toml_file_contents(contents: str) -> Sequence[IncludeSpec]:
    return list(_find_include_specs_in_dtgen_toml_file_contents(contents))

def find_includes_in_dtgen_toml_file_contents(contents: str, header_extension: str) -> Sequence[Union[File, SystemInclude, UnknownInclude]]:
    return [
        recognize_include_spec_as_file(include_spec, header_extension)
        for include_spec in
        find_include_specs_in_dtgen_toml_file_contents(contents)
    ]

def replace_include_in_cpp_file_contents(contents: str, curr: PurePath, goal: PurePath) -> str:
    def do_replace(s: str, open_delim: str, close_delim: str) -> str:
        replaced, _ = re.subn(
            fr'#include(\s+){re.escape(open_delim)}{re.escape(str(curr))}{re.escape(close_delim)}',
            fr'#include\1{open_delim}{str(goal)}{close_delim}',
            s,
        )
        return replaced

    contents = do_replace(contents, '"', '"')
    contents = do_replace(contents, '<', '>')
    return contents

def replace_file_group_include_in_cpp_file_contents(contents: str, curr: FileGroup, goal: FileGroup, header_extension: str) -> str:
    contents = replace_include_in_cpp_file_contents(
        contents,
        curr=get_include_path(curr, header_extension=header_extension),
        goal=get_include_path(goal, header_extension=header_extension),
    )

    contents = replace_include_in_cpp_file_contents(
        contents,
        curr=get_generated_include_path(curr, header_extension=header_extension),
        goal=get_generated_include_path(goal, header_extension=header_extension),
    )

    return contents

def replace_include_in_dtg_toml_file_contents(contents: str, curr: PurePath, goal: PurePath) -> str:
    result, _ = re.subn(fr'"{re.escape(str(curr))}"', f'"{goal}"', contents)
    return result

def replace_file_group_include_in_dtg_toml_file_contents(contents: str, curr: FileGroup, goal: FileGroup, header_extension: str) -> str:
    contents = replace_include_in_dtg_toml_file_contents(
        contents,
        curr=get_include_path(curr, header_extension=header_extension),
        goal=get_include_path(goal, header_extension=header_extension),
    )

    contents = replace_include_in_dtg_toml_file_contents(
        contents,
        curr=get_generated_include_path(curr, header_extension=header_extension),
        goal=get_generated_include_path(goal, header_extension=header_extension),
    )

    return contents

def find_occurrences_of_include(repo_file_tree: FileTree, include: IncludeSpec, extension_config: ExtensionConfig) -> Set[File]:
    return set(_find_occurrences_of_include(repo_file_tree, include, extension_config))

def _find_occurrences_of_include(repo_file_tree: FileTree, include: IncludeSpec, extension_config: ExtensionConfig) -> Iterator[File]:
    for file in scan_repo_for_files(repo_file_tree, extension_config):
        if isinstance(file, File):
            path = get_repo_rel_path(file, extension_config=extension_config).path
            if file.role in [RoleInGroup.GENERATED_HEADER, RoleInGroup.GENERATED_HEADER]:
                continue
            elif file.role == RoleInGroup.DTGEN_TOML:
                if include in find_include_specs_in_dtgen_toml_file_contents(
                    repo_file_tree.get_file_contents(path),
                ):
                    yield file
            elif file.role in [
                RoleInGroup.PUBLIC_HEADER,
                RoleInGroup.SOURCE,
                RoleInGroup.TEST,
                RoleInGroup.BENCHMARK_SOURCE,
                RoleInGroup.BENCHMARK_HEADER,
            ]:
                if include in find_include_specs_in_cpp_file_contents(
                    repo_file_tree.get_file_contents(path),
                ):
                    yield file
