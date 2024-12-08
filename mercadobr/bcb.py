import csv
import datetime
import io
import json
from calendar import monthrange
from dataclasses import dataclass
from decimal import Decimal

from .utils import create_session, parse_br_date, parse_date


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
        self._session = create_session()
        # Por algum motivo, o serviço REST "novoselic" não retorna resultados caso o cabeçalho `Accept` seja passado
        del self._session.headers["Accept"]

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
        response = self._session.get(url, params=params)
        return [Taxa(data=parse_br_date(row["data"]), valor=Decimal(row["valor"])) for row in response.json()]

    def _novoselic_csv_request(self, filtro: dict, ordenacao: list[dict]):
        response = self._session.post(
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
            raise ValueError("Data final precisa ser o último dia do mês")
        fator = 1
        for ano in range(data_inicial.year, data_final.year + 1):
            for taxa in self.por_mes(ano):
                if taxa.data_inicial >= data_inicial and taxa.data_final <= data_final:
                    fator *= taxa.valor
        fator = fator.quantize(Decimal("0.0000000000000001"))
        return (fator * valor).quantize(Decimal("0.01"))
