from ..project_utils import (
    project_instance,
)
from proj.config_file import (
    find_config_root,
    get_source_path,
    get_possible_spec_paths,
)
from proj.dtgen.find_outdated import (
    find_outdated,
)
from proj.config_file import (
    get_config,
)

def test_find_config_root():
    with project_instance('dtgen') as d:
        assert find_config_root(d) == d

def test_find_outdated():
    with project_instance('dtgen') as d:
        config = get_config(d)

        with (d / 'lib/person/include/person/out_of_date.dtg.hh').open('w') as _:
            pass

        with (d / 'lib/person/src/person/out_of_date2.dtg.cc').open('w') as _:
            pass

        found = set(find_outdated(d, config))
        correct = set([
            d / 'lib/person/include/person/out_of_date.dtg.hh',
            d / 'lib/person/src/person/out_of_date2.dtg.cc',
        ])
        assert found == correct

def test_get_source_path():
    with project_instance('dtgen') as d:
        correct = d / 'lib/person/src/person/color.dtg.cc'
        assert get_source_path(d / 'lib/person/include/person/color.dtg.hh') == correct

def test_get_possible_spec_paths():
    with project_instance('dtgen') as d:
        found = set(get_possible_spec_paths(d / 'lib/person/include/person/color.dtg.hh'))
        correct = set([
            d / 'lib/person/include/person/color.struct.toml',
            d / 'lib/person/include/person/color.enum.toml',
            d / 'lib/person/include/person/color.variant.toml',
            d / 'lib/person/src/person/color.struct.toml',
            d / 'lib/person/src/person/color.enum.toml',
            d / 'lib/person/src/person/color.variant.toml',
        ])
        assert found == correct


