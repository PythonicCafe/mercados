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

    def serialize(self):
        return asdict(self)


@dataclass
class Taxa:
    data: datetime.date
    valor: Decimal

    def serialize(self):
        return asdict(self)


class BancoCentral:
    """Acessa séries temporais e sistema "novoselic" do Banco Central"""

    # TODO: adicionar unidade de medida
    # TODO: talvez já converter (/ 100) as que são variação percentual
    series = {
        # Juros
        "Selic": 11,  # Frequência: diária. Fonte: BCB-Demab
        "Selic meta": 432,  # Frequência: diária. Fonte: Copom
        "CDI": 12,  # Frequência: diária. Fonte: Cetip
        "Taxa Referencial": 226,  # Frequência: diária. Fonte: BCB-Demab
        "TR": 226,  # Frequência: diária. Fonte: BCB-Demab
        "Taxa básica financeira": 253,  # Frequência: diária. Fonte: BCB-Demab
        "TBF": 253,  # Frequência: diária. Fonte: BCB-Demab
        # Inflação
        "IPCA": 433,  # Frequência: mensal. Fonte: IBGE
        "Fator IPCA": 29542,  # Frequência: mensal. Fonte: BCB-Demab
        "IPCA-15": 7478,  # Frequência: mensal. Fonte: IBGE
        "IPCA-E": 10764,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Alimentação e bebidas": 1635,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Habitação": 1636,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Artigos de residência": 1637,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Vestuário": 1638,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Transportes": 1639,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Comunicação": 1640,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Saúde e cuidados pessoais": 1641,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Despesas pessoais": 1642,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Educação": 1643,  # Frequência: mensal. Fonte: IBGE
        "IPCA - Comercializáveis": 4447,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Não comercializáveis": 4448,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Administrados": 4449,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo médias aparadas com suavização": 4466,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Bens não-duráveis": 10841,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Bens semi-duráveis": 10842,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Duráveis": 10843,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Serviços": 10844,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo médias aparadas sem suavização": 11426,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo por exclusão - EX0": 11427,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Itens livres": 11428,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Alimentação no domicílio": 27864,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Industriais": 27863,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo Ex-alimentação e energia (EXFE)": 28751,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo Percentil 55": 28750,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo de dupla ponderação": 16122,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo por exclusão - EX1": 16121,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo por exclusão - EX2": 27838,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Núcleo por exclusão - EX3": 27839,  # Frequência: mensal. Fonte: BCB-Depec
        "IPCA - Índice de difusão": 21379,  # Frequência: mensal. Fonte: BCB-Depec
        "IGP-M": 189,  # Frequência: mensal. Fonte: FGV
        "IGP-DI": 190,  # Frequência: mensal. Fonte: ANBIMA
        # Moedas
        "Dólar venda": 1,  # Frequência: diária. Fonte: Sisbacen PTAX800
        "Dólar compra": 10813,  # Frequência: diária. Fonte: Sisbacen PTAX800
        "USD venda": 1,  # Frequência: diária. Fonte: Sisbacen PTAX800
        "USD compra": 10813,  # Frequência: diária. Fonte: Sisbacen PTAX800
        "Euro venda": 21619,  # Frequência: diária. Fonte: PTAX
        "Euro compra": 21620,  # Frequência: diária. Fonte: PTAX
        "EUR venda": 21619,  # Frequência: diária. Fonte: PTAX
        "EUR compra": 21620,  # Frequência: diária. Fonte: PTAX
        "Iene venda": 21621,  # Frequência: diária. Fonte: PTAX
        "Iene compra": 21622,  # Frequência: diária. Fonte: PTAX
        "JPY venda": 21621,  # Frequência: diária. Fonte: PTAX
        "JPY compra": 21622,  # Frequência: diária. Fonte: PTAX
        "Libra Esterlina venda": 21623,  # Frequência: diária. Fonte: PTAX
        "Libra Esterlina compra": 21624,  # Frequência: diária. Fonte: PTAX
        "GBP venda": 21623,  # Frequência: diária. Fonte: PTAX
        "GBP compra": 21624,  # Frequência: diária. Fonte: PTAX
        "Franco Suíço venda": 21625,  # Frequência: diária. Fonte: PTAX
        "Franco Suíço compra": 21626,  # Frequência: diária. Fonte: PTAX
        "CHF venda": 21625,  # Frequência: diária. Fonte: PTAX
        "CHF compra": 21626,  # Frequência: diária. Fonte: PTAX
        "Coroa Dinamarquesa venda": 21627,  # Frequência: diária. Fonte: PTAX
        "Coroa Dinamarquesa compra": 21628,  # Frequência: diária. Fonte: PTAX
        "DKK venda": 21627,  # Frequência: diária. Fonte: PTAX
        "DKK compra": 21628,  # Frequência: diária. Fonte: PTAX
        "Coroa Norueguesa venda": 21629,  # Frequência: diária. Fonte: PTAX
        "Coroa Norueguesa compra": 21630,  # Frequência: diária. Fonte: PTAX
        "NOK venda": 21629,  # Frequência: diária. Fonte: PTAX
        "NOK compra": 21630,  # Frequência: diária. Fonte: PTAX
        "Coroa Sueca venda": 21631,  # Frequência: diária. Fonte: PTAX
        "Coroa Sueca compra": 21632,  # Frequência: diária. Fonte: PTAX
        "SEK venda": 21631,  # Frequência: diária. Fonte: PTAX
        "SEK compra": 21632,  # Frequência: diária. Fonte: PTAX
        "Dólar Australiano venda": 21633,  # Frequência: diária. Fonte: PTAX
        "Dólar Australiano compra": 21634,  # Frequência: diária. Fonte: PTAX
        "AUD venda": 21633,  # Frequência: diária. Fonte: PTAX
        "AUD compra": 21634,  # Frequência: diária. Fonte: PTAX
        "Dólar Canadense venda": 21635,  # Frequência: diária. Fonte: PTAX
        "Dólar Canadense compra": 21636,  # Frequência: diária. Fonte: PTAX
        "CAD venda": 21635,  # Frequência: diária. Fonte: PTAX
        "CAD compra": 21636,  # Frequência: diária. Fonte: PTAX
        # Outras
        "Saldo de depósitos de poupança": 239,  # Frequência: diário. Fonte: Sisbacen PESP300
        "Reservas internacionais": 13621,  # Frequência: diária. Fonte: BCB-DSTAT
    }
    # XXX: algumas séries pararam de ser atualizadas e por isso não foram adicionadas, como:
    #      "Bovespa - índice" (código 7)
    #      "Dow Jones NYSE - índice" (código 7809)
    #      "Nasdaq - índice" (código 7810)
    #      "IPCA - Transportes e comunicação" (código 1655)

    # TODO: pegar índices IMA-X diretamente da Anbima (não estão mais sendo atualizados no SGS)
    # TODO: pegar URV (parou) de https://api.bcb.gov.br/dados/serie/bcdata.sgs.XX/dados?formato=json
    # TODO: pegar UFIR (parou) de https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=22
    # TODO: pegar outras das principais séries

    def __init__(self):
        self.session = create_session()
        # Por algum motivo, o serviço REST "novoselic" não retorna resultados caso o cabeçalho `Accept` seja passado
        del self.session.headers["Accept"]

    def serie_temporal(
        self, nome_ou_codigo: str | int, inicio: datetime.date = None, fim: datetime.date = None
    ) -> list[Taxa]:
        """
        Acessa API de séries temporais do Banco Central

        :param str | int nome_ou_codigo: nome da série temporal a ser usada (ver lista na variável `series`) ou código
        usado pelo SGS.
        :param datetime.date inicio: (opcional) Data de início dos dados. Se não especificado, pegará desde o início da
        série (pode ser demorado).
        :param datetime.date fim: (opcional) Data de fim dos dados. Se não especificado, pegará até o final da série.
        """
        if isinstance(nome_ou_codigo, str):
            codigo = self.series.get(nome_ou_codigo)
            if codigo is None:
                raise ValueError(f"Nome de série não encontrado: {repr(nome_ou_codigo)}")
        else:
            codigo = nome_ou_codigo
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
