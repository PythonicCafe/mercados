import base64
import csv
import datetime
import io
import json
import time
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Dict, List, Optional
from urllib.parse import urljoin
from zipfile import ZipFile

from mercados.bcb import Taxa
from mercados.utils import (
    BRT,
    USER_AGENT,
    clean_string,
    create_session,
    parse_br_date,
    parse_br_decimal,
    parse_date,
    parse_datetime_force_timezone,
    parse_iso_date,
    parse_time,
)

_UM_CENTAVO = Decimal("0.01")
_UM_MILESIMO = Decimal("0.001")
_UM_PONTO_BASE = Decimal("0.0001")
_DESCRICAO_CLI = "Coleta dados históricos de negociação, dentre outros"


def parse_br_int(value):
    if value is None or value == "":
        return None
    return int(value.replace(".", ""))


def parse_float(value):
    if value is None or value == "":
        return None
    return float(value)


def parse_decimal(value, places=2):
    if value is None or value == "":
        return None
    quantization = {2: _UM_CENTAVO, 3: _UM_MILESIMO, 4: _UM_PONTO_BASE}[places]
    return Decimal(value).quantize(quantization)


def json_decode(data):
    try:
        return json.loads(data)
    except json.decoder.JSONDecodeError:
        raise ValueError(f"Cannot decode JSON: {repr(data)}")


# TODO: pegar plantão de notícias <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/plantao-de-noticias/>
# TODO: Preço teórico de ETFs de renda fixa:
# https://sistemaswebb3-derivativos.b3.com.br/financialIndicatorsProxy/PriceEtfShare/GetPrices/eyJsYW5ndWFnZSI6InB0LWJyIn0=
# {"language":"pt-br"}

# TODO: notícias filtradas por empresas:
#       https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedHeadLines/
#       b'{"agency":"18","dateInitial":"2025-06-17","dateFinal":"2025-07-17","issuingCompany":"(CSMG"}'
#       issuingCompany tem um "(" antes?

# TODO: baixar e tratar vários arquivos de <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/pesquisa-por-pregao/>
#       Descrição: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/descricao-dos-arquivos/
#       Layout: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/layout-dos-arquivos/
# TODO: 'Arquivo de Índices' https://www.b3.com.br/pesquisapregao/download?filelist=IR241210.zip,
# TODO: 'Mercado de Títulos Públicos - Preços Referenciais para Títulos Públicos' https://www.b3.com.br/pesquisapregao/download?filelist=PU241210.ex_,
# TODO: 'Mercado de Câmbio - Taxas Praticadas, Parâmetros de Abertura e Operações Contratadas' https://www.b3.com.br/pesquisapregao/download?filelist=CT241210.zip,
# TODO: 'Mercado de Derivativos - Indicadores Econômicos e Agropecuários - Final' https://www.b3.com.br/pesquisapregao/download?filelist=ID241210.ex_,
# TODO: 'Mercado de Derivativos - Negócios Realizados no Mercado de Balcão' https://www.b3.com.br/pesquisapregao/download?filelist=BE241210.ex_,
# TODO: 'Mercado de Derivativos - Negócios Registrados em Leilão BACEN' https://www.b3.com.br/pesquisapregao/download?filelist=LB180802.zip,
# TODO: 'Renda Fixa Privada' https://www.b3.com.br/pesquisapregao/download?filelist=RF241210.ex_,
# TODO: 'Taxas do Mercado de Renda Variável' https://www.b3.com.br/pesquisapregao/download?filelist=TX241202.zip,

# TODO: pegar negociações after market de
# <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/>
# ou de lugar parecido com as de balcão?

# TODO: opções - séries autorizadas https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/series-autorizadas/
# TOOD: dados em tempo real (com atraso) -- ver https://pypi.org/project/b3api/
# TODO: pegar DI histórico http://estatisticas.cetip.com.br/astec/series_v05/paginas/lum_web_v05_template_informacoes_di.asp?str_Modulo=completo&int_Idioma=1&int_Titulo=6&int_NivelBD=2


@lru_cache(maxsize=16 * 1024)
def converte_centavos_para_decimal(valor: str) -> Optional[Decimal]:
    """Converte um valor em centavos em str para Decimal em Reais com 2 casas decimais

    >>> print(converte_centavos_para_decimal(""))
    None
    >>> print(converte_centavos_para_decimal(None))
    None
    >>> converte_centavos_para_decimal("0")
    Decimal('0.00')
    >>> converte_centavos_para_decimal("1")
    Decimal('0.01')
    >>> converte_centavos_para_decimal("10")
    Decimal('0.10')
    >>> converte_centavos_para_decimal("100")
    Decimal('1.00')
    >>> converte_centavos_para_decimal("12356")
    Decimal('123.56')
    """
    return (Decimal(valor) / 100).quantize(_UM_CENTAVO) if valor else None


@lru_cache(maxsize=16 * 1024)
def converte_decimal(valor: str) -> Optional[Decimal]:
    """
    >>> print(converte_decimal(""))
    None
    >>> print(converte_decimal("   \\t\\n "))
    None
    >>> print(converte_decimal(None))
    None
    >>> converte_decimal("1.23")
    Decimal('1.23')
    >>> converte_decimal("1.23456789")
    Decimal('1.23456789')
    >>> converte_decimal("1.2")
    Decimal('1.20')
    """
    valor = str(valor or "").strip()
    if not valor:
        return None
    valor = Decimal(valor)
    if len(str(valor - int(valor))) < 4:
        valor = valor.quantize(_UM_CENTAVO)
    return valor


@dataclass
class Codigo:
    negociacao: str
    isin: str

    def serialize(self):
        return {
            "negociacao": self.negociacao,
            "isin": self.isin,
        }


@dataclass
class Empresa:
    codigo_cvm: int
    emissora: str
    razao_social: str
    nome_pregao: str
    indicador_mercado: int
    estado: str
    segmento: str
    tipo: int
    cnpj: Optional[str] = None
    mercado: Optional[str] = None
    data_listagem: Optional[datetime.date] = None
    tipo_bdr: Optional[str] = None
    inicio_negociacao: Optional[datetime.date] = None
    atividade_principal: Optional[str] = None
    classificacao_setorial: Optional[str] = None
    website: Optional[str] = None
    codigo_negociacao: Optional[str] = None
    instituicao: list[str] = None
    outros_codigos: list[Codigo] = None
    tem_bdr: Optional[str] = None
    tem_emissoes: Optional[bool] = None

    @classmethod
    def _parse_base(cls, row):
        # XXX: para o registro de empresa detalhado, não temos 'dateListing', 'segment', 'segmentEng' e 'type'
        data_listagem = row.pop("dateListing", None)  # TODO: É o início da negociação?
        if data_listagem is not None:
            if data_listagem.endswith("/9999"):
                data_listagem = None
            else:
                data_listagem = parse_date("br-date", data_listagem)
        cnpj = row.pop("cnpj")
        if cnpj == "0":
            cnpj = None
        row.pop("segmentEng", None)  # Segmento em Inglês - ignorado (`None` para caso `detalhe = True`)
        tipo = row.pop("type", None)
        tipo = int(tipo) if tipo is not None else None
        return {
            "codigo_cvm": int(row.pop("codeCVM")),
            "emissora": row.pop("issuingCompany"),
            "razao_social": row.pop("companyName"),
            "nome_pregao": row.pop("tradingName"),
            "cnpj": cnpj,
            "data_listagem": data_listagem,
            "indicador_mercado": int(row.pop("marketIndicator")),
            "tipo_bdr": row.pop("typeBDR") or None,
            "estado": row.pop("status"),
            "segmento": row.pop("segment", None),
            "tipo": tipo,
            "mercado": row.pop("market"),
        }

    @classmethod
    def from_dict(cls, row, detalhe=None):
        if row is not None:
            obj = cls._parse_base(row)
            assert not row, f"Dados de empresa listada não extraídos: {row}"
        elif not detalhe:
            raise ValueError("Dados da empresa em branco")
        else:  # Caso de `B3.empresa_detalhe`
            obj = {}

        if detalhe:
            novo_base = cls._parse_base(detalhe)
            for key, value in novo_base.items():
                obj[key] = value or obj.get(key)  # `.get()` é usado para caso `row` seja `None`
            row = detalhe
            campos_ignorados = (
                "industryClassificationEng",  # Não nos interessa, já temos em Português
                "hasQuotation",  # Vem sempre `None`
                "describleCategoryBVMF",  # Vem sempre `None`
                "lastDate",  # Não é exibido na interface do site
            )
            for campo in campos_ignorados:
                del row[campo]
            obj.update(
                {
                    "inicio_negociacao": parse_date(
                        "br-date", row.pop("dateQuotation")
                    ),  # TODO: é o mesmo que dateListing?
                    "atividade_principal": row.pop("activity"),  # TODO: é o mesmo que segment?
                    "classificacao_setorial": row.pop("industryClassification"),  # TODO: é o mesmo que segment?
                    "website": row.pop("website"),
                    "codigo_negociacao": row.pop("code"),
                    "tem_bdr": row.pop("hasBDR"),
                    "tem_emissoes": row.pop("hasEmissions"),
                    "instituicao": [
                        item for item in (row.pop("institutionCommon"), row.pop("institutionPreferred")) if item
                    ],
                    "outros_codigos": [],
                }
            )
            codigos = row.pop("otherCodes") or []
            for codigo in codigos:
                negociacao, isin = codigo.pop("code"), codigo.pop("isin")
                obj["outros_codigos"].append(Codigo(negociacao=negociacao, isin=isin))
                assert not codigo, f"Dados de código de negociação não extraídos: {codigo}"
            assert not row, f"Dados detalhados de empresa listada não extraídos: {row}"
        return cls(**obj)

    def serialize(self):
        return {
            "codigo_cvm": self.codigo_cvm,
            "emissora": self.emissora,
            "razao_social": self.razao_social,
            "nome_pregao": self.nome_pregao,
            "indicador_mercado": self.indicador_mercado,
            "estado": self.estado,
            "segmento": self.segmento,
            "tipo": self.tipo,
            "cnpj": self.cnpj,
            "mercado": self.mercado,
            "data_listagem": self.data_listagem,
            "tipo_bdr": self.tipo_bdr,
            "inicio_negociacao": self.inicio_negociacao,
            "atividade_principal": self.atividade_principal,
            "classificacao_setorial": self.classificacao_setorial,
            "website": self.website,
            "codigo_negociacao": self.codigo_negociacao,
            "instituicao": self.instituicao,
            "outros_codigos": self.outros_codigos,
            "tem_bdr": self.tem_bdr,
            "tem_emissoes": self.tem_emissoes,
        }


@dataclass
class AtivoIndice:
    codigo_negociacao: str
    ativo: str
    tipo: str
    qtd_teorica: Decimal
    participacao: Decimal

    def serialize(self):
        return {
            "codigo_negociacao": self.codigo_negociacao,
            "ativo": self.ativo,
            "tipo": self.tipo,
            "qtd_teorica": self.qtd_teorica,
            "participacao": self.participacao,
        }


@dataclass
class NegociacaoBolsa:
    quantidade: Optional[int]
    pontos_strike: Optional[int]
    data: datetime.date
    data_vencimento: Optional[datetime.date]
    negociacoes: Optional[int]
    lote: Optional[int]
    indice_correcao: Optional[int]
    distribuicao: Optional[int]
    codigo_bdi: Optional[int]
    codigo_tipo_mercado: Optional[int]
    prazo_termo: Optional[int]
    codigo_isin: str
    codigo_negociacao: str
    moeda: str
    nome_pregao: str
    tipo_papel: str
    preco_abertura: Optional[Decimal]
    preco_maximo: Optional[Decimal]
    preco_minimo: Optional[Decimal]
    preco_medio: Optional[Decimal]
    preco_ultimo: Optional[Decimal]
    preco_melhor_oferta_compra: Optional[Decimal]
    preco_melhor_oferta_venda: Optional[Decimal]
    volume: Optional[Decimal]
    preco_execucao: Optional[Decimal]

    @classmethod
    def _line_to_dict(cls, line):
        return {
            "date_of_exchange": line[2:10].strip(),
            "codbdi": line[10:12].strip(),
            "codneg": line[12:24].strip(),
            "tpmerc": line[24:27].strip(),
            "nomres": line[27:39].strip(),
            "especi": line[39:49].strip(),
            "prazot": line[49:52].strip(),
            "modref": line[52:56].strip(),
            "preabe": line[56:69].strip(),
            "premax": line[69:82].strip(),
            "premin": line[82:95].strip(),
            "premed": line[95:108].strip(),
            "preult": line[108:121].strip(),
            "preofc": line[121:134].strip(),
            "preofv": line[134:147].strip(),
            "totneg": line[147:152].strip(),
            "quatot": line[152:170].strip(),
            "voltot": line[170:188].strip(),
            "preexe": line[188:201].strip(),
            "indopc": line[201:202].strip(),
            "datven": line[202:210].strip(),
            "fatcot": line[210:217].strip(),
            "ptoexe": line[217:230].strip(),
            "codisi": line[230:242].strip(),
            "dismes": line[242:245].strip(),
        }

    @classmethod
    def from_line(cls, line: str):
        assert len(line) == 246 and line[:2] == "01"
        row = cls._line_to_dict(line)
        qtd = row.pop("quatot")
        strike = row.pop("ptoexe")
        vencimento = row.pop("datven")
        negociacoes = row.pop("totneg")
        lote = row.pop("fatcot")
        indice_correcao = row.pop("indopc")
        distribuicao = row.pop("dismes")
        codigo_bdi = row.pop("codbdi")
        codigo_tipo_mercado = row.pop("tpmerc")
        prazo_termo = row.pop("prazot")
        obj = cls(
            quantidade=int(qtd) if qtd else None,
            pontos_strike=int(strike) if strike != "0000000000000" else None,
            data=datetime.datetime.strptime(row.pop("date_of_exchange"), "%Y%m%d").date(),
            data_vencimento=(
                None if vencimento == "99991231" else datetime.datetime.strptime(vencimento, "%Y%m%d").date()
            ),
            negociacoes=int(negociacoes) if negociacoes else None,
            lote=int(lote) if lote else None,
            indice_correcao=int(indice_correcao) if indice_correcao else None,
            distribuicao=int(distribuicao) if distribuicao else None,
            codigo_bdi=int(codigo_bdi) if codigo_bdi else None,
            codigo_tipo_mercado=int(codigo_tipo_mercado) if codigo_tipo_mercado else None,
            prazo_termo=None if prazo_termo == "" else int(prazo_termo),
            codigo_isin=row.pop("codisi"),
            codigo_negociacao=row.pop("codneg").strip(),
            moeda=row.pop("modref"),
            nome_pregao=row.pop("nomres"),
            tipo_papel=row.pop("especi"),
            preco_abertura=converte_centavos_para_decimal(row.pop("preabe")),
            preco_maximo=converte_centavos_para_decimal(row.pop("premax")),
            preco_minimo=converte_centavos_para_decimal(row.pop("premin")),
            preco_medio=converte_centavos_para_decimal(row.pop("premed")),
            preco_ultimo=converte_centavos_para_decimal(row.pop("preult")),
            preco_melhor_oferta_compra=converte_centavos_para_decimal(row.pop("preofc")),
            preco_melhor_oferta_venda=converte_centavos_para_decimal(row.pop("preofv")),
            volume=converte_centavos_para_decimal(row.pop("voltot")),
            preco_execucao=converte_centavos_para_decimal(row.pop("preexe")),
        )
        assert not row, f"Dados de negociação não extraídos: {row=}"
        return obj

    def serialize(self):
        return {
            "quantidade": self.quantidade,
            "pontos_strike": self.pontos_strike,
            "data": self.data,
            "data_vencimento": self.data_vencimento,
            "negociacoes": self.negociacoes,
            "lote": self.lote,
            "indice_correcao": self.indice_correcao,
            "distribuicao": self.distribuicao,
            "codigo_bdi": self.codigo_bdi,
            "codigo_tipo_mercado": self.codigo_tipo_mercado,
            "prazo_termo": self.prazo_termo,
            "codigo_isin": self.codigo_isin,
            "codigo_negociacao": self.codigo_negociacao,
            "moeda": self.moeda,
            "nome_pregao": self.nome_pregao,
            "tipo_papel": self.tipo_papel,
            "preco_abertura": self.preco_abertura,
            "preco_maximo": self.preco_maximo,
            "preco_minimo": self.preco_minimo,
            "preco_medio": self.preco_medio,
            "preco_ultimo": self.preco_ultimo,
            "preco_melhor_oferta_compra": self.preco_melhor_oferta_compra,
            "preco_melhor_oferta_venda": self.preco_melhor_oferta_venda,
            "volume": self.volume,
            "preco_execucao": self.preco_execucao,
        }


@dataclass
class PrecoAtivo:
    codigo_negociacao: str
    valor: Decimal
    datahora: datetime.datetime

    @classmethod
    def from_dict(cls, data, codigo_negociacao, row):
        obj = cls(
            codigo_negociacao=codigo_negociacao,
            valor=Decimal(row.pop("closPric")).quantize(_UM_CENTAVO),
            datahora=parse_date("iso-datetime-tz", f"{data}T{row.pop('dtTm')}-0300", full=True),
        )
        row.pop("prcFlcn")  # Flutuação - ignorado
        assert not row, f"Dados de preço não extraídos: {row=}"
        return obj

    def serialize(self):
        return {
            "codigo_negociacao": self.codigo_negociacao,
            "valor": self.valor,
            "datahora": self.datahora,
        }


@dataclass
class Dividendo:
    tipo: str
    codigo_isin: str
    data_aprovacao: datetime.date
    data_base: datetime.date
    data_pagamento: datetime.date
    valor_por_cota: Decimal
    periodo_referencia: str

    @classmethod
    def from_dict(cls, row):
        tipo_mapping = {
            "AMORTIZACAO RF": "Amortização RF",
            "DIVIDENDO": "Dividendo",
            "RENDIMENTO": "Rendimento",
        }
        return cls(
            codigo_isin=row["isinCode"],
            data_aprovacao=parse_br_date(row["approvedOn"]),
            data_base=parse_br_date(row["lastDatePrior"]),
            data_pagamento=parse_br_date(row["paymentDate"]),
            valor_por_cota=converte_decimal(row["rate"].replace(".", "").replace(",", ".")),
            periodo_referencia=row["relatedTo"],
            tipo=tipo_mapping.get(row["label"], row["label"]),
        )

    def serialize(self):
        return {
            "tipo": self.tipo,
            "codigo_isin": self.codigo_isin,
            "data_aprovacao": self.data_aprovacao,
            "data_base": self.data_base,
            "data_pagamento": self.data_pagamento,
            "valor_por_cota": self.valor_por_cota,
            "periodo_referencia": self.periodo_referencia,
        }


@dataclass
class FundoDocumento:
    acronimo: str
    fundo: str
    tipo: str
    datahora_entrega: datetime.datetime
    url: str
    data_referencia: datetime.date = None
    data_ordem: datetime.date = None

    @classmethod
    def from_dict(cls, acronimo, row):
        """
        >>> FundoDocumento.from_dict('XPID', {'name': 'Regulamento', 'date': '2021-05-05T11:29:59.46', 'referenceDate': '', 'companyName': 'XP FDO INV. COTAS FDO INC. INV. EM INFR. R. FIXA  ', 'dateOrder': '0001-01-01T00:00:00'})
        FundoDocumento(acronimo='XPID', fundo='XP FDO INV. COTAS FDO INC. INV. EM INFR. R. FIXA', tipo='Regulamento', datahora_entrega=datetime.datetime(2021, 5, 5, 11, 29, 59, 460000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=75600))), url='https://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=XPID&strData=2021-05-05T11:29:59.46', data_referencia=None, data_ordem=None)
        """
        return cls(
            acronimo=acronimo,
            fundo=clean_string(row["companyName"]),
            tipo=row["name"],
            datahora_entrega=parse_datetime_force_timezone(row["date"]),
            data_referencia=parse_br_date(row["referenceDate"]),
            data_ordem=parse_date("iso-date", row["dateOrder"].replace("T00:00:00", "")),
            url=f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla={acronimo}&strData={row['date']}",
        )

    def serialize(self):
        return {
            "acronimo": self.acronimo,
            "fundo": self.fundo,
            "tipo": self.tipo,
            "datahora_entrega": self.datahora_entrega,
            "url": self.url,
            "data_referencia": self.data_referencia,
            "data_ordem": self.data_ordem,
        }


@dataclass
class FundoB3Resumido:
    id_fnet: int
    tipo: str
    acronimo: str
    nome_negociacao: str
    empresa_razao_social: str

    def serialize(self):
        return {
            "id_fnet": self.id_fnet,
            "tipo": self.tipo,
            "acronimo": self.acronimo,
            "nome_negociacao": self.nome_negociacao,
            "empresa_razao_social": self.empresa_razao_social,
        }

    @classmethod
    def from_dict(cls, obj, tipo, check=True):
        data = deepcopy(obj)

        id_fnet = data.pop("id")
        tipo = data.pop("typeName") or tipo
        acronimo = clean_string(data.pop("acronym"))
        empresa_razao_social = clean_string(data.pop("fundName"))
        nome_negociacao = clean_string(data.pop("tradingName"))
        if check:
            assert not data, f"Dados do fundo não extraídos: {data=}"
        return cls(
            id_fnet=id_fnet,
            tipo=tipo,
            acronimo=acronimo,
            nome_negociacao=nome_negociacao,
            empresa_razao_social=empresa_razao_social,
        )


@dataclass
class FundoB3:
    id_fnet: int
    tipo: str
    acronimo: str
    nome_negociacao: str
    cnpj: str
    classificacao: str
    endereco: str
    ddd: str
    telefone: str
    fax: str
    empresa_endereco: str
    empresa_ddd: str
    empresa_telefone: str
    empresa_fax: str
    empresa_email: str
    empresa_razao_social: str
    cotas: float
    data_aprovacao_cotas: datetime.date
    administrador_responsavel: str
    administrador_responsavel_cargo: str
    administrador: Optional[str] = None
    administrador_endereco: Optional[str] = None
    administrador_ddd: Optional[str] = None
    administrador_telefone: Optional[str] = None
    administrador_fax: Optional[str] = None
    administrador_email: Optional[str] = None
    website: Optional[str] = None
    tipo_fnet: Optional[str] = None
    codigos_negociacao: Optional[List[str]] = None
    segmento: Optional[str] = None

    @property
    def codigo_negociacao(self):
        return self.codigos_negociacao[0] if self.codigos_negociacao else f"{self.acronimo}11"

    def serialize(self):
        obj = {
            "id_fnet": self.id_fnet,
            "tipo": self.tipo,
            "acronimo": self.acronimo,
            "nome_negociacao": self.nome_negociacao,
            "cnpj": self.cnpj,
            "classificacao": self.classificacao,
            "endereco": self.endereco,
            "ddd": self.ddd,
            "telefone": self.telefone,
            "fax": self.fax,
            "empresa_endereco": self.empresa_endereco,
            "empresa_ddd": self.empresa_ddd,
            "empresa_telefone": self.empresa_telefone,
            "empresa_fax": self.empresa_fax,
            "empresa_email": self.empresa_email,
            "empresa_razao_social": self.empresa_razao_social,
            "cotas": self.cotas,
            "data_aprovacao_cotas": self.data_aprovacao_cotas,
            "administrador_responsavel": self.administrador_responsavel,
            "administrador_responsavel_cargo": self.administrador_responsavel_cargo,
            "administrador": self.administrador,
            "administrador_endereco": self.administrador_endereco,
            "administrador_ddd": self.administrador_ddd,
            "administrador_telefone": self.administrador_telefone,
            "administrador_fax": self.administrador_fax,
            "administrador_email": self.administrador_email,
            "website": self.website,
            "tipo_fnet": self.tipo_fnet,
            "codigos_negociacao": self.codigos_negociacao,
            "segmento": self.segmento,
        }
        if obj["data_aprovacao_cotas"]:
            obj["data_aprovacao_cotas"] = obj["data_aprovacao_cotas"].isoformat()
        if obj["codigos_negociacao"]:
            obj["codigos_negociacao"] = json.dumps(obj["codigos_negociacao"])
        return obj

    @classmethod
    def from_dict(cls, obj, check=True):
        data = deepcopy(obj)

        shareholder = data.pop("shareHolder") or {}
        administrador = clean_string(shareholder.pop("shareHolderName", None))
        administrador_endereco = clean_string(shareholder.pop("shareHolderAddress", None))
        administrador_ddd = clean_string(shareholder.pop("shareHolderPhoneNumberDDD", None))
        administrador_telefone = clean_string(shareholder.pop("shareHolderPhoneNumber", None))
        administrador_fax = clean_string(shareholder.pop("shareHolderFaxNumber", None))
        administrador_fax = administrador_fax if administrador_fax != "0" else None
        administrador_email = clean_string(shareholder.pop("shareHolderEmail", None))
        administrador_responsavel = clean_string(data.pop("managerName"))
        administrador_responsavel_cargo = clean_string(data.pop("positionManager"))
        if check:
            assert not shareholder, f"Dados não extraídos: {shareholder=}"

        codigo_negociacao = clean_string(data.pop("tradingCode"))
        codigos_negociacao = [codigo_negociacao] if codigo_negociacao else []
        outros = data.pop("tradingCodeOthers")
        if outros and outros is not None:
            for item in outros.split(","):
                item = clean_string(item)
                if item not in codigos_negociacao:
                    codigos_negociacao.append(item)
        id_fnet = data.pop("idFNET")
        tipo = data.pop("typeName")
        acronimo = clean_string(data.pop("acronym"))
        nome_negociacao = clean_string(data.pop("tradingName"))
        fax = clean_string(data.pop("fundPhoneNumberFax"))
        fax = fax if fax != "0" else None
        empresa_fax = clean_string(data.pop("companyPhoneNumberFax", None))
        empresa_fax = empresa_fax if empresa_fax != "0" else None
        cnpj = clean_string(data.pop("cnpj"))
        classificacao = clean_string(data.pop("classification"))
        cotas = parse_br_int(clean_string(data.pop("quotaCount")))
        data_aprovacao_cotas = parse_br_date(clean_string(data.pop("quotaDateApproved")))
        tipo_fnet = clean_string(data.pop("typeFNET"))
        endereco = clean_string(data.pop("fundAddress"))
        segmento = clean_string(data.pop("segment"))
        ddd = clean_string(data.pop("fundPhoneNumberDDD"))
        telefone = clean_string(data.pop("fundPhoneNumber"))
        empresa_endereco = clean_string(data.pop("companyAddress", None))
        empresa_ddd = clean_string(data.pop("companyPhoneNumberDDD", None))
        empresa_telefone = clean_string(data.pop("companyPhoneNumber", None))
        empresa_email = clean_string(data.pop("companyEmail", None))
        empresa_razao_social = clean_string(data.pop("fundName"))
        website = clean_string(data.pop("webSite"))
        if website and not website.lower().startswith("https:") and not website.lower().startswith("http:"):
            website = f"https://{website}"
        # TODO: guardar/tratar esses campos
        data.pop("type")
        data.pop("classes")
        if check:
            assert not data, f"Dados do fundo não extraídos: {data=}"

        return cls(
            id_fnet=id_fnet,
            tipo=tipo,
            acronimo=acronimo,
            nome_negociacao=nome_negociacao,
            cnpj=cnpj,
            classificacao=classificacao,
            endereco=endereco,
            ddd=ddd,
            telefone=telefone,
            fax=fax,
            empresa_endereco=empresa_endereco,
            empresa_ddd=empresa_ddd,
            empresa_telefone=empresa_telefone,
            empresa_fax=empresa_fax,
            empresa_email=empresa_email,
            empresa_razao_social=empresa_razao_social,
            cotas=cotas,
            data_aprovacao_cotas=data_aprovacao_cotas,
            administrador=administrador,
            administrador_endereco=administrador_endereco,
            administrador_ddd=administrador_ddd,
            administrador_telefone=administrador_telefone,
            administrador_fax=administrador_fax,
            administrador_responsavel=administrador_responsavel,
            administrador_responsavel_cargo=administrador_responsavel_cargo,
            administrador_email=administrador_email,
            website=website,
            tipo_fnet=tipo_fnet,
            codigos_negociacao=codigos_negociacao,
            segmento=segmento,
        )


@dataclass
class NegociacaoBalcao:
    codigo: str
    codigo_if: str
    instrumento: str
    datahora: datetime.date
    quantidade: Decimal
    preco: Decimal
    volume: Decimal
    origem: str
    codigo_isin: str = None
    data_liquidacao: datetime.date = None
    emissor: str = None
    situacao: str = None
    taxa: Decimal = None

    @classmethod
    def from_dict(cls, row):
        day, month, year = row.pop("Data Negocio").split("/")
        date = f"{year}-{int(month):02d}-{int(day):02d}"
        quantidade = parse_br_decimal(row.pop("Quantidade Negociada"))
        preco = parse_br_decimal(row.pop("Preco Negocio"))
        volume = parse_br_decimal(row.pop("Volume Financeiro R$").replace("################", ""))
        if volume is None:  # Only in 2 cases in 2021
            volume = quantidade * preco
        data_liquidacao = str(row.pop("Data Liquidacao") or "").strip()
        data_liquidacao = data_liquidacao.split()[0] if data_liquidacao else None
        data_liquidacao = parse_date("br-date", data_liquidacao)
        obj = cls(
            codigo=row.pop("Cod. Identificador do Negocio"),
            codigo_if=row.pop("Codigo IF"),
            codigo_isin=row.pop("Cod. Isin"),
            data_liquidacao=data_liquidacao,
            datahora=parse_date("iso-datetime-tz", f"{date}T{row.pop('Horario Negocio')}-03:00"),
            emissor=row.pop("Emissor"),
            instrumento=row.pop("Instrumento Financeiro"),
            taxa=parse_br_decimal(row.pop("Taxa Negocio")),
            quantidade=quantidade,
            preco=preco,
            volume=volume,
            origem=row.pop("Origem Negocio"),
            situacao=row.pop("Situacao Negocio", None),
        )
        assert not row
        return obj

    @classmethod
    def from_converted_dict(cls, row):
        data_liquidacao = row.pop("data_liquidacao")
        taxa = row.pop("taxa")
        obj = cls(
            codigo=row.pop("codigo"),
            codigo_if=row.pop("codigo_if"),
            instrumento=row.pop("instrumento"),
            datahora=parse_date("iso-datetime-tz", row.pop("datahora")),
            quantidade=converte_decimal(row.pop("quantidade")),
            preco=converte_decimal(row.pop("preco")),
            volume=converte_decimal(row.pop("volume")),
            origem=row.pop("origem"),
            codigo_isin=row.pop("codigo_isin") or None,
            data_liquidacao=parse_date("iso-date", data_liquidacao) if data_liquidacao else None,
            emissor=row.pop("emissor") or None,
            taxa=converte_decimal(taxa) if taxa else None,
        )
        assert not row
        return obj

    def serialize(self):
        return {
            "codigo": self.codigo,
            "codigo_if": self.codigo_if,
            "instrumento": self.instrumento,
            "datahora": self.datahora,
            "quantidade": self.quantidade,
            "preco": self.preco,
            "volume": self.volume,
            "origem": self.origem,
            "codigo_isin": self.codigo_isin,
            "data_liquidacao": self.data_liquidacao,
            "emissor": self.emissor,
            "situacao": self.situacao,
            "taxa": self.taxa,
        }


@dataclass
class NegociacaoIntradiaria:
    """
    Representa uma negociação intradiária na B3

    Extraído de acordo com o documento "Negócio a negócio - Listados (.PDF, 105KB)", encontrado em:
    <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/glossario/>
    """

    datahora: datetime.datetime
    codigo_negocio: int
    codigo_negociacao: str
    acao_atualizacao: int
    preco: Decimal
    quantidade: int
    pregao_tipo: int
    comprador_codigo: str
    vendedor_codigo: str

    @classmethod
    def from_dict(cls, row: Dict):
        row.pop("DataReferencia")  # Não será usado, dado que DataNegocio é a data em que o negócio ocorreu
        data = parse_date("iso-date", row.pop("DataNegocio"))
        hora = parse_time(row.pop("HoraFechamento"))
        datahora = datetime.datetime.combine(data, hora).replace(tzinfo=BRT)
        obj = cls(
            datahora=datahora,
            codigo_negociacao=row.pop("CodigoInstrumento"),
            acao_atualizacao=int(row.pop("AcaoAtualizacao")),
            preco=parse_br_decimal(row.pop("PrecoNegocio")),
            quantidade=int(row.pop("QuantidadeNegociada")),
            codigo_negocio=int(row.pop("CodigoIdentificadorNegocio")),
            pregao_tipo=int(row.pop("TipoSessaoPregao")),
            comprador_codigo=row.pop("CodigoParticipanteComprador"),
            vendedor_codigo=row.pop("CodigoParticipanteVendedor"),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "datahora": self.datahora,
            "codigo_negocio": self.codigo_negocio,
            "codigo_negociacao": self.codigo_negociacao,
            "acao_atualizacao": self.acao_atualizacao,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "pregao_tipo": self.pregao_tipo,
            "comprador_codigo": self.comprador_codigo,
            "vendedor_codigo": self.vendedor_codigo,
        }


@dataclass
class EmprestimoAtivo:
    data: datetime.date
    codigo_negociacao: str
    codigo_isin: str
    nome: str
    mercado: str
    contratos: int
    quantidade: int
    minima: float
    media_ponderada: float
    maxima: float
    valor: Decimal
    taxa_doador: float
    taxa_tomador: float

    @classmethod
    def from_dict(cls, row):
        key = "Data"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            data=row.pop("Data"),
            codigo_negociacao=row.pop("Código IF"),
            codigo_isin=row.pop("Código ISIN"),
            nome=row.pop("Empresa ou fundo"),
            mercado=row.pop("Mercado"),
            contratos=int(row.pop("Número de contratos")),
            quantidade=int(row.pop("Quantidade de ativos")),
            minima=parse_float(row.pop("Mínima")),
            media_ponderada=parse_float(row.pop("Média ponderada")),
            maxima=parse_float(row.pop("Máxima")),
            valor=parse_decimal(row.pop("Valor em R$")),
            taxa_doador=parse_float(row.pop("Taxa doador")),
            taxa_tomador=parse_float(row.pop("Taxa tomador")),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data": self.data,
            "codigo_negociacao": self.codigo_negociacao,
            "codigo_isin": self.codigo_isin,
            "nome": self.nome,
            "mercado": self.mercado,
            "contratos": self.contratos,
            "quantidade": self.quantidade,
            "minima": self.minima,
            "media_ponderada": self.media_ponderada,
            "maxima": self.maxima,
            "valor": self.valor,
            "taxa_doador": self.taxa_doador,
            "taxa_tomador": self.taxa_tomador,
        }


@dataclass
class EmprestimoNegociado:
    data_referencia: datetime.date
    codigo_negociacao: str
    quantidade: int
    taxa_remuneracao: float
    numero_negocio: int
    mercado: str
    data_hora: datetime.datetime
    codigo: int
    doador: str
    tomador: str
    acao_atualizacao: str
    tipo_sessao_pregao: str
    participante_doador: str
    participante_tomador: str

    @classmethod
    def from_dict(cls, row):
        key = "Data de referência"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            data_referencia=row.pop("Data de referência"),
            codigo_negociacao=row.pop("Papel"),
            quantidade=int(row.pop("Quantidade")),
            codigo=int(row.pop("Código")),
            taxa_remuneracao=parse_float(row.pop("Taxa % Remuneração")),
            numero_negocio=int(row.pop("Número do negócio")),
            mercado=row.pop("Mercado"),
            data_hora=parse_datetime_force_timezone(row.pop("Hora")),
            doador=row.pop("Nome Doador"),
            tomador=row.pop("Nome Tomador"),
            acao_atualizacao=row.pop("Ação de Atualização"),
            tipo_sessao_pregao=row.pop("Tipo Sessão do Pregão"),
            participante_doador=row.pop("Participante Doador"),
            participante_tomador=row.pop("Participante Tomador"),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data_referencia": self.data_referencia,
            "codigo_negociacao": self.codigo_negociacao,
            "quantidade": self.quantidade,
            "taxa_remuneracao": self.taxa_remuneracao,
            "numero_negocio": self.numero_negocio,
            "mercado": self.mercado,
            "data_hora": self.data_hora,
            "codigo": self.codigo,
            "doador": self.doador,
            "tomador": self.tomador,
            "acao_atualizacao": self.acao_atualizacao,
            "tipo_sessao_pregao": self.tipo_sessao_pregao,
            "participante_doador": self.participante_doador,
            "participante_tomador": self.participante_tomador,
        }


@dataclass
class EmprestimoEmAberto:
    data: datetime.date
    codigo_negociacao: str
    codigo_isin: str
    empresa: str
    tipo: str
    mercado: str
    saldo_quantidade: int
    saldo: Decimal
    preco_medio: Decimal = None

    @classmethod
    def from_dict(cls, row):
        key = "Data"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            data=row.pop("Data"),
            codigo_negociacao=row.pop("Código IF"),
            codigo_isin=row.pop("Código ISIN"),
            empresa=row.pop("Empresa ou fundo"),
            tipo=row.pop("Tipo de empréstimo"),
            mercado=row.pop("Mercado"),
            saldo_quantidade=int(row.pop("Saldo em quantidade do ativo")),
            preco_medio=parse_decimal(row.pop("Preço médio")),
            saldo=parse_decimal(row.pop("Saldo em R$")),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data": self.data,
            "codigo_negociacao": self.codigo_negociacao,
            "codigo_isin": self.codigo_isin,
            "empresa": self.empresa,
            "tipo": self.tipo,
            "mercado": self.mercado,
            "saldo_quantidade": self.saldo_quantidade,
            "saldo": self.saldo,
            "preco_medio": self.preco_medio,
        }


@dataclass
class OpcaoFlexivel:
    codigo_negociacao: str
    operacao: str
    descricao: str
    vencimento: datetime.date
    negocios: int
    volume: Decimal
    premio_medio: Decimal
    preco_exercicio_medio: Decimal

    @classmethod
    def from_dict(cls, row):
        key = "Vencimento"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            codigo_negociacao=row.pop("Código"),
            operacao=row.pop("Tipo de opção"),
            descricao=row.pop("Opção"),
            vencimento=row.pop("Vencimento"),
            negocios=int(row.pop("Número de negócios")),
            volume=parse_decimal(row.pop("Volume (R$)")),
            premio_medio=parse_decimal(row.pop("Prêmio médio (R$)"), places=4),
            preco_exercicio_medio=parse_decimal(row.pop("Preço exercício médio (R$)"), places=4),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "codigo_negociacao": self.codigo_negociacao,
            "operacao": self.operacao,
            "descricao": self.descricao,
            "vencimento": self.vencimento,
            "negocios": self.negocios,
            "volume": self.volume,
            "premio_medio": self.premio_medio,
            "preco_exercicio_medio": self.preco_exercicio_medio,
        }


@dataclass
class PrazoDeposito:
    data: datetime.date
    empresa: str
    codigo: str
    tipo: str

    @classmethod
    def from_dict(cls, row):
        key = "Data"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            data=row.pop("Data"),
            empresa=row.pop("Empresa"),
            codigo=row.pop("Código"),
            tipo=row.pop("Provento"),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data": self.data,
            "empresa": self.empresa,
            "codigo": self.codigo,
            "tipo": self.tipo,
        }


@dataclass
class PosicaoEmAberto:
    data: datetime.date
    mercado: str
    contratos: int
    valor_milhares: Decimal
    ordenacao: int

    @classmethod
    def from_dict(cls, row):
        key = "Data"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            data=row.pop("Data"),
            mercado=row.pop("Mercado"),
            contratos=int(row.pop("Número de contratos")),
            valor_milhares=parse_decimal(row.pop("Valor Referencial (mil R$)")),
            ordenacao=int(row.pop("OrderCol")),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "data": self.data,
            "mercado": self.mercado,
            "contratos": self.contratos,
            "valor_milhares": self.valor_milhares,
            "ordenacao": self.ordenacao,
        }


@dataclass
class Swap:
    codigo: str
    vencimento: datetime.date
    negocios: int
    volume: Decimal
    taxa_media_diaria: Decimal

    @classmethod
    def from_dict(cls, row):
        key = "Vencimento"
        if key in row:
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            codigo=row.pop("Código"),
            vencimento=row.pop("Vencimento"),
            negocios=int(row.pop("Número de negócios")),
            volume=parse_decimal(row.pop("Volume (R$)")),
            taxa_media_diaria=parse_decimal(row.pop("Taxa média diária"), places=4),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "codigo": self.codigo,
            "vencimento": self.vencimento,
            "negocios": self.negocios,
            "volume": self.volume,
            "taxa_media_diaria": self.taxa_media_diaria,
        }


@dataclass
class AcaoCustodiada:
    empresa: str
    tipo: str
    quantidade: int

    @classmethod
    def from_dict(cls, row):
        obj = cls(
            empresa=row.pop("Empresa"),
            tipo=row.pop("Tipo"),
            quantidade=row.pop("Quantidade de ações"),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "empresa": self.empresa,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
        }


@dataclass
class CreditoProvento:
    emissor: str
    codigo_isin: str
    tipo: str
    data_aprovacao: datetime.date
    valor: Decimal
    data_credito: datetime.date

    @classmethod
    def from_dict(cls, row):
        for key in ("Data de aprovação", "Data de crédito"):
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            emissor=row.pop("Emissor"),
            codigo_isin=row.pop("Código ISIN"),
            tipo=row.pop("Tipo de provento"),
            data_aprovacao=row.pop("Data de aprovação"),
            data_credito=row.pop("Data de crédito"),
            valor=parse_decimal(row.pop("Valor (R$)")),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "emissor": self.emissor,
            "codigo_isin": self.codigo_isin,
            "tipo": self.tipo,
            "data_aprovacao": self.data_aprovacao,
            "valor": self.valor,
            "data_credito": self.data_credito,
        }


@dataclass
class CustodiaFungivel:
    prazo_final_subscricao: datetime.date
    prazo_final_cessao: datetime.date
    emissor: str
    codigo_isin_origem: str
    codigo_isin_direito: str
    codigo_isin_subscricao: str

    @classmethod
    def from_dict(cls, row):
        for key in ("Prazo final subscrição", "Prazo final cessão"):
            assert row[key].endswith("T00:00:00"), f"Data para coluna {key} em formato inválido: {repr(row[key])}"
            row[key] = parse_iso_date(row[key].replace("T00:00:00", ""))
        obj = cls(
            prazo_final_subscricao=row.pop("Prazo final subscrição"),
            prazo_final_cessao=row.pop("Prazo final cessão"),
            emissor=row.pop("Emissor"),
            codigo_isin_origem=row.pop("Código ISIN origem"),
            codigo_isin_direito=row.pop("Código ISIN direito"),
            codigo_isin_subscricao=row.pop("Código ISIN subscrição"),
        )
        assert not row, f"Dados sobraram e não foram extraídos para {cls.__name__}: {row}"
        return obj

    def serialize(self):
        return {
            "prazo_final_subscricao": self.prazo_final_subscricao,
            "prazo_final_cessao": self.prazo_final_cessao,
            "emissor": self.emissor,
            "codigo_isin_origem": self.codigo_isin_origem,
            "codigo_isin_direito": self.codigo_isin_direito,
            "codigo_isin_subscricao": self.codigo_isin_subscricao,
        }


class B3:
    _funds_call_url = "https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/"
    _indexes_stats_url = "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/"
    _indexes_call_url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/"
    _companies_call_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
    indices = (
        "AGFS BDRX GPTW IBBC IBBE IBBR IBEE IBEP IBEW IBHB IBLV IBOVESPA IBRA IBSD IBXL IBXX ICO2 ICON IDIV IDVR IEEX "
        "IFIL IFIX IFNC IGCT IGCX IGNM IMAT IMOB INDX ISEE ITAG IVBX MLCX SMLL UTIL".split()
    )
    # TODO: (talvez, se possível) criar método para listar todos os índices programaticamente a partir de scraping
    _carteira_indice_periodos = ("dia", "teórica", "próxima")

    def __init__(self, user_agent: str = USER_AGENT, proxy: str | None = None, timeout: float = 15.0) -> None:
        self.session = create_session(user_agent=user_agent, proxy=proxy)
        self.timeout = timeout
        # Requisição para guardar cookies:
        self.request(
            "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/fundos-de-investimento-imobiliario-fii.htm",
            decode_json=False,
        )

    def _make_url_params(self, params):
        return base64.b64encode(json.dumps(params, separators=(",", ":")).encode("utf-8")).decode("ascii")

    def url_negociacao_bolsa(self, frequencia: str, data: datetime.date):
        """
        :param frequencia: deve ser "dia", "mês" ou "ano"
        :param data: data desejada (use o dia "01" caso frequência seja "mês" e o dia e mês "01" caso frequência seja
        "ano")
        """
        # TODO: aceitar datetime.date ou str (iso format)
        if frequencia == "dia":
            date = data.strftime("%d%m%Y")
            return f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_D{date}.ZIP"
        elif frequencia == "mês":
            date = data.strftime("%m%Y")
            return f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_M{date}.ZIP"
        elif frequencia == "ano":
            date = data.strftime("%Y")
            return f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{date}.ZIP"

    def negociacao_bolsa(self, frequencia: str, data: datetime.date):
        """
        Baixa cotação para uma determinada data (dia, mês ou ano)

        :param frequencia: deve ser "dia", "mês" ou "ano"
        :param data: data das cotações a serem baixadas (use o dia "01" caso frequência seja "mês" e o dia e mês "01"
        caso frequência seja "ano")

        Horários de atualização, de acordo com meus testes:
        - Diária: 23:31:45 GMT
        - Mensal: 00:20:56 GMT
        - Anual: 23:32:31 GMT
        """
        # TODO: aceitar datetime.date ou str (iso format)
        assert frequencia in ("dia", "mês", "ano")

        url = self.url_negociacao_bolsa(frequencia, data)
        # TODO: salvar arquivo em cache
        response = self.session.get(url, verify=False, timeout=self.timeout)
        if len(response.content) == 0:  # Arquivo vazio (provavelmente dia sem pregão)
            return ValueError(
                f"Data {data} possui arquivo de cotação vazio (provavelmente não teve pregão ou data no futuro)"
            )
        zf = ZipFile(io.BytesIO(response.content))
        if len(zf.filelist) != 1:
            filenames = ", ".join(sorted(info.filename for info in zf.filelist))
            raise RuntimeError(
                f"Esperado apenas um arquivo dentro do ZIP de negociação em bolsa, encontrados: {filenames}"
            )
        fobj = io.TextIOWrapper(zf.open(zf.filelist[0].filename), encoding="iso-8859-1")
        for line in fobj:
            if line[:2] != "01":  # Não é um registro de fato
                continue
            yield NegociacaoBolsa.from_line(line)

    def url_intradiaria_zip(self, data: datetime.date):
        # <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/cotacoes/>
        # TODO: aceitar datetime.date ou str (iso format)
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://arquivos.b3.com.br/rapinegocios/tickercsv/{data_str}"
        return url

    def _le_zip_intradiaria(self, fobj):
        zf = ZipFile(fobj)
        if len(zf.filelist) != 1:
            filenames = ", ".join(sorted(info.filename for info in zf.filelist))
            raise RuntimeError(
                f"Esperado apenas um arquivo dentro do ZIP de negociações intradiárias, encontrados: {filenames}"
            )
        filename = zf.filelist[0].filename
        assert "_NEGOCIOSAVISTA.txt" in filename
        fobj = io.TextIOWrapper(zf.open(zf.filelist[0].filename), encoding="iso-8859-1")
        for row in csv.DictReader(fobj, delimiter=";"):
            yield NegociacaoIntradiaria.from_dict(row)

    def negociacao_intradiaria(self, data: datetime.date):
        # TODO: aceitar datetime.date ou str (iso format)
        url = self.url_intradiaria_zip(data)
        # TODO: salvar arquivo em cache
        response = self.session.get(url, timeout=self.timeout)
        yield from self._le_zip_intradiaria(io.BytesIO(response.content))

    def request(
        self,
        url,
        url_params=None,
        params=None,
        method="GET",
        timeout=None,
        decode_json=True,
        verify_ssl=False,
        json_data=None,
        max_tries=5,
        wait_between_errors=0.5,
    ):
        if url_params is not None:
            url_params = self._make_url_params(url_params)
            url = urljoin(url, url_params)
        if timeout is None:
            timeout = self.timeout
        tried = 0
        while tried < max_tries:
            # São feitas múltiplas tentativas porque recorrentemente os servidores da CloudFlare respondem com erro
            # HTTP 520.
            response = self.session.request(
                method, url, params=params, timeout=timeout, verify=verify_ssl, json=json_data
            )
            tried += 1
            if response.status_code < 500:
                break
            else:
                time.sleep(wait_between_errors)
        if decode_json:
            text = response.text
            if text and text[0] == text[-1] == '"':  # WTF, B3?
                text = json_decode(text)
            return json_decode(text) if text else {}
        return response

    def paginate(self, base_url, url_params=None, params=None, method="GET"):
        url_params = url_params or {}
        if "pageNumber" not in url_params:
            url_params["pageNumber"] = 1
        if "pageSize" not in url_params:
            url_params["pageSize"] = 100
        finished = False
        while not finished:
            response = self.request(base_url, url_params, params=params, method=method)
            if isinstance(response, list):
                yield from response
                finished = True
            elif isinstance(response, dict):
                if "results" in response:
                    yield from response["results"]
                    finished = url_params["pageNumber"] >= response["page"]["totalPages"]
                    url_params["pageNumber"] += 1
                else:
                    yield response

    def _fundos_listados_por_tipo(self, tipo, detalhe=True):
        objs = self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListFunds/"),
            url_params={"language": "pt-br", "typeFund": tipo},
        )
        for obj in objs:
            if detalhe:
                yield self.fundo_listado_detalhe(tipo, obj["id"], obj["acronym"])
            else:
                yield FundoB3Resumido.from_dict(obj, tipo=tipo)

    def fundo_listado_detalhe(self, tipo, id_fnet, acronimo):
        response_data = self.request(
            method="GET",
            url=urljoin(self._funds_call_url, "GetDetailFund/"),
            url_params={"language": "pt-br", "idFNET": id_fnet, "idCEM": acronimo, "typeFund": tipo},
        )
        return FundoB3.from_dict(response_data)

    def fundo_listado_dividendos(self, acronimo):
        data = self.request(
            url=urljoin(self._funds_call_url, "GetEventsCorporateActions/"),
            url_params={"language": "pt-br", "idCEM": acronimo},
        )
        dividends = data.get("cashDividends") or [] if data else []
        return [Dividendo.from_dict(row) for row in dividends]

    # TODO: implement stockDividends

    def _fund_subscriptions(self, type_id, cnpj, identifier):
        # TODO: parse/convert to dataclass:
        # assetIssued	percentage	priceUnit	tradingPeriod	subscriptionDate	approvedOn	isinCode	label	lastDatePrior	remarks
        # BRAFHICTF005	31,33913825813	95,80000000000	31/12/9999 a 06/06/2024	11/06/2024	20/05/2024	BRAFHICTF005	SUBSCRICAO	23/05/2024
        # BRAFHICTF005	31,01981846164	96,43000000000	31/12/9999 a 24/01/2024	29/01/2024	08/01/2024	BRAFHICTF005	SUBSCRICAO	11/01/2024
        # BRAFHICTF005	20,66255046858	96,17000000000	31/12/9999 a 02/08/2023	07/08/2023	18/07/2023	BRAFHICTF005	SUBSCRICAO	21/07/2023
        # BRALZCCTF016	128,40431952130	100,51000000000	31/12/9999 a 27/05/2024	31/05/2024	10/05/2024	BRALZCCTF016	SUBSCRICAO	15/05/2024

        return self.request(
            url=urljoin(self._funds_call_url, "GetListedSupplementFunds/"),
            url_params={"cnpj": cnpj, "identifierFund": identifier, "typeFund": type_id},
        )["subscriptions"]

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def _fundo_comunicados(self, identificador):
        "Comunicados"
        result = self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedPreviousDocuments/"),
            url_params={"identifierFund": identificador, "type": 1},
        )
        for row in result:
            yield FundoDocumento.from_dict(identificador, row)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def _fundo_demonstrativos(self, identificador):
        "Demonstrativos financeiros e relatórios"
        result = self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedPreviousDocuments/"),
            url_params={"identifierFund": identificador, "type": 2},
        )
        for row in result:
            yield FundoDocumento.from_dict(identificador, row)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def _fundo_outros_documentos(self, identificador):
        "Demonstrativos financeiros e relatórios"
        result = self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedPreviousDocuments/"),
            url_params={"identifierFund": identificador, "type": 3},
        )
        for row in result:
            yield FundoDocumento.from_dict(identificador, row)

    def _fund_documents(self, type_id, cnpj, identifier, start_date: datetime.date, end_date: datetime.date):
        # TODO: aceitar datetime.date ou str (iso format)
        # TODO: parse/convert to dataclass:
        iterator = self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedDocuments/"),
            url_params={
                "identifierFund": identifier,
                "typeFund": type_id,
                "cnpj": cnpj,
                "dateInitial": start_date.strftime("%Y-%m-%d"),
                "dateFinal": end_date.strftime("%Y-%m-%d"),
            },
        )
        for row in iterator:
            yield row

    # TODO: GetListedHeadLines/ b'{"agency":"18","identifierFund":"CPTR","dateInitial":"2023-06-10","dateFinal":"2024-06-05"}'
    # TODO: GetListedByType/ b'{"cnpj":"42537579000176","identifierFund":"CPTR","typeFund":34,"dateInitial":"2024-01-01","dateFinal":"2024-12-31"}'
    # TODO: GetListedCategory/ b'{"cnpj":"42537579000176"}'
    # TODO: GetListedDocuments/ b'{"pageNumber":1,"pageSize":4,"cnpj":"42537579000176","identifierFund":"CPTR","typeFund":34,"dateInitial":"2024-01-01","dateFinal":"2024-12-31","category":7}'

    def _empresa_detalhe_raw(self, codigo_cvm):
        # TODO: para vários códigos CVM, o valor retornado é `{}`, como: 900049, 916478, 900242, 916304. Verificar se é
        # possível pegar essas informações diretamente da CVM.
        return self.request(
            urljoin(self._companies_call_url, "GetDetail/"),
            url_params={"codeCVM": codigo_cvm, "language": "pt-br"},
        )

    def empresas(self, detalhe=False):
        """Devolve as empresas listadas na B3"""
        # TODO: checar se inclui BDRs patrocinados e não patrocinados
        lista = self.paginate(
            base_url=urljoin(self._companies_call_url, "GetInitialCompanies/"),
            url_params={"language": "pt-br"},
        )
        if not detalhe:
            for row in lista:
                yield Empresa.from_dict(row)
        else:
            # TODO: executar em paralelo?
            for row in lista:
                empresa_detalhe = self._empresa_detalhe_raw(row["codeCVM"])
                yield Empresa.from_dict(row, detalhe=empresa_detalhe)

    def empresa_detalhe(self, codigo_cvm):
        """
        Coleta detalhes da empresa, porém sem alguns campos

        Apesar de ter mais detalhes que as empresas retornadas em `empresas(detalhes=False)`, esse endpoint não tem os
        seguinetes campos: 'dateListing', 'segment', 'segmentEng' e 'type'. Agradeça à B3 pela consistência.
        ATENÇÃO: esse método não vai funcionar para empresas que retornam os detalhes em branco.
        """
        detalhe = self._empresa_detalhe_raw(codigo_cvm)
        return Empresa.from_dict(None, detalhe=detalhe)

    def bdrs(self):
        """Devolve os BDRs listados na B3"""
        # TODO: retornar dataclass
        return self.paginate(
            base_url=urljoin(self._companies_call_url, "GetCompaniesBDR/"),
            url_params={"language": "pt-br"},
        )

    def etfs(self, detalhe=False):
        """Devolve os ETFs listados na B3 (incluindo os de renda fixa)"""
        # TODO: corrigir `None` em `data_aprovacao_cotas = parse_br_date(clean_string(data.pop("quotaDateApproved")))`
        yield from self._fundos_listados_por_tipo("ETF", detalhe=detalhe)
        yield from self._fundos_listados_por_tipo("ETF-RF", detalhe=detalhe)

    def fiis(self, detalhe=False):
        """Devolve os FIIs listados na B3"""
        yield from self._fundos_listados_por_tipo("FII", detalhe=detalhe)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fii_detail(self, fundo_id, identificador):
        return self.fundo_listado_detalhe("FII", fundo_id, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fii_dividends(self, identificador):
        return self.fundo_listado_dividendos(identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fii_subscriptions(self, cnpj, identificador):
        # TODO: Corrigir: `KeyError: 'subscriptions'`
        return self._fund_subscriptions(7, cnpj, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fii_documents(self, cnpj, identificador, data_inicial: datetime.date = None, data_final: datetime.date = None):
        # TODO: aceitar datetime.date ou str (iso format)
        today = datetime.datetime.now()
        if data_inicial is None:
            data_inicial = (today - datetime.timedelta(days=365)).date()
        if data_final is None:
            data_final = today.date()
        yield from self._fund_documents(7, cnpj, identificador, data_inicial, data_final)

    def fiinfras(self, detalhe=False):
        """Devolve os FI-Infras listados na B3"""
        yield from self._fundos_listados_por_tipo("FI-Infra", detalhe=detalhe)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiinfra_detail(self, fundo_id, identificador):
        return self.fundo_listado_detalhe("FI-Infra", fundo_id, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiinfra_dividends(self, identificador):
        return self.fundo_listado_dividendos(identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiinfra_subscriptions(self, cnpj, identificador):
        # TODO: não está funcionando: KeyError: 'subscriptions'
        return self._fund_subscriptions(27, cnpj, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiinfra_documents(
        self, cnpj, identificador, data_inicial: datetime.date = None, data_final: datetime.date = None
    ):
        today = datetime.datetime.now()
        if data_inicial is None:
            data_inicial = (today - datetime.timedelta(days=365)).date()
        if data_final is None:
            data_final = today.date()
        yield from self._fund_documents(27, cnpj, identificador, data_inicial, data_final)

    def fips(self, detalhe=False):
        """Devolve os FIPs listados na B3"""
        yield from self._fundos_listados_por_tipo("FIP", detalhe=detalhe)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fip_detail(self, fundo_id, identificador):
        return self.fundo_listado_detalhe("FIP", fundo_id, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fip_dividends(self, identificador):
        return self.fundo_listado_dividendos(identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fip_subscriptions(self, cnpj, identificador):
        # TODO: não está funcionando: KeyError: 'subscriptions'
        return self._fund_subscriptions(21, cnpj, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fip_documents(self, cnpj, identificador, data_inicial: datetime.date = None, data_final: datetime.date = None):
        # TODO: aceitar datetime.date ou str (iso format)
        today = datetime.datetime.now()
        if data_inicial is None:
            data_inicial = (today - datetime.timedelta(days=365)).date()
        if data_final is None:
            data_final = today.date()
        yield from self._fund_documents(21, cnpj, identificador, data_inicial, data_final)

    def fiagros(self, detalhe=False):
        """Devolve os FI-Agros listados na B3"""
        yield from self._fundos_listados_por_tipo("FIAGRO", detalhe=detalhe)
        yield from self._fundos_listados_por_tipo("FIAGRO-FII", detalhe=detalhe)
        yield from self._fundos_listados_por_tipo("FIAGRO-FIDC", detalhe=detalhe)
        yield from self._fundos_listados_por_tipo("FIAGRO-FIP", detalhe=detalhe)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiagro_detail(self, fundo_id, identificador):
        return self.fundo_listado_detalhe("FIAGRO-FII", fundo_id, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiagro_dividends(self, identificador):
        return self.fundo_listado_dividendos(identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiagro_subscriptions(self, cnpj, identificador):
        # TODO: não está funcionando: KeyError: 'subscriptions'
        return self._fund_subscriptions(34, cnpj, identificador)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fiagro_documents(
        self, cnpj, identificador, data_inicial: datetime.date = None, data_final: datetime.date = None
    ):
        today = datetime.datetime.now()
        if data_inicial is None:
            data_inicial = (today - datetime.timedelta(days=365)).date()
        if data_final is None:
            data_final = today.date()
        yield from self._fund_documents(34, cnpj, identificador, data_inicial, data_final)

    def fidcs(self, detalhe=False):
        """Devolve os FIDCs listados na B3"""
        yield from self._fundos_listados_por_tipo("FIDC", detalhe=detalhe)

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def fidc_detail(self, fundo_id, identificador):
        return self.fundo_listado_detalhe("FIDC", fundo_id, identificador)

    def securitizadoras(self):
        # TODO: página não encontrada (deve ter sido migrada)
        yield from self.paginate(urljoin(self._funds_call_url, "GetListedSecuritization/"))

    def cris(self, cnpj_securitizadora):
        yield from self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedCertified/"),
            url_params={"dateInitial": "", "cnpj": cnpj_securitizadora, "type": "CRI"},
        )

    def cras(self, cnpj_securitizadora):
        yield from self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedCertified/"),
            url_params={"dateInitial": "", "cnpj": cnpj_securitizadora, "type": "CRA"},
        )

    # TODO: renomear identificador para um nome mais específico (acronimo, id_fnet, cnpj etc.)
    def certificate_documents(self, identificador, start_date: datetime.date, end_date: datetime.date):  # CRI or CRA
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self.paginate(
            base_url=urljoin(self._funds_call_url, "GetListedDocumentsTypeHistory/"),
            url_params={
                "cnpj": identificador,
                "dateInitial": start_date.strftime("%Y-%m-%d"),
                "dateFinal": end_date.strftime("%Y-%m-%d"),
            },
        )

    def debentures(self):
        response = self.request(
            "https://sistemaswebb3-balcao.b3.com.br/featuresDebenturesProxy/DebenturesCall/GetDownload",
            decode_json=False,
        )
        decoded_data = base64.b64decode(response.text).decode("ISO-8859-1")
        reader = csv.DictReader(io.StringIO(decoded_data), delimiter=";")
        yield from reader

    def negociacao_balcao(self, date):
        response = self.request(
            "https://bvmf.bmfbovespa.com.br/NegociosRealizados/Registro/DownloadArquivoDiretorio",
            params={"data": date.strftime("%d-%m-%Y")},
            decode_json=False,
        )
        if response.status_code == 404:  # No data for this date
            return
        decoded_data = base64.b64decode(response.text).decode("ISO-8859-1")
        csv_data = decoded_data[decoded_data.find("\n") + 1 :]
        reader = csv.DictReader(io.StringIO(csv_data), delimiter=";")
        for row in reader:
            for field in ("Cod. Isin", "Data Liquidacao"):
                if field not in row:
                    row[field] = None
            yield NegociacaoBalcao.from_dict(row)

    def valor_indice(self, indice: str, ano: int):
        if indice not in self.indices:
            # TODO: testar IDAP5 e ICBIO
            raise ValueError(f"Índice desconhecido: {repr(indice)}")
        response = self.request(
            urljoin(self._indexes_stats_url, "GetPortfolioDay/"),
            url_params={"index": indice, "language": "pt-br", "year": ano},
            decode_json=True,
        )
        dados = []
        for valor_dia in response["results"]:
            dia = valor_dia.pop("day")
            for mes in range(1, 12 + 1):
                valor_mes = valor_dia.pop(f"rateValue{mes}")
                if valor_mes is not None:
                    dados.append(Taxa(data=datetime.date(ano, mes, dia), valor=parse_br_decimal(valor_mes)))
            if valor_dia:
                raise RuntimeError(f"Dados não extraídos: {repr(valor_dia)}")
        dados.sort(key=lambda row: row.data)
        return dados

    def carteira_indice(self, indice, periodo):
        # TODO: adicionar checagem de índices. ATENÇÃO: a lista de strings não é a mesma de `valor_indice`, por
        # exemplo: IBOV (carteira_indice) é IBOVESPA (valor_indice). Obrigado B3 mais uma vez pela consistência. :|
        # XXX: a carteira "próxima" muitas vezes é igual à teórica (provavelmente somente pouco antes do
        # rebalanceamento é que ela é atualizada).
        if periodo not in self._carteira_indice_periodos:
            raise ValueError(f"Período {repr(periodo)} inválido. Use: {', '.join(self._carteira_indice_periodos)}")

        items = []

        if periodo == "dia":
            # TODO: por que não paginar?
            response = self.request(
                urljoin(self._indexes_call_url, "GetPortfolioDay/"),
                url_params={"language": "pt-br", "index": indice, "segment": "1", "pageNumber": 1, "pageSize": 120},
                decode_json=True,
            )
            assert response["page"]["totalPages"] == 1, f"Número de páginas diferente do esperado: {response['page']}"
            for row in response["results"]:
                items.append(
                    AtivoIndice(
                        codigo_negociacao=row["cod"],
                        ativo=row["asset"],
                        tipo=row["type"],
                        qtd_teorica=parse_br_decimal(row["theoricalQty"]),
                        participacao=parse_br_decimal(row["part"]),
                    )
                )

        elif periodo == "teórica":
            # TODO: por que não paginar?
            response = self.request(
                urljoin(self._indexes_call_url, "GetTheoricalPortfolio/"),
                url_params={"language": "pt-br", "index": indice, "pageNumber": 1, "pageSize": 120},
                decode_json=True,
            )
            assert response["page"]["totalPages"] == 1, f"Número de páginas diferente do esperado: {response['page']}"
            for row in response["results"]:
                items.append(
                    AtivoIndice(
                        codigo_negociacao=row["cod"],
                        ativo=row["asset"],
                        tipo=row["type"],
                        qtd_teorica=parse_br_decimal(row["theoricalQty"]),
                        participacao=parse_br_decimal(row["part"]),
                    )
                )

        elif periodo == "próxima":
            # TODO: por que não paginar?
            response = self.request(
                urljoin(self._indexes_call_url, "GetQuartelyPreview/"),
                url_params={"language": "pt-br", "index": indice, "pageNumber": 1, "pageSize": 120},
                decode_json=True,
            )
            assert response["page"]["totalPages"] == 1, f"Número de páginas diferente do esperado: {response['page']}"
            for row in response["results"]:
                items.append(
                    AtivoIndice(
                        codigo_negociacao=row["cod"],
                        ativo=row["asset"],
                        tipo=row["type"],
                        qtd_teorica=parse_br_decimal(row["theoricalQty"]),
                        participacao=parse_br_decimal(row["part"]),
                    )
                )
        header = response["header"]
        items.extend(
            [
                AtivoIndice(
                    codigo_negociacao="Quantidade Teórica Total",
                    ativo="",
                    tipo="",
                    qtd_teorica=parse_br_decimal(header["theoricalQty"]),
                    participacao=parse_br_decimal(header["part"]),
                ),
                AtivoIndice(
                    codigo_negociacao="Redutor",
                    ativo="",
                    tipo="",
                    qtd_teorica=parse_br_decimal(header["reductor"]),
                    participacao=None,
                ),
            ]
        )
        items.sort(key=lambda row: row.participacao or 0, reverse=True)
        return items

    # def carteira_indice_historica(self, indice, ano: int):
    #     # TODO: ano não funciona!
    #     response = self.request(
    #         url=urljoin(self._indexes_call_url, "GetDownloadPortfolioDay/"),
    #         url_params={"language": "pt-br", "index": indice, "year": ano},
    #         decode_json=False
    #     )
    #     csv_data = response.content
    #     if csv_data[0:1] == csv_data[-1:] == b'"':  # WTF, B3?
    #         csv_data = base64.b64decode(csv_data[1:-1])
    #     with io.StringIO(csv_data.decode("iso-8859-1")) as fobj:
    #         _ = fobj.readline()  # Skip first line
    #         for row in csv.DictReader(fobj, delimiter=";"):
    #             yield AtivoIndice(
    #                 codigo_negociacao=row["Código"],
    #                 ativo=row["Ação"],
    #                 tipo=row["Tipo"],
    #                 qtd_teorica=parse_br_decimal(row["Qtde. Teórica"]),
    #                 participacao=parse_br_decimal(row["Part. (%)"]),
    #             )

    def _tabela_clearing(self, url_template, url_params, query_params, json_data=None, data_class=None):
        """
        Baixa dados de Clearing do Boletim do Mercado da B3

        <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/boletim-diario-do-mercado/>
        """
        page, page_size = 1, 1000
        json_data = json_data if json_data is not None else {}
        finished = False
        while not finished:
            url = url_template.format(page=page, page_size=page_size, **url_params)
            data = self.request(url, params=query_params, method="POST", json_data=json_data, decode_json=True)
            table = data["table"]
            header = [col["friendlyNamePt"] or col["name"] for col in table["columns"]]
            for item in table["values"]:
                row = dict(zip(header, item))
                if data_class is not None:
                    yield data_class.from_dict(row)
                else:
                    yield row
            finished = table["pageCount"] == page or len(table["values"]) == 0
            page += 1

    def clearing_acoes_custodiadas(self, data_inicial: datetime.date):
        """Clearing - Ações Custodiadas"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/Custody/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data_inicial.isoformat(), "data_final": data_inicial.isoformat()},
            query_params={"sort": "TckrSymb"},
            data_class=AcaoCustodiada,
        )

    def clearing_creditos_de_proventos(self, data_inicial: datetime.date, filtro_emissor=None):
        """Clearing - Créditos de Proventos - Renda Variável"""
        # TODO: aceitar datetime.date ou str (iso format)
        query_params = {"sort": "TckrSymb"}
        if filtro_emissor is not None:
            query_params["filter"] = base64.b64encode(filtro_emissor.encode("utf-8")).decode("ascii")
        # TODO: corrigir 'Data de aprovação': AttributeError: 'NoneType' object has no attribute 'endswith'
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/ProventionCreditVariable/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data_inicial.isoformat(), "data_final": data_inicial.isoformat()},
            query_params=query_params,
            data_class=CreditoProvento,
        )

    def clearing_custodia_fungivel(self, data: datetime.date):
        """Clearing - Custódia Fungível"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/FugibleCustody/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params={"sort": "TckrSymb"},
            data_class=CustodiaFungivel,
        )

    def clearing_emprestimos_registrados(
        self, data_inicial: datetime.date, data_final: datetime.date, codigo_negociacao=None
    ):
        """Clearing - Empréstimos de Ativos - Empréstimos Registrados"""
        # TODO: aceitar datetime.date ou str (iso format)
        query_params = {"sort": "TckrSymb"}
        if codigo_negociacao is not None:
            query_params["filter"] = base64.b64encode(codigo_negociacao.encode("utf-8")).decode("ascii")
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/BTBLoanBalance/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data_inicial.isoformat(), "data_final": data_final.isoformat()},
            query_params=query_params,
            data_class=EmprestimoAtivo,
        )

    def clearing_emprestimos_negociados(
        self, data: datetime.date, filtro_tomador=None, filtro_doador=None, filtro_mercado=None, codigo_negociacao=None
    ):
        """Clearing - Empréstimos de Ativos - Negócios"""
        # TODO: aceitar datetime.date ou str (iso format)
        query_params = {"sort": "TckrSymb"}
        json_data = {}
        if filtro_tomador is not None:
            json_data["EntryBuyerNm"] = filtro_tomador
        if filtro_doador is not None:
            json_data["EntrySellerNm"] = filtro_doador
        if filtro_mercado is not None:
            json_data["MarketBTB"] = filtro_mercado
        if codigo_negociacao is not None:
            query_params["filter"] = base64.b64encode(codigo_negociacao.encode("utf-8")).decode("ascii")
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/BTBTrade/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params=query_params,
            json_data=json_data,
            data_class=EmprestimoNegociado,
        )

    def clearing_filtros_emprestimos_negociados(self, data: datetime.date):
        """Lista valores disponíveis para filtros de empréstimos negociados"""
        # TODO: aceitar datetime.date ou str (iso format)
        data = data.isoformat()
        return self.request(f"https://arquivos.b3.com.br/bdi/table/BTBTrade/{data}/{data}/filters")

    def clearing_emprestimos_em_aberto(
        self, data_inicial: datetime.date, data_final: datetime.date, filtro_mercado=None, codigo_negociacao=None
    ):
        """Clearing - Empréstimos de Ativos - Posições em Aberto"""
        # TODO: aceitar datetime.date ou str (iso format)
        query_params = {"sort": "TckrSymb"}
        if codigo_negociacao is not None:
            query_params["filter"] = base64.b64encode(codigo_negociacao.encode("utf-8")).decode("ascii")
        json_data = {}
        if filtro_mercado is not None:
            json_data["Market"] = filtro_mercado
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data_inicial.isoformat(), "data_final": data_final.isoformat()},
            query_params=query_params,
            json_data=json_data,
            data_class=EmprestimoEmAberto,
        )

    def clearing_filtros_emprestimos_em_aberto(self, data_inicial: datetime.date, data_final: datetime.date):
        """Lista valores disponíveis para filtros de empréstimos em aberto"""
        # TODO: aceitar datetime.date ou str (iso format)
        data_inicial = data_inicial.isoformat()
        data_final = data_final.isoformat()
        return self.request(
            f"https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition/{data_inicial}/{data_final}/filters"
        )

    def clearing_opcoes_flexiveis(self, data: datetime.date, codigo_negociacao=None):
        """Clearing - Opções Flexíveis"""
        # TODO: aceitar datetime.date ou str (iso format)
        query_params = {"sort": "TckrSymb"}
        if codigo_negociacao is not None:
            query_params["filter"] = base64.b64encode(codigo_negociacao.encode("utf-8")).decode("ascii")
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/FlexibleOptions/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params=query_params,
            data_class=OpcaoFlexivel,
        )

    def clearing_prazo_deposito_titulos(self, data: datetime.date):
        """Clearing - Prazo para Depósito de Títulos"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/DeadlineDepositSecurities/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params={"sort": "TckrSymb"},
            data_class=PrazoDeposito,
        )

    def clearing_posicoes_em_aberto(self, data: datetime.date):
        """Clearing - Quadro Analítico das Posições em Aberto"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/AnalyticalFramework/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params={"sort": "TckrSymb"},
            data_class=PosicaoEmAberto,
        )

    def clearing_swap(self, data: datetime.date):
        """Clearing - Swap"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/SwapFlex/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params={"sort": "TckrSymb"},
            data_class=Swap,
        )

    def clearing_termo_eletronico(self, data: datetime.date):
        """Clearing - Termo Eletrônico"""
        # TODO: aceitar datetime.date ou str (iso format)
        yield from self._tabela_clearing(
            url_template="https://arquivos.b3.com.br/bdi/table/EletronicTerm/{data_inicial}/{data_final}/{page}/{page_size}",
            url_params={"data_inicial": data.isoformat(), "data_final": data.isoformat()},
            query_params={"sort": "TckrSymb"},
        )

    def ultimas_cotacoes(self, codigo_negociacao):
        """Baixa as cotações para o último pregão para um determinado ativo, com atraso de 15min

        Os preços ficam disponíveis a cada intervalo de 5 minutos e são os de fechamento de cada instante de tempo.
        API acessível pela página <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/outros-ativos.htm>
        """
        url = f"https://cotacao.b3.com.br/mds/api/v1/DailyFluctuationHistory/{codigo_negociacao}"
        response = self.request(url, decode_json=True, verify_ssl=False)
        data = parse_date("iso-date", response["TradgFlr"]["date"])
        ticker = response["TradgFlr"]["scty"]["symb"]
        assert (
            ticker.lower().strip() == codigo_negociacao.lower().strip()
        ), f"Código negociação retornado diferente do fornecido: {repr(ticker)} vs {repr(codigo_negociacao)}"
        return [PrecoAtivo.from_dict(data, ticker, obj) for obj in response["TradgFlr"]["scty"]["lstQtn"]]

    # TODO: implementar valor de mercado das empresas
    # https://sistemaswebb3-listados.b3.com.br/marketValueProxy/marketValueCall/GetStockExchangeDaily/
    # {"language": "pt-br", "company": "", "keyword": ""}

    # TODO: lotes de negociação
    # https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/lotes-de-negociacao/

    # TODO: cadastro de instrumentos listados
    # https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/

    # TODO: opções - lista completa de séries autorizadas
    # https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/series-autorizadas/

    # TODO: pegar diversos dados históricos em https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/pesquisa-por-pregao/


def _configura_parser_cli(parser):
    from pathlib import Path

    comandos_padrao = {
        "bdr": "Coleta lista de BDRs",
        "cra-documents": "Coleta documentos publicados por CRAs",
        "cri-documents": "Coleta documentos publicados por CRIs",
        "debentures": "Coleta lista de debêntures",
        "fiagro-dividends": "Coleta dividendos de FI-Agros",
        "fiagro-documents": "Coleta lista de documentos publicados por FI-Agros",
        "fiagro-subscriptions": "Coleta histórico de subscrições de FI-Agros",
        "fii-dividends": "Coleta dividendos de FIIs",
        "fii-documents": "Coleta documentos publicados por FIIs",
        "fii-subscriptions": "Coleta histórico de subscrições de FIIs",
        "fiinfra-dividends": "Coleta dividendos de FI-Infras",
        "fiinfra-documents": "Coleta documentos publicados por FI-Infras",
        "fiinfra-subscriptions": "Coleta histórico de subscrições de FI-Infras",
        "fip-dividends": "Coleta dividendos de FIPs",
        "fip-documents": "Coleta documentos publicados por FIPs",
        "fip-subscriptions": "Coleta histórico de subscrições de FIPs",
        "fundo-listado": "Coleta fundos listados",
        "negociacao-balcao": "Coleta dados históricos de negociação em balcão",
    }
    subparsers = parser.add_subparsers(dest="comando", metavar="comando", required=True)
    for comando, descricao in comandos_padrao.items():
        subparser = subparsers.add_parser(comando, help=descricao)
        subparser.add_argument("-q", "--quiet", action="store_true", help="Não mostra mensagens de status")
        if comando == "fundo-listado":
            subparser.add_argument(
                "-d", "--detalhe", action="store_true", help="Baixa informações mais detalhadas dos fundos"
            )
        subparser.add_argument("csv_filename", type=Path, help="Nome do arquivo CSV a ser salvo")

    subparser = subparsers.add_parser("valor-indice", help="Coleta valores diários dos índices")
    subparser.add_argument(
        "indice",
        type=str,
        metavar="indice",
        choices=sorted(B3.indices),
        help=f"Código do índice na B3. Opções: {', '.join(sorted(B3.indices))}",
    )
    subparser.add_argument("ano", type=int)
    subparser.add_argument("csv_filename", type=Path, help="Nome do arquivo CSV a ser salvo")

    subparser = subparsers.add_parser("carteira-indice", help="Coleta ativos da carteira de um determinado índice")
    indices_carteira = list(B3.indices) + ["IBOV"]
    indices_carteira.remove("IBOVESPA")
    indices_carteira.sort()
    subparser.add_argument(
        "indice",
        type=str,
        metavar="indice",
        choices=indices_carteira,
        help=f"Código do índice na B3. Opções: {', '.join(sorted(indices_carteira))}",
    )
    subparser.add_argument(
        "periodo",
        type=str,
        metavar="periodo",
        choices=B3._carteira_indice_periodos,
        help=f"Período de validade da carteira. Opções: {', '.join(sorted(B3._carteira_indice_periodos))}",
    )
    subparser.add_argument("csv_filename", type=Path, help="Nome do arquivo CSV a ser salvo")

    subparser = subparsers.add_parser(
        "ultimas-cotacoes", help="Coleta cotação do último pregão para determinado ativo, com atraso de 15min"
    )
    subparser.add_argument("codigo_negociacao", type=str, help="Código de negociação do ativo na B3")
    subparser.add_argument("csv_filename", type=Path, help="Nome do arquivo CSV a ser salvo")

    subparser_negociacao_bolsa = subparsers.add_parser(
        "negociacao-bolsa", help="Coleta dados históricos consolidados por dia de negociação"
    )
    subparser_negociacao_bolsa.add_argument(
        "frequencia",
        type=str,
        metavar="frequencia",
        choices=["dia", "mês", "ano"],
        help="Frequência do arquivo de cotação disponível. Opções: dia, mês, ano",
    )
    subparser_negociacao_bolsa.add_argument(
        "data",
        type=parse_iso_date,
        help="Data a ser baixada no formato YYYY-MM-DD (para frequência mensal, use dia = 01, para anual use mês e dia = 01)",
    )
    subparser_negociacao_bolsa.add_argument("csv_filename", type=Path, help="Nome do arquivo CSV a ser salvo")

    subparser_baixar = subparsers.add_parser(
        "intradiaria-baixar", help="Baixa arquivo ZIP de negociações intradiárias para uma data."
    )
    subparser_baixar.add_argument(
        "-t", "--timeout", type=float, default=15.0, help="Tempo de timeout da requisição HTTP"
    )
    subparser_baixar.add_argument(
        "-c", "--chunk-size", type=int, default=256 * 1024, help="Tamanho do chunk no download"
    )
    subparser_baixar.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_baixar.add_argument("zip_filename", type=Path, help="Nome do arquivo ZIP a ser salvo")

    subparser_converter = subparsers.add_parser(
        "intradiaria-converter", help="Converte arquivo ZIP de negociações intradiárias para CSV."
    )
    subparser_converter.add_argument(
        "-c", "--codigo-negociacao", action="append", help="Filtra pelo código de negociação"
    )
    subparser_converter.add_argument(
        "zip_filename", type=Path, help="Nome do arquivo ZIP (já baixado) a ser convertido"
    )
    subparser_converter.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_acoes_custodiadas = subparsers.add_parser(
        "clearing-acoes-custodiadas", help="Coleta dados de Clearing - Ações Custodiadas"
    )
    subparser_clearing_acoes_custodiadas.add_argument(
        "data_inicial", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_acoes_custodiadas.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_creditos_de_proventos = subparsers.add_parser(
        "clearing-creditos-de-proventos", help="Coleta dados de Clearing - Créditos de Proventos - Renda Variável"
    )
    subparser_clearing_creditos_de_proventos.add_argument("-e", "--emissor", type=str, help="Filtra por emissor")
    subparser_clearing_creditos_de_proventos.add_argument(
        "data_inicial", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_creditos_de_proventos.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_custodia_fungivel = subparsers.add_parser(
        "clearing-custodia-fungivel", help="Coleta dados de Clearing - Custódia Fungível"
    )
    subparser_clearing_custodia_fungivel.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_clearing_custodia_fungivel.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_emprestimos_registrados = subparsers.add_parser(
        "clearing-emprestimos-registrados",
        help="Coleta dados de Clearing - Empréstimos de Ativos - Empréstimos Registrados",
    )
    subparser_clearing_emprestimos_registrados.add_argument(
        "-c", "--codigo-negociacao", type=str, help="Filtra por código de negociação"
    )
    subparser_clearing_emprestimos_registrados.add_argument(
        "data_inicial", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_emprestimos_registrados.add_argument(
        "data_final", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_emprestimos_registrados.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_emprestimos_negociados = subparsers.add_parser(
        "clearing-emprestimos-negociados", help="Coleta dados de Clearing - Empréstimos de Ativos - Negócios"
    )
    subparser_clearing_emprestimos_negociados.add_argument("-t", "--tomador", type=str, help="Filtra por tomador")
    subparser_clearing_emprestimos_negociados.add_argument("-d", "--doador", type=str, help="Filtra por doador")
    subparser_clearing_emprestimos_negociados.add_argument("-m", "--mercado", type=str, help="Filtra por mercado")
    subparser_clearing_emprestimos_negociados.add_argument(
        "-c", "--codigo-negociacao", type=str, help="Filtra por código de negociação"
    )
    subparser_clearing_emprestimos_negociados.add_argument(
        "data", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_emprestimos_negociados.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_emprestimos_em_aberto = subparsers.add_parser(
        "clearing-emprestimos-em-aberto", help="Coleta dados de Clearing - Empréstimos de Ativos - Posições em Aberto"
    )
    subparser_clearing_emprestimos_em_aberto.add_argument("-m", "--mercado", type=str, help="Filtra por mercado")
    subparser_clearing_emprestimos_em_aberto.add_argument(
        "-c", "--codigo-negociacao", type=str, help="Filtra por código de negociação"
    )
    subparser_clearing_emprestimos_em_aberto.add_argument(
        "data_inicial", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_emprestimos_em_aberto.add_argument(
        "data_final", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_emprestimos_em_aberto.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_opcoes_flexiveis = subparsers.add_parser(
        "clearing-opcoes-flexiveis", help="Coleta dados de Clearing - Opções Flexíveis"
    )
    subparser_clearing_opcoes_flexiveis.add_argument(
        "-c", "--codigo-negociacao", type=str, help="Filtra por código de negociação"
    )
    subparser_clearing_opcoes_flexiveis.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_clearing_opcoes_flexiveis.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_prazo_deposito_titulos = subparsers.add_parser(
        "clearing-prazo-deposito-titulos", help="Coleta dados de Clearing - Prazo para Depósito de Títulos"
    )
    subparser_clearing_prazo_deposito_titulos.add_argument(
        "data", type=parse_iso_date, help="Data no formato YYYY-MM-DD"
    )
    subparser_clearing_prazo_deposito_titulos.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_posicoes_em_aberto = subparsers.add_parser(
        "clearing-posicoes-em-aberto", help="Coleta dados de Clearing - Quadro Analítico das Posições em Aberto"
    )
    subparser_clearing_posicoes_em_aberto.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_clearing_posicoes_em_aberto.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_swap = subparsers.add_parser("clearing-swap", help="Coleta dados de Clearing - Swap")
    subparser_clearing_swap.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_clearing_swap.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")

    subparser_clearing_termo_eletronico = subparsers.add_parser(
        "clearing-termo-eletronico", help="Coleta dados de Clearing - Termo Eletrônico"
    )
    subparser_clearing_termo_eletronico.add_argument("data", type=parse_iso_date, help="Data no formato YYYY-MM-DD")
    subparser_clearing_termo_eletronico.add_argument("csv_filename", type=Path, help="Nome do CSV a ser criado")


def main(args):
    import datetime

    from mercados.utils import day_range

    TERM_CLEAR_LINE_FROM_CURSOR = "\x1b[K"
    b3 = B3()
    comando = args.comando
    csv_filename = getattr(args, "csv_filename", None)
    if csv_filename:
        csv_filename.parent.mkdir(parents=True, exist_ok=True)

    if comando == "bdr":
        quiet = args.quiet
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            if not quiet:
                print("\rBDR: ..." + TERM_CLEAR_LINE_FROM_CURSOR, end="", flush=True)
            for counter, row in enumerate(b3.bdrs(), start=1):
                if not quiet:
                    print(f"\rBDR: {counter:3}" + TERM_CLEAR_LINE_FROM_CURSOR, end="", flush=True)
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
            if not quiet:
                print(f"\rBDR: {counter:4}" + TERM_CLEAR_LINE_FROM_CURSOR, flush=True)

    elif comando == "cri-documents":
        current_year = datetime.datetime.now().year
        securitizadoras = b3.securitizadoras()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for securitizadora in securitizadoras:
                for cri in b3.cris(securitizadora["cnpj"]):
                    start_date = parse_date("iso-datetime-tz", cri["issueDate"])
                    base_row = {**securitizadora, **cri}
                    for year in range(start_date.year, current_year + 1):
                        start, stop = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
                        documents = list(
                            b3.certificate_documents(cri["identificationCode"], start_date=start, end_date=stop)
                        )
                        for doc in documents:
                            row = {**base_row, **doc}
                            if writer is None:
                                writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                                writer.writeheader()
                            writer.writerow(row)

    elif comando == "cra-documents":
        current_year = datetime.datetime.now().year
        securitizadoras = b3.securitizadoras()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for securitizadora in securitizadoras:
                for cra in b3.cras(securitizadora["cnpj"]):
                    start_date = parse_date("iso-datetime-tz", cra["issueDate"])
                    base_row = {**securitizadora, **cra}
                    for year in range(start_date.year, current_year + 1):
                        start, stop = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
                        documents = list(
                            b3.certificate_documents(cra["identificationCode"], start_date=start, end_date=stop)
                        )
                        for doc in documents:
                            row = {**base_row, **doc}
                            if writer is None:
                                writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                                writer.writeheader()
                            writer.writerow(row)

    elif comando == "fundo-listado":
        quiet = args.quiet
        detalhe = args.detalhe
        data_sources = (
            (b3.fiis(detalhe=detalhe), "FII"),
            (b3.fiinfras(detalhe=detalhe), "FI-Infra"),
            (b3.fips(detalhe=detalhe), "FIP"),
            (b3.fiagros(detalhe=detalhe), "FI-Agro"),
            (b3.fidcs(detalhe=detalhe), "FIDC"),
            (b3.etfs(detalhe=detalhe), "ETF"),
        )
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for iterator, tipo in data_sources:
                if not quiet:
                    print(f"\r{tipo:10}: ..." + TERM_CLEAR_LINE_FROM_CURSOR, end="", flush=True)
                for counter, obj in enumerate(iterator, start=1):
                    if not quiet:
                        print(f"\r{tipo:10}: {counter:4}" + TERM_CLEAR_LINE_FROM_CURSOR, end="", flush=True)
                    row = obj.serialize()
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                if not quiet:
                    print(f"\r{tipo:10}: {counter:4}" + TERM_CLEAR_LINE_FROM_CURSOR, flush=True)

    elif comando == "fii-dividends":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiis(detalhe=False):
                base_fund_data = obj.serialize()
                for dividend in b3.fii_dividends(identificador=obj.acronimo):
                    row = {**base_fund_data, **dividend.serialize()}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                    # TODO: include stock_dividends?

    elif comando == "fii-subscriptions":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiis(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fii_subscriptions(cnpj=obj.cnpj, identificador=obj.acronimo)
                for subscription in data:
                    row = {**base_fund_data, **subscription}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fii-documents":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiis(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fii_documents(identificador=obj.acronimo, cnpj=obj.cnpj)
                for doc in data:
                    row = {**base_fund_data, **doc}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fiinfra-dividends":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiinfras(detalhe=False):
                base_fund_data = obj.serialize()
                for dividend in b3.fiinfra_dividends(identificador=obj.acronimo):
                    row = {**base_fund_data, **dividend.serialize()}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                    # TODO: include stock_dividends?

    elif comando == "fiinfra-subscriptions":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiinfras(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fiinfra_subscriptions(cnpj=obj.cnpj, identificador=obj.acronimo)
                for subscription in data:
                    row = {**base_fund_data, **subscription}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fiinfra-documents":
        # TODO: o arquivo está ficando em branco, verificar
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiinfras(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fiinfra_documents(identificador=obj.acronimo, cnpj=obj.cnpj)
                for doc in data:
                    row = {**base_fund_data, **doc}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fiagro-dividends":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiagros(detalhe=False):
                base_fund_data = obj.serialize()
                for dividend in b3.fiagro_dividends(identificador=obj.acronimo):
                    row = {**base_fund_data, **dividend.serialize()}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                    # TODO: include stock_dividends?

    elif comando == "fiagro-subscriptions":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiagros(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fiagro_subscriptions(cnpj=obj.cnpj, identificador=obj.acronimo)
                for subscription in data:
                    row = {**base_fund_data, **subscription}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fiagro-documents":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fiagros(detalhe=True):
                base_fund_data = obj.serialize()
                data = b3.fiagro_documents(identificador=obj.acronimo, cnpj=obj.cnpj)
                for doc in data:
                    row = {**base_fund_data, **doc}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fip-dividends":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fips(detalhe=False):
                base_fund_data = obj.serialize()
                for dividend in b3.fip_dividends(identificador=obj.acronimo):
                    row = {**base_fund_data, **dividend.serialize()}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                    # TODO: include stock_dividends?

    elif comando == "fip-documents":
        # TODO: o arquivo está ficando em branco, verificar
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fips(detalhe=True):
                base_fund_data = obj.serialize()
                for doc in b3.fip_documents(identificador=obj.acronimo, cnpj=obj.cnpj):
                    row = {**base_fund_data, **doc}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "fip-subscriptions":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for obj in b3.fips(detalhe=True):
                base_fund_data = obj.serialize()
                for subscription in b3.fip_subscriptions(cnpj=obj.cnpj, identificador=obj.acronimo):
                    row = {**base_fund_data, **subscription}
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "debentures":
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.debentures():
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "negociacao-balcao":
        # TODO: adicionar opção de data inicial/data final
        today = datetime.datetime.now().date()
        start_date = datetime.date(today.year, 1, 1)
        end_date = today + datetime.timedelta(days=1)
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for date in day_range(start_date, end_date + datetime.timedelta(days=1)):
                for row in b3.negociacao_balcao(date):
                    row = row.serialize()
                    if writer is None:
                        writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)

    elif comando == "negociacao-bolsa":
        frequencia = args.frequencia
        data = args.data

        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.negociacao_bolsa(frequencia, data):
                row = row.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "intradiaria-baixar":
        data = args.data
        chunk_size = args.chunk_size
        zip_filename = args.zip_filename
        timeout = args.timeout
        zip_filename.parent.mkdir(parents=True, exist_ok=True)

        url = b3.url_intradiaria_zip(data)
        response = b3.session.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with zip_filename.open("wb") as fobj:
            for chunk in response.iter_content(chunk_size):
                fobj.write(chunk)

    elif comando == "intradiaria-converter":
        zip_filename = args.zip_filename
        zip_filename.parent.mkdir(parents=True, exist_ok=True)
        csv_filename = args.csv_filename
        filtro_codigo_negociacao = set(args.codigo_negociacao) if args.codigo_negociacao else None

        with csv_filename.open(mode="w") as fobj, zip_filename.open(mode="rb") as zip_fobj:
            writer = None
            for item in b3._le_zip_intradiaria(zip_fobj):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                if filtro_codigo_negociacao is None or item.codigo_negociacao in filtro_codigo_negociacao:
                    writer.writerow(row)

    elif comando == "clearing-acoes-custodiadas":
        data_inicial = args.data_inicial
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_acoes_custodiadas(data_inicial=data_inicial):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-creditos-de-proventos":
        data_inicial = args.data_inicial
        emissor = args.emissor
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_creditos_de_proventos(data_inicial=data_inicial, filtro_emissor=emissor):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-custodia-fungivel":
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_custodia_fungivel(data=data):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-emprestimos-registrados":
        data_inicial = args.data_inicial
        data_final = args.data_final
        codigo_negociacao = args.codigo_negociacao
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_emprestimos_registrados(
                data_inicial=data_inicial, data_final=data_final, codigo_negociacao=codigo_negociacao
            ):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-emprestimos-negociados":
        data = args.data
        tomador = args.tomador
        doador = args.doador
        mercado = args.mercado
        codigo_negociacao = args.codigo_negociacao
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_emprestimos_negociados(
                data=data,
                filtro_tomador=tomador,
                filtro_doador=doador,
                filtro_mercado=mercado,
                codigo_negociacao=codigo_negociacao,
            ):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-emprestimos-em-aberto":
        data_inicial = args.data_inicial
        data_final = args.data_final
        mercado = args.mercado
        codigo_negociacao = args.codigo_negociacao
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_emprestimos_em_aberto(
                data_inicial=data_inicial,
                data_final=data_final,
                filtro_mercado=mercado,
                codigo_negociacao=codigo_negociacao,
            ):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-opcoes-flexiveis":
        codigo_negociacao = args.codigo_negociacao
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_opcoes_flexiveis(data=data, codigo_negociacao=codigo_negociacao):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-prazo-deposito-titulos":
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_prazo_deposito_titulos(data=data):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-posicoes-em-aberto":
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_posicoes_em_aberto(data=data):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-swap":
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for item in b3.clearing_swap(data=data):
                row = item.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "clearing-termo-eletronico":
        data = args.data
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.clearing_termo_eletronico(data=data):
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "valor-indice":
        indice = args.indice
        ano = args.ano
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.valor_indice(indice=indice, ano=ano):
                row = row.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "carteira-indice":
        indice = args.indice
        periodo = args.periodo
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.carteira_indice(indice=indice, periodo=periodo):
                row = row.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif comando == "ultimas-cotacoes":
        codigo_negociacao = args.codigo_negociacao
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for row in b3.ultimas_cotacoes(codigo_negociacao=codigo_negociacao):
                row = row.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

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
