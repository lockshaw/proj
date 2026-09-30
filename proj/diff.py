from .trees import (
    MoveTrace,
    MkDirTrace,
    RmFileTrace,
    CreateFileTrace,
    ModifyFileTrace,
)
from typing import (
    Sequence,
    Union,
)
from .utils import (
    nearest_common_ancestor,
)
import io
import textwrap

def render_path_diff(
    path_diff: Sequence[Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
    ]],
) -> str:
    return render_file_diff(path_diff)

def render_file_diff(
    file_diff: Sequence[Union[
        MoveTrace,
        MkDirTrace,
        RmFileTrace,
        CreateFileTrace,
        ModifyFileTrace,
    ]],
) -> str:
    f = io.StringIO()
    for trace_elem in file_diff:
        if isinstance(trace_elem, MoveTrace):
            ancestor = nearest_common_ancestor(trace_elem.src, trace_elem.dst)
            src_rel = trace_elem.src.relative_to(ancestor)
            dst_rel = trace_elem.dst.relative_to(ancestor)
            f.write(f'm {ancestor}/{{{src_rel} -> {dst_rel}}}\n')
        elif isinstance(trace_elem, MkDirTrace):
            f.write(f'c {trace_elem.path}/\n')
        elif isinstance(trace_elem, RmFileTrace):
            f.write(f'd {trace_elem.path}\n')
        elif isinstance(trace_elem, CreateFileTrace):
            f.write(f'c {trace_elem.path}\n' + textwrap.indent(trace_elem.contents, '  ') + '\n')
        elif isinstance(trace_elem, ModifyFileTrace):
            f.write(f'm {trace_elem.path}\n' + textwrap.indent(trace_elem.diff, '  ') + '\n')
    return f.getvalue()
