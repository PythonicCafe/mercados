import argparse
import sys

from mercados import b3, bcb, cvm, fundosnet, ibge, stn

_MODULES = {module.__name__.replace("mercados.", ""): module for module in (b3, bcb, cvm, fundosnet, ibge, stn)}


def _cria_parser():
    parser = argparse.ArgumentParser(prog="mercados", description="Coleta dados do mercado financeiro brasileiro")
    subparsers = parser.add_subparsers(dest="fonte", metavar="fonte", help="Fonte de dados", required=True)
    for name, module in _MODULES.items():
        subparser = subparsers.add_parser(name, help=module._DESCRICAO_CLI)
        module._configura_parser_cli(subparser)
    return parser


def main():
    parser = _cria_parser()
    args = parser.parse_args()
    fonte = args.fonte

    if fonte in _MODULES:
        module = _MODULES[fonte]
        sys.exit(module.main(args))
    else:
        sys.exit(100)


if __name__ == "__main__":
    main()
