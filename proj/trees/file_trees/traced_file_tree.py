from ..file_tree import (
    TracedMutableFileTree,
    MoveTrace,
    MkDirTrace,
    RmFileTrace,
    CreateFileTrace,
    ModifyFileTrace,
    MutableFileTree,
)
from typing import (
    List,
    Union,
    Iterator,
)
from pathlib import PurePath

class MutableTracedFileTreeByWrapping(TracedMutableFileTree):
    _wrapped: MutableFileTree
    _trace: List[Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
        CreateFileTrace,
        ModifyFileTrace,
    ]]

    def __init__(self, file_tree: MutableFileTree) -> None:
        self._wrapped = file_tree
        self._trace = list()

    def get_path_trace(self) -> List[Union[MoveTrace, MkDirTrace, RmFileTrace]]:
        return [
            t for t in self._trace if isinstance(t, (MoveTrace, MkDirTrace, RmFileTrace))
        ]

    def get_file_trace(self) -> List[Union[MoveTrace, MkDirTrace, RmFileTrace, CreateFileTrace, ModifyFileTrace]]:
        return list(self._trace)

    def get_file_contents(
        self,
        p: PurePath,
    ) -> str:
        return self._wrapped.get_file_contents(p=p)

    def has_path(self, p: PurePath) -> bool:
        return self._wrapped.has_path(p=p)

    def has_dir(self, p: PurePath) -> bool:
        return self._wrapped.has_dir(p=p)

    def ls_dir(self, p: PurePath) -> Iterator[PurePath]:
        return self._wrapped.ls_dir(p=p)

    def restrict_to_subdir(self, p: PurePath) -> 'MutableTracedFileTreeByWrapping':
        return MutableTracedFileTreeByWrapping(
            self._wrapped.restrict_to_subdir(p=p),
        )

    def has_file(self, p: PurePath) -> bool:
        return self._wrapped.has_file(p=p)

    def with_extension(self, extension: str) -> Iterator[PurePath]:
        return self._wrapped.with_extension(extension=extension)

    def files(self) -> Iterator[PurePath]:
        return self._wrapped.files()

    def dirs(self) -> Iterator[PurePath]:
        return self._wrapped.dirs()

    def _mkdir_in_trace(self, p: PurePath) -> None:
        for parent in list(p.parents)[::-1]:
            if not self._wrapped.has_dir(parent):
                self._trace.append(
                    MkDirTrace(
                        path=parent,
                    )
                )
        if not self._wrapped.has_dir(p):
            self._trace.append(
                MkDirTrace(
                    path=p,
                )
            )

    def mkdir(
        self,
        p: PurePath,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        self._mkdir_in_trace(p)
        self._wrapped.mkdir(
            p=p,
            exist_ok=exist_ok,
            parents=parents,
        )

    def rename(
        self,
        src: PurePath,
        dst: PurePath,
    ) -> None:
        self._trace.append(
            MoveTrace(
                src=src,
                dst=dst,
            )
        )
        self._wrapped.rename(
            src=src,
            dst=dst,
        )

    def rm_file(
        self,
        p: PurePath,
    ) -> None:
        self._trace.append(
            RmFileTrace(
                path=p,
            )
        )
        self._wrapped.rm_file(
            p=p,
        )

    def set_file_contents(
        self,
        p: PurePath,
        contents: str,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        self._mkdir_in_trace(p.parent)
        if self._wrapped.has_file(p):
            curr_contents = self._wrapped.get_file_contents(p)

            if curr_contents != contents:
                self._trace.append(
                    ModifyFileTrace(
                        path=p,
                        old_contents=curr_contents,
                        new_contents=contents,
                    )
                )
        else:
            self._trace.append(
                CreateFileTrace(
                    path=p,
                    contents=contents,
                )
            )
        self._wrapped.set_file_contents(
            p=p,
            contents=contents,
            exist_ok=exist_ok,
            parents=parents,
        )
