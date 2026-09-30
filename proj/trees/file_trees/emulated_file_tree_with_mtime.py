from dataclasses import dataclass
from typing import (
    Dict,
    Optional,
    Iterator,
    Mapping,
    Iterable,
    Union,
)
from ..file_tree import MutableFileTreeWithMtime
from ..path_trees import EmulatedPathTree, PathType
from .emulated_file_tree import EmulatedFileTree
from pathlib import PurePath
from typing import Tuple
from proj.utils import is_relative_to

@dataclass(eq=True)
class PathRecord:
    contents: Optional[str]
    mtime: float

    def is_dir(self) -> bool:
        return self.contents is None

    def is_file(self) -> bool:
        return self.contents is not None

@dataclass(eq=True)
class EmulatedFileTreeWithMtime(MutableFileTreeWithMtime):
    _m: Dict[PurePath, PathRecord]
    _curr_time: float

    def has_path(self, p: PurePath) -> bool:
        return p in self._m

    def has_dir(self, p: PurePath) -> bool:
        if not self.has_path(p):
            return False
        return self._m[p].is_dir()

    def has_file(self, p: PurePath) -> bool:
        if not self.has_path(p):
            return False
        return self._m[p].is_file()

    def ls_dir(self, p: PurePath) -> Iterator[PurePath]:
        assert self.has_dir(p)
        for path in self._m:
            if path == (p / path.name):
                yield path

    def rename(self, src: PurePath, dst: PurePath) -> None:
        assert self.has_file(src)
        assert not self.has_file(dst)
        self._m[dst] = self._m[src]
        del self._m[src]

    def mkdir(
        self,
        p: PurePath,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        if not exist_ok:
            assert not self.has_dir(p)
        if parents:
            for parent in list(p.parents)[::-1]:
                self.mkdir(parent, exist_ok=True, parents=False)
        self._m[p] = PathRecord(
            contents=None,
            mtime=self._curr_time,
        )

    def get_file_contents(
        self,
        p: PurePath
    ) -> str:
        assert self.has_file(p)
        contents = self._m[p].contents
        assert contents is not None
        return contents

    def set_file_contents(
        self,
        p: PurePath,
        contents: str,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        if not exist_ok:
            assert not self.has_file(p)
        if parents:
            self.mkdir(p.parent)
        self._m[p] = PathRecord(
            contents=contents,
            mtime=self._curr_time,
        )

    def set_curr_time(
        self,
        t: float
    ) -> None:
        assert t >= self._curr_time
        self._mtime = t

    def get_curr_time(
        self,
    ) -> float:
        return self._mtime

    def get_mtime(
        self,
        p: PurePath,
    ) -> float:
        assert self.has_path(p)
        return self._m[p].mtime

    def rm_file(self, p: PurePath) -> None:
        assert self.has_file(p)
        del self._m[p]

    def restrict_to_subdir(self, p: PurePath) -> 'EmulatedFileTreeWithMtime':
        assert self.has_dir(p)
        return EmulatedFileTreeWithMtime(
            {
                k.relative_to(p): v for k, v in self._m.items()
                if is_relative_to(k, p)
            },
            self._curr_time,
        )

    def with_extension(self, extension: str) -> Iterator[PurePath]:
        assert extension.startswith('.')
        for path in self._m:
            if path.name.endswith(extension):
                yield path

    def files(self) -> Iterator[PurePath]:
        for path in self._m:
            if self.has_file(path):
                yield path

    def dirs(self) -> Iterator[PurePath]:
        for path in self._m:
            if self.has_dir(path):
                yield path

    def path_tree(self) -> EmulatedPathTree:
        def get_file_type(v: PathRecord) -> PathType:
            if v.contents is None:
                return PathType.DIR
            else:
                return PathType.FILE

        return EmulatedPathTree({
            k: get_file_type(v) for k, v in self._m.items()
        })

    def without_mtime(self) -> EmulatedFileTree:
        return EmulatedFileTree.from_lists(
            files=[
                (p, self.get_file_contents(p)) for p in self.files()
            ],
            dirs=[
                p for p in self.dirs()
            ],
        )

    @staticmethod
    def from_map(curr_time: float, m: Mapping[PurePath, PathRecord]) -> 'EmulatedFileTreeWithMtime':
        expanded: Dict[PurePath, PathRecord] = {}
        for p, record in m.items():
            for parent in p.parents:
                existing_parent = expanded.get(parent, None)
                new_parent = PathRecord(contents=None, mtime=curr_time)
                if existing_parent is None:
                    expanded[parent] = new_parent
                else:
                    assert new_parent == existing_parent
            expanded[p] = record
        return EmulatedFileTreeWithMtime(expanded, curr_time)

    @staticmethod
    def from_lists(
        curr_time: float,
        files: Iterable[Tuple[Union[str, PurePath], float, str]],
        dirs: Iterable[Tuple[Union[str, PurePath], float]],
    ) -> 'EmulatedFileTreeWithMtime':
        return EmulatedFileTreeWithMtime.from_map(
            curr_time,
            {
                **{
                    PurePath(p): PathRecord(contents=c, mtime=t)
                    for p, t, c in files
                },
                **{
                    PurePath(p): PathRecord(contents=None, mtime=t)
                    for p, t in dirs
                },
            },
        )

