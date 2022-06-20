import datetime
import re
import time
from collections import OrderedDict
from functools import cached_property
from urllib.parse import urljoin

import requests
import rows
from lxml.html import document_fromstring
from rows.utils.download import Downloader, Download


REGEXP_CSRF_TOKEN = re.compile("""csrf_token ?= ?["']([^"']+)["']""")
CATEGORIES = {
    "Todos": 0,
    "Aditamento de Termo de Securitização": 19,
    "Assembleia": 2,
    "Atos de Deliberação do Administrador": 11,
    "Averbação ou Registro do Termo de Securitização": 18,
    "Aviso aos Cotistas": 4,
    "Aviso aos Cotistas - Estruturado": 14,
    "Aviso aos Investidores": 20,
    "Comunicado ao Mercado": 3,
    "Documentos de Oferta de Distribuição Pública": 16,
    "Fato Relevante": 1,
    "Informações para Registro de Oferta de CRA": 21,
    "Informações para Registro de Oferta de CRI": 22,
    "Informações para Registro Provisório de Oferta de CRI": 23,
    "Informes Periódicos": 6,
    "Laudo de Avaliação (Conclusão de Negócio)": 13,
    "Listagem e  Admissão à  Negociação  de Cotas": 24,
    "Oferta Pública de Aquisição de Cotas": 12,
    "Oferta Pública de Distribuição de Cotas": 8,
    "Outras Informações": 10,
    "Políticas de Governança Corporativa": 9,
    "Regulamento": 5,
    "Regulamento de Emissores B3": 15,
    "Relatórios": 7,
    "Termo de Securitização": 17,
}
FUND_TYPES = {
    "Todos": "",
    "ETF": 3,
    "ETF RF": 4,
    "FIDC": 2,
    "Fundo Imobiliário": 1,
    "Fundo Setorial": 7,
}
TYPES_BY_CATEGORY = {  # TODO: simplify structure
 0: [],
 19: [],
 2: [{'id': 1,
   'descricao': 'AGO',
   'situacao': True,
   'templateDocumento': None},
  {'id': 2, 'descricao': 'AGO/E', 'situacao': True, 'templateDocumento': None},
  {'id': 3, 'descricao': 'AGE', 'situacao': True, 'templateDocumento': None}],
 11: [{'id': 31,
   'descricao': 'Instrumento Particular de Constituição/Encerramento do Fundo',
   'situacao': True,
   'templateDocumento': None},
  {'id': 32,
   'descricao': 'Instrumento Particular de Alteração do Regulamento',
   'situacao': True,
   'templateDocumento': None},
  {'id': 46,
   'descricao': 'Instrumento Particular de Emissão de Cotas',
   'situacao': True,
   'templateDocumento': None}],
 18: [],
 4: [],
 14: [{'id': 41,
   'descricao': 'Rendimentos e Amortizações',
   'situacao': True,
   'templateDocumento': None}],
 20: [],
 3: [{'id': 49,
   'descricao': 'Outros Comunicados Não Considerados Fatos Relevantes',
   'situacao': True,
   'templateDocumento': None},
  {'id': 50,
   'descricao': 'Esclarecimentos de consulta B3 / CVM',
   'situacao': True,
   'templateDocumento': None}],
 16: [{'id': 72,
   'descricao': 'Anúncio de Encerramento de Distribuição Pública',
   'situacao': True,
   'templateDocumento': None},
  {'id': 74,
   'descricao': 'Anúncio de Início de Distribuição Pública',
   'situacao': True,
   'templateDocumento': None},
  {'id': 75,
   'descricao': 'Aviso ao Mercado',
   'situacao': True,
   'templateDocumento': None},
  {'id': 76,
   'descricao': 'Comunicação de Modificação de Oferta',
   'situacao': True,
   'templateDocumento': None},
  {'id': 78,
   'descricao': 'Comunicado de Encerramento de Oferta com Esforços Restritos',
   'situacao': True,
   'templateDocumento': None},
  {'id': 80,
   'descricao': 'Comunicado de Início de Oferta com Esforços Restritos',
   'situacao': True,
   'templateDocumento': None},
  {'id': 82,
   'descricao': 'Prospecto de Distribuição Pública',
   'situacao': True,
   'templateDocumento': None},
  {'id': 103,
   'descricao': 'Formulário de Liberação para Negociação das Cotas',
   'situacao': True,
   'templateDocumento': None}],
 1: [],
 21: [{'id': 83,
   'descricao': 'ANEXO "11 - I" CVM 600/18',
   'situacao': True,
   'templateDocumento': None}],
 22: [{'id': 84,
   'descricao': 'Anexo I - ICVM 414/04',
   'situacao': True,
   'templateDocumento': None}],
 23: [{'id': 85,
   'descricao': 'Anexo II - ICVM 414/04',
   'situacao': True,
   'templateDocumento': None}],
 6: [{'id': 4,
   'descricao': 'Informe Mensal',
   'situacao': True,
   'templateDocumento': None},
  {'id': 5,
   'descricao': 'Informe Trimestral',
   'situacao': True,
   'templateDocumento': None},
  {'id': 6,
   'descricao': 'Informe Anual',
   'situacao': True,
   'templateDocumento': None},
  {'id': 7,
   'descricao': 'Relatório do Representante de Cotistas',
   'situacao': True,
   'templateDocumento': None},
  {'id': 8,
   'descricao': 'Informe Semestral - DFC e Relatório do Administrador',
   'situacao': True,
   'templateDocumento': None},
  {'id': 30,
   'descricao': 'Demonstrações Financeiras',
   'situacao': True,
   'templateDocumento': None},
  {'id': 33,
   'descricao': 'Relação das demandas judiciais ou extrajudiciais',
   'situacao': True,
   'templateDocumento': None},
  {'id': 40,
   'descricao': 'Informe Mensal Estruturado',
   'situacao': True,
   'templateDocumento': None},
  {'id': 45,
   'descricao': 'Informe Trimestral Estruturado',
   'situacao': True,
   'templateDocumento': None},
  {'id': 47,
   'descricao': 'Informe Anual Estruturado',
   'situacao': True,
   'templateDocumento': None},
  {'id': 51,
   'descricao': 'Demonstração Financeira de Encerramento',
   'situacao': True,
   'templateDocumento': None},
  {'id': 52,
   'descricao': 'Relatório Anual',
   'situacao': True,
   'templateDocumento': None},
  {'id': 63,
   'descricao': 'Composição da Carteira (CDA)',
   'situacao': True,
   'templateDocumento': None},
  {'id': 64,
   'descricao': 'Informe Diário',
   'situacao': True,
   'templateDocumento': None},
  {'id': 65,
   'descricao': 'Balancete',
   'situacao': True,
   'templateDocumento': None},
  {'id': 81,
   'descricao': 'Informe Mensal de CRA (Anexo "37" ICVM 600/18)',
   'situacao': True,
   'templateDocumento': None},
  {'id': 86,
   'descricao': 'Informe Mensal de CRI (Anexo 32, II ICVM 480)',
   'situacao': True,
   'templateDocumento': None},
  {'id': 91,
   'descricao': 'Demonstrações Financeiras do Devedor ou Coobrigado',
   'situacao': True,
   'templateDocumento': None}],
 13: [],
 24: [{'id': 92,
   'descricao': 'Protocolo Inicial',
   'situacao': True,
   'templateDocumento': None},
  {'id': 93,
   'descricao': 'Protocolo para Cumprimento de Exigências',
   'situacao': True,
   'templateDocumento': None},
  {'id': 94,
   'descricao': 'Protocolo para Pedido de Prorrogação/Interrupção',
   'situacao': True,
   'templateDocumento': None}],
 12: [{'id': 34,
   'descricao': 'Edital de Oferta Pública de Aquisição de Cotas',
   'situacao': True,
   'templateDocumento': None},
  {'id': 35,
   'descricao': 'Laudo de Avaliação',
   'situacao': True,
   'templateDocumento': None},
  {'id': 37,
   'descricao': 'Manifestação do Administrador / Gestor',
   'situacao': True,
   'templateDocumento': None},
  {'id': 38,
   'descricao': 'Edital de Oferta Pública de Aquisição de Cotas - Concorrente',
   'situacao': True,
   'templateDocumento': None}],
 8: [{'id': 13,
   'descricao': 'Prospecto',
   'situacao': True,
   'templateDocumento': None},
  {'id': 14,
   'descricao': 'Anúncio de Início',
   'situacao': True,
   'templateDocumento': None},
  {'id': 15,
   'descricao': 'Aviso ao Mercado',
   'situacao': True,
   'templateDocumento': None},
  {'id': 16,
   'descricao': 'Anúncio de Encerramento',
   'situacao': True,
   'templateDocumento': None},
  {'id': 17,
   'descricao': 'Restritos - ICVM 476',
   'situacao': True,
   'templateDocumento': None},
  {'id': 18,
   'descricao': 'Aviso de Modificação de Oferta',
   'situacao': True,
   'templateDocumento': None},
  {'id': 19,
   'descricao': 'Outros Documentos',
   'situacao': True,
   'templateDocumento': None},
  {'id': 53,
   'descricao': 'Material de Divulgação',
   'situacao': True,
   'templateDocumento': None},
  {'id': 90,
   'descricao': 'Anexo 39-V (art. 10 §1º, inciso I da ICVM 472)',
   'situacao': True,
   'templateDocumento': None},
  {'id': 98,
   'descricao': 'Formulário de Subscrição de Cotas (Estruturado)',
   'situacao': True,
   'templateDocumento': None},
  {'id': 100,
   'descricao': 'Formulário de Liberação para Negociação das Cotas',
   'situacao': True,
   'templateDocumento': None}],
 10: [{'id': 26,
   'descricao': 'Perfil do Fundo',
   'situacao': True,
   'templateDocumento': None},
  {'id': 27,
   'descricao': 'Rentabilidade',
   'situacao': True,
   'templateDocumento': None},
  {'id': 29,
   'descricao': 'Outros Documentos',
   'situacao': True,
   'templateDocumento': None},
  {'id': 101,
   'descricao': 'Perfil do Fundo (Estruturado)',
   'situacao': True,
   'templateDocumento': None}],
 9: [{'id': 20,
   'descricao': 'Divulgação de Fato Relevante',
   'situacao': True,
   'templateDocumento': None},
  {'id': 21,
   'descricao': 'Negociação de Cotas',
   'situacao': True,
   'templateDocumento': None},
  {'id': 22,
   'descricao': 'Participação em Assembleia',
   'situacao': True,
   'templateDocumento': None},
  {'id': 23,
   'descricao': 'Investimento',
   'situacao': True,
   'templateDocumento': None},
  {'id': 25,
   'descricao': 'Outras Políticas',
   'situacao': True,
   'templateDocumento': None}],
 5: [],
 15: [{'id': 66,
   'descricao': 'Processo de enforcement',
   'situacao': True,
   'templateDocumento': None}],
 7: [{'id': 9,
   'descricao': 'Relatório Gerencial',
   'situacao': True,
   'templateDocumento': None},
  {'id': 10,
   'descricao': 'Press - Release',
   'situacao': True,
   'templateDocumento': None},
  {'id': 11,
   'descricao': 'Relatório Anual',
   'situacao': True,
   'templateDocumento': None},
  {'id': 12,
   'descricao': 'Outros Relatórios',
   'situacao': True,
   'templateDocumento': None},
  {'id': 68,
   'descricao': 'Relatório de Agência de Rating',
   'situacao': True,
   'templateDocumento': None},
  {'id': 71,
   'descricao': 'Relatório de Agente Fiduciário',
   'situacao': True,
   'templateDocumento': None}],
 17: []}


class PtBrBoolField(rows.fields.BoolField):
    @classmethod
    def deserialize(cls, value):
        value = str(value or "").strip().lower()
        if value == "s":
            return True
        elif value == "n":
            return False


class PtBrDateTimeField(rows.fields.Field):
    TYPE = (datetime.datetime,)

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        return value.isoformat() if value is not None else ""

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super().deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        return datetime.datetime.strptime(value, "%d/%m/%Y %H:%M")


field_types = OrderedDict([
    ("id", rows.fields.IntegerField),
    ("descricaoFundo", rows.fields.TextField),
    ("categoriaDocumento", rows.fields.TextField),
    ("tipoDocumento", rows.fields.TextField),
    ("especieDocumento", rows.fields.TextField),
    ("dataReferencia", rows.fields.TextField),
    ("dataEntrega", PtBrDateTimeField),
    ("status", rows.fields.TextField),
    ("descricaoStatus", rows.fields.TextField),
    ("analisado", PtBrBoolField),
    ("situacaoDocumento", rows.fields.TextField),
    ("assuntos", rows.fields.TextField),
    ("altaPrioridade", rows.fields.BoolField),
    ("formatoDataReferencia", rows.fields.IntegerField),
    ("versao", rows.fields.IntegerField),
    ("modalidade", rows.fields.TextField),
    ("descricaoModalidade", rows.fields.TextField),
    ("nomePregao", rows.fields.TextField),
    ("informacoesAdicionais", rows.fields.TextField),
    ("arquivoEstruturado", rows.fields.TextField),
    ("formatoEstruturaDocumento", rows.fields.TextField),
    ("nomeAdministrador", rows.fields.TextField),
    ("cnpjAdministrador", rows.fields.TextField),
    ("cnpjFundo", rows.fields.TextField),
    ("idTemplate", rows.fields.IntegerField),
    ("idSelectNotificacaoConvenio", rows.fields.TextField),
    ("idSelectItemConvenio", rows.fields.IntegerField),
    ("indicadorFundoAtivoB3", rows.fields.BoolField),
    ("idEntidadeGerenciadora", rows.fields.TextField),
    ("ofertaPublica", rows.fields.TextField),
    ("numeroEmissao", rows.fields.TextField),
    ("tipoPedido", rows.fields.TextField),
    ("dda", rows.fields.TextField),
])


# TODO: implementar crawler/parser para antes de 2016
# <https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/ResultListaPartic.aspx?TPConsulta=9>

class FundosNet:
    base_url = "https://fnet.bmfbovespa.com.br/fnet/publico/"

    def __init__(self, user_agent="mercado/python"):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.session.headers["CSRFToken"] = self.csrf_token
        self.draw = 0

    def request(self, method, path, headers=None, params=None, data=None, json=None, xhr=False):
        params = params or {}
        headers = headers or {}
        if xhr:
            self.draw += 1
            params["d"] = self.draw
            headers["X-Requested-With"] = "XMLHttpRequest"
        return self.session.request(
            method,
            urljoin(self.base_url, path),
            headers=headers,
            params=params,
            data=data,
            json=json,
        )

    @cached_property
    def main_page(self):
        response = self.request("GET", "abrirGerenciadorDocumentosCVM", xhr=False)
        return response.text

    @cached_property
    def csrf_token(self):
        # TODO: expires crsf_token after some time
        matches = REGEXP_CSRF_TOKEN.findall(self.main_page)
        if not matches:
            raise RuntimeError("Cannot find CSRF token")

        return matches[0]

    @cached_property
    def categories(self):
        tree = document_fromstring(self.main_page)
        return {
            option.xpath("./text()")[0].strip(): int(option.xpath("./@value")[0])
            for option in tree.xpath("//select[@id = 'categoriaDocumento']/option")
        }

    @cached_property
    def fund_types(self):
        tree = document_fromstring(self.main_page)
        options = tree.xpath("//select[@id = 'tipoFundo']/option")
        result = {}
        for option in options:
            key = option.xpath("./text()")[0].strip()
            value = option.xpath("./@value")[0].strip()
            if not value:
                key = "Todos"
            else:
                value = int(value)
            result[key] = value
        return result

    @cached_property
    def types(self):
        result = {}
        for category_id in self.categories.values():
            response = self.request("GET", "listarTodosTiposPorCategoria", params={"idCategoria": category_id}, xhr=True)
            result[category_id] = []
            for row in response.json():
                row["descricao"] = row["descricao"].strip()
                result[category_id].append(row)
        return result

    def paginate(self, path, params=None, xhr=True, items_per_page=200):
        params = params or {}
        params["s"] = 0  # rows to skip
        params["l"] = items_per_page  # page length
        params["_"] = int(time.time() * 1000)
        total_rows, finished = None, False
        while not finished:
            response = self.request("GET", path, params=params, xhr=xhr)
            response_data = response.json()
            if total_rows is None:
                total_rows = response_data["recordsTotal"]
            data = response_data["data"]
            # TODO: convert row
            # formatodatareferencia: {'2': '05/2022', '3': '17/06/2022', '4': '13/06/2022 15:00'}
            yield from data
            params["s"] += len(data)
            params["_"] = int(time.time() * 1000)
            finished = params["s"] >= total_rows

    def search(self, category="Todos", type_="Todos", fund_type="Todos", start_date=None, end_date=None, ordering_field="dataEntrega", order="desc", items_per_page=200):
        assert order in ("asc", "desc")
        assert ordering_field in ("b3CategoriaDescricao", "denominacaoSocial", "tipoDescricao", "especieDocumento", "dataReferencia", "dataEntrega", "situacaoDocumento", "versao", "modalidade")
        assert category in CATEGORIES
        category_id = CATEGORIES[category]
        assert type_ == "Todos" or type_ in [item["descricao"] for item in TYPES_BY_CATEGORY[category_id]]
        if type_ == "Todos":
            type_id = 0
        else:
            type_id = [item for item in TYPES_BY_CATEGORY[category_id] if item["descricao"] == type_][0]["id"]
        assert fund_type in FUND_TYPES
        fund_type_id = FUND_TYPES[fund_type]
        # TODO: filter other fields, like:
        # - administrador
        # - cnpj
        # - cnpjFundo
        # - idEspecieDocumento
        # - situacao
        # (there are others)
        # TODO: get all possible especie
        # TODO: get all administradores https://fnet.bmfbovespa.com.br/fnet/publico/buscarAdministrador?term=&page=2&paginaCertificados=false&_=1655592601540
        yield from self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params={
                f"o[0][{ordering_field}]": order,
                "idCategoriaDocumento": category_id,
                "idTipoDocumento": type_id,
                "tipoFundo": fund_type_id,
                "idEspecieDocumento": "0",
                "dataInicial": start_date.strftime("%d/%m/%Y") if start_date else "",
                "dataFinal": end_date.strftime("%d/%m/%Y") if end_date else "",
            },
            xhr=True,
            items_per_page=items_per_page,
        )


def download(document_ids, path):
    downloader = Downloader.subclasses()["aria2c"](path=path)
    for doc_id in document_ids:
        downloader.add(
            Download(
                url=f"https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id={doc_id}",
                filename=f"{doc_id}",
            )
        )
    downloader.run()
