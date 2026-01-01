from io import BytesIO

from mercados.utils import USER_AGENT, create_session

_DESCRICAO_CLI = "Coleta valores históricos de índices"


class IBGE:
    _urls = {
        "IPCA": "https://ftp.ibge.gov.br/Precos_Indices_de_Precos_ao_Consumidor/IPCA/Serie_Historica/ipca_SerieHist.zip",
        "IPCA-15": "https://ftp.ibge.gov.br/Precos_Indices_de_Precos_ao_Consumidor/IPCA_15/Series_Historicas/ipca-15_SerieHist.zip",
        "INPC": "https://ftp.ibge.gov.br/Precos_Indices_de_Precos_ao_Consumidor/INPC/Serie_Historica/inpc_SerieHist.zip",
    }

    def __init__(self, user_agent: str = USER_AGENT, proxy: str | None = None, timeout: float = 15.0) -> None:
        self.session = create_session(user_agent=user_agent, proxy=proxy)
        self.timeout = timeout

    def _baixa_planilha_indice(self, url):
        # TODO: implementar cache
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.content

    def _extrai_planilha_indice(self, content: BytesIO):
        import datetime
        from decimal import Decimal
        from zipfile import ZipFile

        import xlrd

        from mercados.bcb import Taxa

        # TODO: adicionar cache
        # TODO: adicionar variação na taxa

        zf = ZipFile(BytesIO(content))
        assert len(zf.filelist) == 1, f"Número de arquivos dentro do ZIP ({len(zf.filelist)}) diferente do esperado (1)"
        file_info = zf.filelist[0]
        with zf.open(file_info.filename) as fobj:
            contents = fobj.read()
        workbook = xlrd.open_workbook_xls(file_contents=contents)
        sheet = workbook.sheet_by_index(0)
        meses = "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split()
        resultado = [Taxa(data=datetime.date(1993, 12, 15), valor=Decimal("100.00"))]
        ultimo_ano = None
        for row_number in range(sheet.nrows):
            row = [cell.value for cell in sheet.row(row_number)]
            ano, mes, valor = row[:3]
            if not mes or mes == "MÊS":
                continue
            if not ano:
                ano = ultimo_ano
            else:
                ano = int(ano)
                ultimo_ano = ano
            mes = meses.index(mes) + 1
            # TODO: quantize valor UM_CENTAVO
            resultado.append(Taxa(data=datetime.date(ano, mes, 15), valor=Decimal(str(valor))))

        return resultado

    def historico(self, indice):
        """
        Extrai os números-índices para um determinado índice, desde janeiro de 1994 (dez/1993 = 100)

        Os links para download dos ZIPs estão disponíveis nas páginas:
        - IPCA: <https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html?=&t=series-historicas>
        - IPCA-15: <https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9260-indice-nacional-de-precos-ao-consumidor-amplo-15.html?=&t=series-historicas>
        - INPC: <https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9258-indice-nacional-de-precos-ao-consumidor.html?=&t=series-historicas>
        """
        indice_normalizado = str(indice or "").strip().upper()
        if indice_normalizado not in self._urls:
            raise ValueError(f"Índice desconhecido: {repr(indice)}. Opções: {', '.join(sorted(self._urls.keys()))}")
        url = self._urls[indice_normalizado]
        zip_content = self._baixa_planilha_indice(url)
        return self._extrai_planilha_indice(zip_content)


def _configura_parser_cli(parser):
    from mercados.utils import EXPORT_FORMATS, extrai_nome_arquivo, parse_iso_date

    subparsers = parser.add_subparsers(dest="comando", metavar="comando", required=True)

    indice_choices = sorted(IBGE._urls.keys())
    subparser_historico = subparsers.add_parser("historico", help="Baixa histórico de diversos índices")
    subparser_historico.add_argument(
        "-i",
        "--inicio",
        "--data-inicial",
        metavar="data",
        type=parse_iso_date,
        help="Data de início no formato YYYY-MM-DD",
    )
    subparser_historico.add_argument(
        "-f",
        "--fim",
        "--data-final",
        metavar="data",
        type=parse_iso_date,
        help="Data de fim no formato YYYY-MM-DD",
    )
    subparser_historico.add_argument(
        "-F",
        "--formato",
        metavar="fmt",
        type=str,
        choices=EXPORT_FORMATS,
        default=None,
        help=f"Formato de saída. Opções: {', '.join(sorted(EXPORT_FORMATS))}",
    )
    subparser_historico.add_argument(
        "indice",
        choices=indice_choices,
        help=f"Índice. Opções: {', '.join(indice_choices)}",
    )
    subparser_historico.add_argument(
        "arquivo",
        nargs="?",
        type=extrai_nome_arquivo,
        help="Nome do arquivo a ser salvo",
    )


def main(args):
    import sys

    from mercados.utils import define_formato, dicts_to_file

    comando = args.comando
    ibge = IBGE()

    if comando == "historico":
        inicio = args.inicio
        fim = args.fim
        indice = args.indice
        arquivo = args.arquivo
        formato = args.formato
        fmt = define_formato(formato, arquivo)
        data = []
        for tx in ibge.historico(indice=indice):
            if (inicio is not None and tx.data < inicio) or (fim is not None and tx.data > fim):
                continue
            data.append(tx.serialize())

        if arquivo is None:
            dicts_to_file(data, fmt, sys.stdout)
        else:
            arquivo.parent.mkdir(exist_ok=True, parents=True)
            with arquivo.open(mode="w") as fobj:
                dicts_to_file(data, fmt, fobj)

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
