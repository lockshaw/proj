from proj.dtgen.render_utils import (
    render_doxygen_docstring,
)

def test_render_doxygen_docstring():
    input = (
        'hello\n'
        'world'
    ).strip()

    correct = (
        '/**\n'
        ' * hello\n'
        ' * world\n'
        ' */'
    ).strip()

    assert render_doxygen_docstring(input) == correct
