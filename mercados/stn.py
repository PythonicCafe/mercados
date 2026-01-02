import csv
import datetime
import io
from dataclasses import dataclass
from decimal import Decimal

from mercados.utils import USER_AGENT, create_session, parse_br_decimal, parse_date

_DESCRICAO_CLI = "Coleta preços históricos dos títutlos do Tesouro Direto"


@dataclass
class TituloRendaFixa:
    data: datetime.date
    nome: str
    indexador: str
    vencimento: datetime.date
    taxa_compra: Decimal
    taxa_venda: Decimal
    preco: Decimal
    preco_compra: Decimal
    preco_venda: Decimal

    @classmethod
    def from_dict(cls, row):
        nome = row.pop("Tipo Titulo")
        indexador = None
        if nome == "Tesouro Selic":
            indexador = "Selic"
        elif nome.startswith("Tesouro Prefixado"):
            indexador = "Pré-fixado"
        elif nome.startswith("Tesouro IGPM+"):
            indexador = "IGPM"
        elif nome.startswith("Tesouro IPCA+") or nome.startswith("Tesouro Renda+") or nome.startswith("Tesouro Educa+"):
            indexador = "IPCA"
        else:
            raise ValueError("Título com indexador desconhecido: {repr(nome)}")
        obj = cls(
            nome=nome,
            indexador=indexador,
            vencimento=parse_date("br-date", row.pop("Data Vencimento")),
            data=parse_date("br-date", row.pop("Data Base")),
            taxa_compra=parse_br_decimal(row.pop("Taxa Compra Manha")),
            taxa_venda=parse_br_decimal(row.pop("Taxa Venda Manha")),
            preco_compra=parse_br_decimal(row.pop("PU Compra Manha")),
            preco_venda=parse_br_decimal(row.pop("PU Venda Manha")),
            preco=parse_br_decimal(row.pop("PU Base Manha")),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data": self.data,
            "nome": self.nome,
            "indexador": self.indexador,
            "vencimento": self.vencimento,
            "taxa_compra": self.taxa_compra,
            "taxa_venda": self.taxa_venda,
            "preco": self.preco,
            "preco_compra": self.preco_compra,
            "preco_venda": self.preco_venda,
        }


class Tesouro:
    def __init__(self, user_agent: str = USER_AGENT, proxy: str | None = None, timeout: float = 15.0) -> None:
        self.session = create_session(user_agent=user_agent, proxy=proxy)
        self.timeout = timeout

    def historico_titulos(self):
        """
        Baixa histórico de preços de títulos diários do Tesouro

        Como a planilha é relativamente grande e demora um tempo para baixar, o recomendável é salvar os dados em
        cache.
        """
        url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"

        response = self.session.get(url, timeout=self.timeout)
        csv_data = response.content.decode(response.apparent_encoding)
        dados = [TituloRendaFixa.from_dict(row) for row in csv.DictReader(io.StringIO(csv_data), delimiter=";")]
        dados.sort(key=lambda obj: (obj.data, obj.vencimento.year, obj.nome), reverse=True)
        return dados


def _configura_parser_cli(parser):
    from mercados.utils import EXPORT_FORMATS, extrai_nome_arquivo, parse_iso_date

    subparsers = parser.add_subparsers(dest="comando", metavar="comando", required=True)
    parser_titulos = subparsers.add_parser("titulos", help=_DESCRICAO_CLI)
    parser_titulos.add_argument(
        "-I",
        "--indexador",
        metavar="nome",
        type=str,
        help="Filtra pelo indexador do título",
    )
    parser_titulos.add_argument(
        "-i",
        "--inicio",
        "--data-inicial",
        metavar="data",
        type=parse_iso_date,
        help="Data de corte inicial no formato YYYY-MM-DD",
    )
    parser_titulos.add_argument(
        "-f",
        "--fim",
        "--data-final",
        metavar="data",
        type=parse_iso_date,
        help="Data de corte final no formato YYYY-MM-DD",
    )
    parser_titulos.add_argument(
        "-F",
        "--formato",
        type=str,
        metavar="fmt",
        choices=EXPORT_FORMATS,
        default=None,
        help=f"Formato de saída. Opções: {', '.join(sorted(EXPORT_FORMATS))}",
    )
    parser_titulos.add_argument(
        "-n",
        "--nome",
        dest="nomes",
        metavar="nome1 -n nome2 ...",
        action="append",
        help="Filtra pelo nome do título. Pode ser especificado várias vezes.",
    )
    parser_titulos.add_argument(
        "arquivo",
        nargs="?",
        type=extrai_nome_arquivo,
        help="Nome do arquivo a ser salvo",
    )


def main(args):
    import sys

    from mercados.utils import define_formato, dicts_to_file

    comando = args.comando

    if comando == "titulos":
        arquivo = args.arquivo
        fim = args.fim
        formato = args.formato
        inicio = args.inicio
        nomes = args.nomes
        indexador = args.indexador
        fmt = define_formato(formato, arquivo)
        dados = []
        tesouro = Tesouro()
        for registro in tesouro.historico_titulos():
            if (
                (inicio is not None and registro.data < inicio)
                or (fim is not None and registro.data >= fim)
                or (nomes and registro.nome not in nomes)
                or (indexador is not None and registro.indexador != indexador)
            ):
                continue
            dados.append(registro.serialize())
        if arquivo is None:
            dicts_to_file(dados, fmt, sys.stdout)
        else:
            arquivo.parent.mkdir(exist_ok=True, parents=True)
            with arquivo.open(mode="w") as fobj:
                dicts_to_file(dados, fmt, fobj)

    else:
        return 100
    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=_DESCRICAO_CLI)
    _configura_parser_cli(parser)
    args = parser.parse_args()
    sys.exit(main(args))
