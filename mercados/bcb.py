import csv
import datetime
import io
import json
from calendar import monthrange
from dataclasses import asdict, dataclass
from decimal import Decimal

from .utils import create_session, dicts_to_str, parse_br_date


@dataclass
class TaxaIntervalo:
    data_inicial: datetime.date
    data_final: datetime.date
    valor: Decimal


@dataclass
class Taxa:
    data: datetime.date
    valor: Decimal


class BancoCentral:
    """Acessa séries temporais e sistema "novoselic" do Banco Central"""

    series = {
        "Selic diária": 11,
        "Selic meta diária": 432,
        "CDI": 12,
        "IPCA mensal": 433,  # Fonte: IBGE
        "IGP-M mensal": 189,  # Fonte: FGV
        "IGP-DI mensal": 190,  # Fonte: ANBIMA
    }
    # TODO: pegar outros IPCAs
    # TODO: IMA-B (12466?) - a fonte oficial é a ANBIMA, não seria melhor pegar diretamente de lá?
    # TODO: IMA-B 5 (12467?) - a fonte oficial é a ANBIMA, não seria melhor pegar diretamente de lá?
    # TODO: IMA-B 5+ (12468?) - a fonte oficial é a ANBIMA, não seria melhor pegar diretamente de lá?
    # TODO: IMA-S (12462?) - a fonte oficial é a ANBIMA, não seria melhor pegar diretamente de lá?
    # TODO: pegar URV (parou) de https://api.bcb.gov.br/dados/serie/bcdata.sgs.XX/dados?formato=json
    # TODO: pegar UFIR (parou) de https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=22
    # TODO: pegar outras das principais séries

    def __init__(self):
        self.session = create_session()
        # Por algum motivo, o serviço REST "novoselic" não retorna resultados caso o cabeçalho `Accept` seja passado
        del self.session.headers["Accept"]

    def serie_temporal(self, nome: str, inicio: datetime.date = None, fim: datetime.date = None) -> list[Taxa]:
        """
        Acessa API de séries temporais do Banco Central

        :param str nome: nome da série temporal a ser usada (ver lista na variável `series`)
        :param datetime.date inicio: (opcional) Data de início dos dados. Se não especificado, pegará desde o início da
        série (pode ser demorado).
        :param datetime.date fim: (opcional) Data de fim dos dados. Se não especificado, pegará até o final da série.
        """
        codigo = self.series.get(nome)
        if codigo is None:
            raise ValueError(f"Nome de série não encontrado: {repr(nome)}")
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
        params = {"formato": "json"}
        if inicio is not None:
            params["dataInicial"] = inicio.strftime("%d/%m/%Y")
        if fim is not None:
            params["dataFinal"] = fim.strftime("%d/%m/%Y")
        response = self.session.get(url, params=params)
        return [Taxa(data=parse_br_date(row["data"]), valor=Decimal(row["valor"])) for row in response.json()]

    def _novoselic_csv_request(self, filtro: dict, ordenacao: list[dict]):
        response = self.session.post(
            "https://www3.bcb.gov.br/novoselic/rest/fatoresAcumulados/pub/exportarCsv",
            data={"filtro": json.dumps(filtro), "parametrosOrdenacao": json.dumps(ordenacao)},
        )
        csv_fobj = io.StringIO(response.content.decode("utf-8-sig"))
        resultado = []
        for row in csv.DictReader(csv_fobj, delimiter=";"):
            periodo = row.pop("Taxa Selic - Fatores acumulados").lower()
            if periodo == "período":  # Header
                continue
            value_key = [key for key in row.keys() if key.lower().startswith("filtros aplicados")][0]
            resultado.append({"periodo": periodo, "valor": row[value_key]})
        return resultado

    def selic_por_mes(self, ano: int) -> list[TaxaIntervalo]:
        """Utiliza o sistema "novoselic" para pegar a variação mensal da Selic para um determinado ano"""
        ordenacao = [{"nome": "periodo", "decrescente": False}]
        filtro = {
            "campoPeriodo": "mensal",
            "dataInicial": "",
            "dataFinal": "",
            "ano": ano,
            "exibirMeses": True,
        }
        meses = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
        resultado = []
        for row in self._novoselic_csv_request(filtro, ordenacao):
            mes, ano = row["periodo"].lower().split(" / ")
            ano, mes = int(ano), meses.index(mes) + 1
            resultado.append(
                TaxaIntervalo(
                    data_inicial=datetime.date(ano, mes, 1),
                    data_final=datetime.date(ano, mes, monthrange(ano, mes)[1]),
                    valor=Decimal(row["valor"].replace(",", ".")),
                )
            )
        return resultado

    def selic_por_dia(self, data_inicial, data_final) -> TaxaIntervalo:
        """Utiliza o sistema "novoselic" para pegar a variação diária da Selic para um determinado ano"""
        filtro = {
            "campoPeriodo": "periodo",
            "dataInicial": data_inicial.strftime("%d/%m/%Y"),
            "dataFinal": data_final.strftime("%d/%m/%Y"),
        }
        ordenacao = [{"nome": "periodo", "decrescente": False}]
        row = list(self._novoselic_csv_request(filtro, ordenacao))[0]
        inicio, fim = row["periodo"].split(" a ")
        return TaxaIntervalo(
            data_inicial=datetime.datetime.strptime(inicio, "%d/%m/%Y").date(),
            data_final=datetime.datetime.strptime(fim, "%d/%m/%Y").date(),
            valor=Decimal(row["valor"].replace(",", ".")),
        )

    def ajustar_selic_por_dia(
        self, data_inicial: datetime.date, data_final: datetime.date, valor: int | float | Decimal
    ) -> Decimal:
        """Ajusta valor com base na Selic diária (vinda do sistema "novoselic")"""
        taxa = self.selic_por_dia(data_inicial, data_final)
        return (taxa.valor * valor).quantize(Decimal("0.01"))

    def ajustar_selic_por_mes(
        self, data_inicial: datetime.date, data_final: datetime.date, valor: int | float | Decimal
    ) -> Decimal:
        """Ajusta valor com base na Selic mensal (vinda do sistema "novoselic")"""
        if data_inicial.day != 1:
            raise ValueError("Data inicial precisa ser o primeiro dia do mês")
        elif data_final.day != monthrange(data_final.year, data_final.month)[1]:
            raise ValueError(
                f"Data final precisa ser o último dia do mês: {data_final} vs {monthrange(data_final.year, data_final.month)}"
            )
        fator = 1
        for ano in range(data_inicial.year, data_final.year + 1):
            for taxa in self.selic_por_mes(ano):
                if taxa.data_inicial >= data_inicial and taxa.data_final <= data_final:
                    fator *= taxa.valor
        fator = fator.quantize(Decimal("0.0000000000000001"))
        return (fator * valor).quantize(Decimal("0.01"))


if __name__ == "__main__":
    import argparse

    from .utils import parse_iso_date

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparser_ajustar_selic = subparsers.add_parser("ajustar-selic")
    subparser_ajustar_selic.add_argument("tipo_periodo", choices=["dia", "mês"])
    subparser_ajustar_selic.add_argument("data_inicial", type=parse_iso_date, help="Data de início")
    subparser_ajustar_selic.add_argument("data_final", type=parse_iso_date, help="Data de fim")
    subparser_ajustar_selic.add_argument("valor", type=Decimal, help="Valor a ser ajustado")

    subparser_serie_temporal = subparsers.add_parser("serie-temporal")
    subparser_serie_temporal.add_argument("--data-inicial", "-i", type=parse_iso_date, help="Data de início (opcional)")
    subparser_serie_temporal.add_argument("--data-final", "-f", type=parse_iso_date, help="Data de fim (opcional)")
    subparser_serie_temporal.add_argument(
        "--formato",
        "-F",
        type=str,
        choices=["csv", "tsv", "md", "markdown", "txt"],
        default="txt",
        help="Formato de saída",
    )
    subparser_serie_temporal.add_argument(
        "serie",
        choices=list(BancoCentral.series.keys()),
        help="Nome da série temporal",
    )

    args = parser.parse_args()
    bc = BancoCentral()

    if args.command == "ajustar-selic":
        tipo = args.tipo_periodo
        inicio = args.data_inicial
        fim = args.data_final
        valor = args.valor

        if tipo == "dia":
            ajustado = bc.ajustar_selic_por_dia(data_inicial=inicio, data_final=fim, valor=valor)
        elif tipo == "mês":
            ajustado = bc.ajustar_selic_por_mes(data_inicial=inicio, data_final=fim, valor=valor)
        print(ajustado)

    elif args.command == "serie-temporal":
        inicio = args.data_inicial
        fim = args.data_final
        nome_serie = args.serie
        fmt = args.formato
        data = [asdict(tx) for tx in bc.serie_temporal(nome_serie, inicio=inicio, fim=fim)]
        print(dicts_to_str(data, fmt))
