from proj.__main__ import make_parser

def test_cli() -> None:
    p = make_parser()
    p.print_help()
