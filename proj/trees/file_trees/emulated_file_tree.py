from pathlib import PurePath
from ..file_tree import MutableFileTree
from dataclasses import dataclass
from typing import (
    Dict,
    Optional,
    Mapping,
    Iterator,
    Iterable,
    Tuple,
    Union,
)
from proj.utils import is_relative_to

@dataclass(eq=True)
class EmulatedFileTree(MutableFileTree):
    _m: Dict[PurePath, Optional[str]]

    def has_path(self, p: PurePath) -> bool:
        return p in self._m

    def has_dir(self, p: PurePath) -> bool:
        if not self.has_path(p):
            return False
        return self._m[p] is None

    def has_file(self, p: PurePath) -> bool:
        if not self.has_path(p):
            return False
        return self._m[p] is not None

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
        self._m[p] = None

    def get_file_contents(
        self,
        p: PurePath
    ) -> str:
        assert self.has_file(p)
        contents = self._m[p]
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
        self._m[p] = contents

    def restrict_to_subdir(self, p: PurePath) -> 'EmulatedFileTree':
        assert self.has_dir(p)
        return EmulatedFileTree(
            {
                k.relative_to(p): v for k, v in self._m.items()
                if is_relative_to(k, p)
            },
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

    def rm_file(self, p: PurePath) -> None:
        assert self.has_file(p)
        del self._m[p]

    @staticmethod
    def from_map(m: Mapping[PurePath, Optional[str]]) -> 'EmulatedFileTree':
        expanded: Dict[PurePath, Optional[str]] = {}
        for p, contents in m.items():
            for parent in p.parents:
                if parent in expanded:
                    assert expanded[parent] is None
                else:
                    expanded[parent] = None
            expanded[p] = contents
        return EmulatedFileTree(expanded)

    @staticmethod
    def from_lists(
        files: Iterable[Tuple[Union[str, PurePath], str]],
        dirs: Iterable[Union[str, PurePath]],
    ) -> 'EmulatedFileTree':
        return EmulatedFileTree.from_map(
            {
                **{
                    PurePath(p): c
                    for p, c in files
                },
                **{
                    PurePath(p): None
                    for p in dirs
                },
            },
        )
