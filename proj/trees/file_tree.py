from pathlib import (
    PurePath,
)
from .path_tree import (
    PathTree,
    MutablePathTree,
    TracedMutablePathTree,
    MoveTrace,
    MkDirTrace,
    RmFileTrace,
)
import abc
from dataclasses import dataclass
from typing import (
    Sequence,
    Union,
    Iterable,
)
import difflib

class FileTree(PathTree):
    @abc.abstractmethod
    def get_file_contents(
        self,
        p: PurePath,
    ) -> str:
        ...

@dataclass(frozen=True)
class ModifyFileTrace:
    path: PurePath
    old_contents: str
    new_contents: str

    def __post_init__(self) -> None:
        assert self.old_contents != self.new_contents

    @property
    def diff(self) -> str:
        return '\n'.join(
            list(difflib.unified_diff(
                self.old_contents.splitlines(),
                self.new_contents.splitlines(),
                lineterm='\n',
            ))[2:]
        )

@dataclass(frozen=True)
class CreateFileTrace:
    path: PurePath
    contents: str

class MutableFileTree(MutablePathTree, FileTree):
    @abc.abstractmethod
    def set_file_contents(
        self,
        p: PurePath,
        contents: str,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        ...

def execute_trace_element_on_file_tree(
    trace_element: Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
        CreateFileTrace,
        ModifyFileTrace,
    ],
    file_tree: MutableFileTree,
) -> None:
    if isinstance(trace_element, MoveTrace):
        file_tree.rename(src=trace_element.src, dst=trace_element.dst)
    elif isinstance(trace_element, MkDirTrace):
        file_tree.mkdir(trace_element.path, exist_ok=False, parents=False)
    elif isinstance(trace_element, RmFileTrace):
        file_tree.rm_file(trace_element.path)
    elif isinstance(trace_element, CreateFileTrace):
        assert not file_tree.has_file(trace_element.path)
        file_tree.set_file_contents(trace_element.path, trace_element.contents, exist_ok=False, parents=False)
    elif isinstance(trace_element, ModifyFileTrace):
        curr_contents = file_tree.get_file_contents(trace_element.path)
        assert curr_contents == trace_element.old_contents
        file_tree.set_file_contents(trace_element.path, trace_element.new_contents, exist_ok=True, parents=False)

def replay_trace_on_file_tree(
    file_trace: Iterable[Union[MoveTrace, MkDirTrace, RmFileTrace, CreateFileTrace, ModifyFileTrace]],
    file_tree: MutableFileTree,
) -> None:
    for trace_elem in file_trace:
        execute_trace_element_on_file_tree(trace_elem, file_tree)


class TracedMutableFileTree(MutableFileTree, TracedMutablePathTree):
    @abc.abstractmethod
    def get_file_trace(self) -> Sequence[Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
        CreateFileTrace,
        ModifyFileTrace,
    ]]:
        ...

class FileTreeWithMtime(FileTree):
    @abc.abstractmethod
    def get_mtime(self, p: PurePath) -> float:
        ...

class MutableFileTreeWithMtime(MutableFileTree, FileTreeWithMtime):
    ...
