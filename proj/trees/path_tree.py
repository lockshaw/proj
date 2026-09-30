from typing import (
    Iterator,
    Sequence,
    Union,
    Iterable,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from typing import Self

from pathlib import (
    PurePath,
)
import abc
from dataclasses import dataclass

class PathTree(abc.ABC):
    @abc.abstractmethod
    def has_path(self, p: PurePath) -> bool:
        ...

    @abc.abstractmethod
    def has_dir(self, p: PurePath) -> bool:
        ...

    @abc.abstractmethod
    def ls_dir(self, p: PurePath) -> Iterator[PurePath]:
        ...

    @abc.abstractmethod
    def restrict_to_subdir(self, p: PurePath) -> 'Self':
        ...

    @abc.abstractmethod
    def has_file(self, p: PurePath) -> bool:
        ...

    @abc.abstractmethod
    def with_extension(self, extension: str) -> Iterator[PurePath]:
        ...

    @abc.abstractmethod
    def files(self) -> Iterator[PurePath]:
        ...

    @abc.abstractmethod
    def dirs(self) -> Iterator[PurePath]:
        ...

class MutablePathTree(PathTree):
    @abc.abstractmethod
    def mkdir(
        self,
        p: PurePath,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        ...

    @abc.abstractmethod
    def rename(self, src: PurePath, dst: PurePath) -> None:
        ...

    @abc.abstractmethod
    def rm_file(self, p: PurePath) -> None:
        ...

@dataclass(frozen=True)
class MoveTrace:
    src: PurePath
    dst: PurePath

@dataclass(frozen=True)
class MkDirTrace:
    path: PurePath

@dataclass(frozen=True)
class RmFileTrace:
    path: PurePath


def execute_trace_element_on_path_tree(
    trace_element: Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
    ],
    path_tree: MutablePathTree,
) -> None:
    if isinstance(trace_element, MoveTrace):
        path_tree.rename(src=trace_element.src, dst=trace_element.dst)
    elif isinstance(trace_element, MkDirTrace):
        path_tree.mkdir(trace_element.path, exist_ok=False, parents=False)
    elif isinstance(trace_element, RmFileTrace):
        path_tree.rm_file(trace_element.path)

def replay_trace_on_path_tree(
    path_trace: Iterable[Union[MoveTrace, MkDirTrace, RmFileTrace]],
    path_tree: MutablePathTree,
) -> None:
    for trace_elem in path_trace:
        execute_trace_element_on_path_tree(trace_elem, path_tree)


class TracedMutablePathTree(MutablePathTree):
    @abc.abstractmethod
    def get_path_trace(
        self,
    ) -> Sequence[Union[MoveTrace, MkDirTrace, RmFileTrace]]:
        ...
