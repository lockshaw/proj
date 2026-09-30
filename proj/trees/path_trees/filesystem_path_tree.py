from pathlib import PurePath, Path
from dataclasses import dataclass
from typing import (
    Iterator,
    TYPE_CHECKING,
)
from ..path_tree import MutablePathTree
import os
import copy

if TYPE_CHECKING:
    from typing import Self
    from proj.paths import AbsolutePath

@dataclass(eq=True)
class FilesystemPathTree(MutablePathTree):
    _root: 'AbsolutePath'

    def has_path(self, p: PurePath) -> bool:
        return (self._root / p).raw.exists()

    def has_dir(self, p: PurePath) -> bool:
        return (self._root / p).raw.is_dir()

    def has_file(self, p: PurePath) -> bool:
        return (self._root / p) .raw.is_file()

    def mkdir(
        self,
        p: PurePath,
        exist_ok: bool = False,
        parents: bool = False,
    ) -> None:
        Path(self._root.raw / p).mkdir(exist_ok=exist_ok, parents=parents)

    def rm_file(self, p: PurePath) -> None:
        assert self.has_file(p)
        Path(self._root.raw / p).unlink()

    def with_extension(self, extension: str) -> Iterator[PurePath]:
        assert extension.startswith('.')

        def has_extension(p: PurePath) -> bool:
            return p.name.endswith(extension)

        yield from filter(has_extension, self.files())

    def ls_dir(self, p: PurePath) -> Iterator[PurePath]:
        yield from [
            _p.relative_to(self._root.raw) for _p in Path(self._root.raw / p).iterdir()
        ]

    def rename(self, src: PurePath, dst: PurePath) -> None:
        assert self.has_path(src)
        assert self.has_dir(dst.parent)
        assert not self.has_path(dst)
        Path(self._root.raw / src).rename(self._root.raw / dst)

    def restrict_to_subdir(self, p: PurePath) -> 'Self':
        assert self.has_dir(p)
        result = copy.deepcopy(self)
        result._root = self._root / p
        return result

    def files(self) -> Iterator[PurePath]:
        base = self._root.raw

        for (dirpath, dirnames, filenames) in os.walk(base):
            _dirpath = PurePath(dirpath).relative_to(base)
            for fname in filenames:
                yield (_dirpath / fname)

    def dirs(self) -> Iterator[PurePath]:
        base = self._root.raw

        for (dirpath, dirnames, filenames) in os.walk(base):
            _dirpath = PurePath(dirpath).relative_to(base)
            for dirname in dirnames:
                yield (_dirpath / dirname)
