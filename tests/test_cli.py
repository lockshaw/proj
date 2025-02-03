from proj.__main__ import make_parser

def test_cli():
    p = make_parser()
    p.print_help()
