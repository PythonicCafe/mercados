import argparse
import sys

from mercados import b3, bcb, cvm, ibge, fundosnet


parser = argparse.ArgumentParser(prog="mercados", description="Coleta dados do mercado financeiro brasileiro")
subparsers = parser.add_subparsers(dest="fonte", metavar="fonte", help="Fonte de dados", required=True)
parser_b3 = subparsers.add_parser("b3", help=b3._DESCRICAO_CLI)
b3._configura_parser_cli(parser_b3)
parser_bcb = subparsers.add_parser("bcb", help=bcb._DESCRICAO_CLI)
bcb._configura_parser_cli(parser_bcb)
parser_cvm = subparsers.add_parser("cvm", help=cvm._DESCRICAO_CLI)
cvm._configura_parser_cli(parser_cvm)
parser_ibge = subparsers.add_parser("ibge", help=ibge._DESCRICAO_CLI)
ibge._configura_parser_cli(parser_ibge)
parser_fundosnet = subparsers.add_parser("fundosnet", help=fundosnet._DESCRICAO_CLI)
fundosnet._configura_parser_cli(parser_fundosnet)
args = parser.parse_args()
fonte = args.fonte

if fonte == "b3":
    sys.exit(b3.main(args))
elif fonte == "bcb":
    sys.exit(bcb.main(args))
elif fonte == "cvm":
    sys.exit(cvm.main(args))
elif fonte == "ibge":
    sys.exit(ibge.main(args))
elif fonte == "fundosnet":
    sys.exit(fundosnet.main(args))
else:
    sys.exit(100)
