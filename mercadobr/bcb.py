import csv
import datetime
import decimal
import io
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from calendar import monthrange
from dataclasses import dataclass


@dataclass
class Taxa:
    data_inicial: datetime.date
    data_final: datetime.date
    valor: decimal.Decimal


class BancoCentral:
    MESES = "jan feb mar apr may jun jul aug sep oct nov dec".split()
    url = "https://www3.bcb.gov.br/novoselic/rest/fatoresAcumulados/pub/exportarCsv"

    def _deserialize(self, value):
        # TODO: quantize?
        return decimal.Decimal(value.replace(",", "."))

    def _csv_request(self, filtro, ordenacao):
        data = urlencode({
            "filtro": json.dumps(filtro),
            "parametrosOrdenacao": json.dumps(ordenacao),
        })
        request =  Request(self.url, data=data.encode())
        response = urlopen(request)
        csv_fobj = io.StringIO(response.read().decode("utf-8-sig"))
        for row in csv.DictReader(csv_fobj, delimiter=";"):
            periodo = row.pop("Taxa Selic - Fatores acumulados").lower()
            if periodo == "período":  # Header
                continue
            value_key = [key for key in row.keys() if key.lower().startswith("filtros aplicados")][0]
            yield {"periodo": periodo, "valor": row[value_key]}

    def selic_por_mes(self, ano):
        ordenacao = [{"nome": "periodo", "decrescente": False}]
        filtro = {
            "campoPeriodo": "mensal",
            "dataInicial": "",
            "dataFinal": "",
            "ano": ano,
            "exibirMeses": True,
        }
        for row in self._csv_request(filtro, ordenacao):
            mes, ano = row["periodo"].lower().split(" / ")
            ano, mes = int(ano), self.MESES.index(mes) + 1
            yield Taxa(
                data_inicial=datetime.date(ano, mes, 1),
                data_final=datetime.date(ano, mes, monthrange(ano, mes)[1]),
                valor=self._deserialize(row["valor"]),
            )

    def selic_por_dia(self, data_inicial, data_final):
        filtro = {
            "campoPeriodo": "periodo",
            "dataInicial": data_inicial.strftime("%d/%m/%Y"),
            "dataFinal": data_final.strftime("%d/%m/%Y"),
        }
        ordenacao = [{"nome": "periodo", "decrescente": False}]
        row = list(self._csv_request(filtro, ordenacao))[0]
        inicio, fim = row["periodo"].split(" a ")
        return Taxa(
            data_inicial=datetime.datetime.strptime(inicio, "%d/%m/%Y").date(),
            data_final=datetime.datetime.strptime(fim, "%d/%m/%Y").date(),
            valor=self._deserialize(row["valor"]),
        )

    def ajustar_selic_por_dia(self, data_inicial, data_final, valor):
        taxa = self.por_dia(data_inicial, data_final)
        return (taxa.valor * valor).quantize(decimal.Decimal("0.01"))

    def ajustar_selic_por_mes(self, data_inicial, data_final, valor):
        if data_inicial.day != 1:
            raise ValueError("Data inicial precisa ser o primeiro dia do mês")
        elif data_final.day != monthrange(data_final.year, data_final.month)[1]:
            raise ValueError("Data final precisa ser o último dia do mês")
        fator = 1
        for ano in range(data_inicial.year, data_final.year + 1):
            for taxa in self.por_mes(ano):
                if taxa.data_inicial >= data_inicial and taxa.data_final <= data_final:
                    fator *= taxa.valor
        fator = fator.quantize(decimal.Decimal('0.0000000000000001'))
        return (fator * valor).quantize(decimal.Decimal("0.01"))
