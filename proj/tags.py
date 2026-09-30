from dataclasses import (
    dataclass, field
)
from pathlib import PurePath
from typing import (
    Set,
    Tuple,
    Iterator,
)
from proj.trees import FileTree
from proj.dtgen.project import load_dtgen_specs_in_repo
from proj.dtgen.struct.spec import StructSpec
from proj.dtgen.variant.spec import VariantSpec
from proj.dtgen.enum.spec import EnumSpec
from proj.strenum import StrEnum
from proj.config_file import (
    ExtensionConfig,
    ProjectConfig,
)
from . import subprocess_trace as subprocess
import os
from proj.unparse_project import get_repo_rel_path
from proj.trees import load_filesystem_for_repo

class TagType(StrEnum):
    CLASS = 'c'
    ENUM = 'g'

@dataclass(frozen=True)
class Tag:
    tag_name: str
    file_path: PurePath
    ex_cmd: str
    tag_type: TagType
    extension_fields: Tuple[str, ...] = field(default=())

    def serialize(self) -> str:
        return '\t'.join([
            self.tag_name,
            str(self.file_path),
            f'{self.ex_cmd};"',
            self.tag_type.value,
            *self.extension_fields,
        ])

def _tags_for_dtgen_struct(
    spec: StructSpec,
    path: PurePath,
) -> Iterator[Tag]:
    yield Tag(
        tag_name=spec.name,
        file_path=path,
        ex_cmd=f'/^name = "{spec.name}"$/',
        tag_type=TagType.CLASS,
    )

def tags_for_dtgen_struct(
    spec: StructSpec,
    path: PurePath,
) -> Set[Tag]:
    return set(_tags_for_dtgen_struct(spec, path))

def _tags_for_dtgen_variant(
    spec: VariantSpec,
    path: PurePath,
) -> Iterator[Tag]:
    yield Tag(
        tag_name=spec.name,
        file_path=path,
        ex_cmd=f'/^name = "{spec.name}"$/',
        tag_type=TagType.CLASS,
    )

def tags_for_dtgen_variant(
    spec: VariantSpec,
    path: PurePath,
) -> Set[Tag]:
    return set(_tags_for_dtgen_variant(spec, path))

def _tags_for_dtgen_enum(
    spec: EnumSpec,
    path: PurePath,
) -> Iterator[Tag]:
    yield Tag(
        tag_name=spec.name,
        file_path=path,
        ex_cmd=f'/^name = "{spec.name}"$/',
        tag_type=TagType.ENUM,
    )

def tags_for_dtgen_enum(
    spec: EnumSpec,
    path: PurePath,
) -> Set[Tag]:
    return set(_tags_for_dtgen_enum(spec, path))

def _generate_tags_for_dtgen(
    file_tree: FileTree,
    extension_config: ExtensionConfig,
) -> Iterator[Tag]:
    for file_, spec in load_dtgen_specs_in_repo(file_tree, extension_config).items():
        spec_path = get_repo_rel_path(file_, extension_config)

        if isinstance(spec, StructSpec):
            yield from _tags_for_dtgen_struct(spec, spec_path.path)
        elif isinstance(spec, EnumSpec):
            yield from _tags_for_dtgen_enum(spec, spec_path.path)
        elif isinstance(spec, VariantSpec):
            yield from _tags_for_dtgen_variant(spec, spec_path.path)
        else:
            raise ValueError(f'Invalid spec {spec}')

def generate_tags_for_dtgen(
    file_tree: FileTree,
    extension_config: ExtensionConfig,
) -> Set[Tag]:
    return set(_generate_tags_for_dtgen(file_tree, extension_config))

def generate_tag_file(
    config: ProjectConfig,
) -> None:
    subprocess.check_call(
        [
            "ctags",
            "--kinds-c++=-t",
            "--exclude=*.dtg" + config.extension_config.header_extension,
            "--exclude=*.dtg" + config.extension_config.src_extension,
            "--recurse",
            "lib/",
            "bin/",
        ],
        env=os.environ,
        cwd=config.base,
    )
    TAG_FILE_PATH = config.base / 'tags'
    assert TAG_FILE_PATH.is_file()

    repo_file_tree = load_filesystem_for_repo(config.repo)

    dtgen_tags = generate_tags_for_dtgen(
        repo_file_tree,
        config.extension_config,
    )

    tag_file_lines = TAG_FILE_PATH.read_text().splitlines()
    tag_file_lines.extend([t.serialize() for t in dtgen_tags])
    tag_file_lines.sort()

    with TAG_FILE_PATH.open('w') as f:
        f.writelines((l + '\n') for l in tag_file_lines)
