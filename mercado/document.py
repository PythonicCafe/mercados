import datetime
import decimal
from dataclasses import dataclass
from dataclasses import fields as class_fields
from functools import cached_property, lru_cache

import lxml.etree
from lxml.etree import fromstring as parse_xml
from rows.fields import camel_to_snake as rows_camel_to_snake

BRT = datetime.timezone(-datetime.timedelta(hours=3))


def fix_date(value):
    if value.startswith("22021-"):
        value = value[1:]
    return value


def fix_year(value):
    if not value.isdigit():
        value = ""
    return value


def fix_codigo_negociacao(value):
    if value.upper() in ("N/A", "0", "-"):
        value = ""
    return value


def fix_ato(value):
    if slug(value) in ("nao_e_o_caso", ""):
        value = ""
    return value


@lru_cache(maxsize=1024)
def camel_to_snake(*args, **kwargs):
    return rows_camel_to_snake(*args, **kwargs)


def element_to_dict(element):
    if isinstance(element, lxml.etree._ElementTree):
        element = element.getroot()
    children = element.getchildren()
    if not children:
        return element.text.strip() if element.text is not None else None
    return {child.tag: element_to_dict(child) for child in children}


@lru_cache(maxsize=20)
def parse_bool(value):
    return {
        "t": True,
        "true": True,
        "s": True,
        "sim": True,
        "f": False,
        "false": False,
        "n": False,
        "nao": False,
        "não": False,
        "": None,
    }[value.lower()]


def make_data_object(Class, row):
    new = {}
    for field in class_fields(Class):
        value = row.get(field.name)
        if value is None or not value:
            continue
        elif field.type is bool:
            value = parse_bool(str(value or ""))
        elif field.type is datetime.date:
            value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
        elif field.type is int:
            value = int(value)
        elif field.type is decimal.Decimal:
            value = decimal.Decimal(value)
        new[field.name] = value
    return Class(**new)


def camel_dict(data, prefix=""):
    if data is None:
        return {}
    return {prefix + camel_to_snake(key): value for key, value in data.items()}


@dataclass
class InformeRendimentos:
    tipo: str
    fundo: str
    fundo_cnpj: str
    administrador: str
    administrador_cnpj: str
    responsavel: str
    telefone: str
    codigo_isin: str
    valor_por_cota: decimal.Decimal
    data_informacao: datetime.date = None
    codigo_negociacao: str = None
    data_aprovacao: datetime.date = None
    data_base: datetime.date = None
    data_pagamento: datetime.date = None
    periodo_referencia: str = None
    ano: int = None
    ato_societario_aprovacao: str = None
    isento_ir: bool = None

    @classmethod
    def from_tree(cls, tree):
        result = []
        data = element_to_dict(tree)

        gerais = data.pop("DadosGerais", {}) or {}
        row = {
            "fundo": gerais.pop("NomeFundo"),
            "fundo_cnpj": gerais.pop("CNPJFundo"),
            "administrador": gerais.pop("NomeAdministrador"),
            "administrador_cnpj": gerais.pop("CNPJAdministrador"),
            "responsavel": gerais.pop("ResponsavelInformacao"),
            "telefone": gerais.pop("TelefoneContato"),
            "codigo_isin": gerais.pop("CodISINCota", ""),
            "codigo_negociacao": fix_codigo_negociacao(
                gerais.pop("CodNegociacaoCota", "") or ""
            ),
            "data_informacao": gerais.pop("DataInformacao", ""),
            "ano": gerais.pop("Ano", ""),
        }
        assert not gerais, f"gerais: {gerais}"

        rendimentos = data.pop("InformeRendimentos", {}) or {}
        provento = rendimentos.pop("Provento", {}) or {}
        if provento:
            row["codigo_isin"] = provento.pop("CodISIN")
            row["codigo_negociacao"] = fix_codigo_negociacao(
                provento.pop("CodNegociacao") or ""
            )
            rendimento = provento.pop("Rendimento", {}) or {}
            amortizacao = provento.pop("Amortizacao", {}) or {}
            assert not provento, f"provento: {provento}"
        else:
            rendimento = rendimentos.pop("Rendimento", {}) or {}
            amortizacao = rendimentos.pop("Amortizacao", {}) or {}
        assert not rendimentos, f"rendimentos: {rendimentos}"
        assert not data, f"data: {data}"

        # TODO: parse periodo_referencia
        if rendimento and (
            rendimento.get("ValorProventoCota") or rendimento.get("ValorProvento")
        ):
            part = {
                "tipo": "Rendimento",
                "ato_societario_aprovacao": fix_ato(
                    rendimento.pop("AtoSocietarioAprovacao", "")
                ),
                "data_aprovacao": fix_date(rendimento.pop("DataAprovacao", "")),
                "data_base": fix_date(rendimento.pop("DataBase", "")),
                "data_pagamento": fix_date(rendimento.pop("DataPagamento", "")),
                "valor_por_cota": rendimento.pop("ValorProventoCota", "")
                or rendimento.pop("ValorProvento"),
                "periodo_referencia": str(
                    rendimento.pop("PeriodoReferencia", "") or ""
                ).lower(),
                "ano": fix_year(rendimento.pop("Ano", "")),
                "isento_ir": rendimento.pop("RendimentoIsentoIR", "false") or "false",
            }
            if not part["ano"]:
                del part["ano"]
            result.append(make_data_object(cls, {**row, **part}))
            assert not rendimento, f"rendimento: {rendimento}"
        if amortizacao:
            part = {
                "tipo": "Amortização",
                "ato_societario_aprovacao": fix_ato(
                    amortizacao.pop("AtoSocietarioAprovacao", "")
                ),
                "data_aprovacao": fix_date(amortizacao.pop("DataAprovacao", "")),
                "data_base": fix_date(amortizacao.pop("DataBase", "")),
                "data_pagamento": fix_date(amortizacao.pop("DataPagamento", "")),
                "valor_por_cota": amortizacao.pop("ValorProventoCota", "")
                or amortizacao.pop("ValorProvento"),
                "periodo_referencia": str(
                    amortizacao.pop("PeriodoReferencia", "") or ""
                ).lower(),
                "ano": fix_year(amortizacao.pop("Ano", "")),
                "isento_ir": amortizacao.pop("RendimentoIsentoIR", "false") or "false",
            }
            if not part["ano"]:
                del part["ano"]
            result.append(make_data_object(cls, {**row, **part}))
            assert not amortizacao, f"amortizacao: {amortizacao}"
        return result


@dataclass
class OfertaPublica:
    nome_fundo: str = None
    cnpj_fundo: str = None
    nome_administrador: str = None
    cnpj_administrador: str = None
    responsavel_informacao: str = None
    telefone_contato: str = None
    email: str = None
    ato_aprovacao: str = None
    data_aprovacao: datetime.date = None
    tipo_oferta: str = None
    data_corte: datetime.date = None
    numero_emissao: int = None
    qtd_cotas_divide_pl_fundo: int = None
    qtd_max_cotas_serem_emitidas: int = None
    percentual_subscricao: decimal.Decimal = None
    preco_emissao: decimal.Decimal = None
    custo_distribuicao: decimal.Decimal = None
    preco_subscricao: decimal.Decimal = None
    montante_total: decimal.Decimal = None
    codigo_isin: str = None
    codigo_negociacao: str = None
    dp_b3_data_inicio: datetime.date = None
    dp_b3_data_fim: datetime.date = None
    dp_escriturador_data_inicio: datetime.date = None
    dp_escriturador_data_fim: datetime.date = None
    dp_escriturador_data_liquidacao: datetime.date = None
    dp_negociacao_b3_data_inicio: datetime.date = None
    dp_negociacao_b3_data_fim: datetime.date = None
    dp_negociacao_escriturador_data_inicio: datetime.date = None
    dp_negociacao_escriturador_data_fim: datetime.date = None
    dda_subscricao_data_inicio: datetime.date = None
    dda_subscricao_data_fim: datetime.date = None
    dda_alocacao_data_inicio: datetime.date = None
    dda_alocacao_data_fim: datetime.date = None
    dda_data_liquidacao: datetime.date = None
    dda_chamada_capital: bool = None
    possui_negociacao_direito_preferencia: bool = None
    possui_sobras_subscricao: bool = None
    possui_montante_adicional: bool = None
    montante_adicional: str = None
    utiliza_sistema_dda: bool = None
    sobras_data_liquidacao: datetime.date = None
    sobras_b3_data_fim: datetime.date = None
    sobras_b3_data_inicio: datetime.date = None
    sobras_escriturador_data_fim: datetime.date = None
    sobras_escriturador_data_inicio: datetime.date = None
    montante_adicional_exercicio_b3_data_inicio: datetime.date = None
    montante_adicional_exercicio_b3_data_fim: datetime.date = None
    montante_adicional_exercicio_escriturador_data_inicio: datetime.date = None
    montante_adicional_exercicio_escriturador_data_fim: datetime.date = None
    montante_adicional_data_liquidacao: datetime.date = None

    @classmethod
    def from_tree(cls, tree):
        data = element_to_dict(tree)
        row = {}

        gerais = data.pop("DadosGerais", {}) or {}
        row.update({camel_to_snake(key): value for key, value in gerais.items()})

        cota = data.pop("DadosCota", {}) or {}
        cota2 = cota.pop("Cota", {}) or {}
        row.update({camel_to_snake(key): value for key, value in cota2.items()})
        assert not cota, f"cota: {cota}"

        dp = data.pop("DireitoPreferencia", {}) or {}
        row.update(camel_dict(dp.pop("ExercicioDireitoPreferenciaB3", {}), "dp_b3_"))
        row.update(
            camel_dict(
                dp.pop("ExercicioDireitoPreferenciaEscriturador", {}),
                "dp_escriturador_",
            )
        )
        row.update({"dp_escriturador_dt_liquidacao": dp.pop("DtLiquidacao", None)})
        assert not dp, f"dp: {dp}"

        ndp = data.pop("NegociacaoDireitoPreferencia", {}) or {}
        row.update(
            camel_dict(ndp.pop("ExercicioNegociacaoDireitoB3", {}), "dp_negociacao_b3_")
        )
        row.update(
            camel_dict(
                ndp.pop("ExercicioNegociacaoDireitoEscriturador", {}),
                "dp_negociacao_escriturador_",
            )
        )
        assert not ndp, f"ndp: {ndp}"

        sobras = data.pop("SobrasSubscricao", {}) or {}
        row.update(
            camel_dict(sobras.pop("ExercicioSobrasSubscricaoB3", {}), "sobras_b3_")
        )
        row.update(
            camel_dict(
                sobras.pop("ExercicioSobrasSubscricaoEscriturador", {}),
                "sobras_escriturador_",
            )
        )
        row.update({"sobras_dt_liquidacao": sobras.pop("DtLiquidacao", None)})
        assert not sobras, f"sobras: {sobras}"

        dda = data.pop("SistemaDDA", {}) or {}
        row.update(camel_dict(dda.pop("PeriodoSubscricao", {}), "dda_subscricao_"))
        row.update(camel_dict(dda.pop("PeriodoReserva", {}), "dda_reserva_"))
        row.update(camel_dict(dda.pop("PeriodoAlocacao", {}), "dda_alocacao_"))
        row.update({"dda_dt_liquidacao": dda.pop("DtLiquidacao", None)})
        row.update({"dda_chamada_capital": dda.pop("ChamadaCapital", None)})
        assert not dda, f"dda: {dda}"

        montante_adicional = data.pop("MontanteAdicional", {}) or {}
        row.update(
            camel_dict(
                montante_adicional.pop("ExercicioMontanteAdicionalB3", {}),
                "montante_adicional_exercicio_b3_",
            )
        )
        row.update(
            camel_dict(
                montante_adicional.pop("ExercicioMontanteAdicionalEscriturador", {}),
                "montante_adicional_exercicio_escriturador_",
            )
        )
        row.update(
            {
                "montante_adicional_dt_liquidacao": montante_adicional.pop(
                    "DtLiquidacao", None
                )
            }
        )
        assert not montante_adicional, f"montante_adicional: {montante_adicional}"

        for key in list(data):
            value = data[key]
            if not isinstance(value, dict):
                row[camel_to_snake(key)] = value
                del data[key]

        assert not data, f"data: {data}"
        return make_data_object(
            cls,
            {
                key.replace("_dt_", "_data_")
                .replace("_fim_prazo", "_fim")
                .replace("_inicio_prazo", "_inicio"): value
                for key, value in row.items()
            },
        )


DOCUMENT_TYPES = {
    "DireitoPreferenciaSubscricaoCotas": OfertaPublica,
    "DadosEconomicoFinanceiros": InformeRendimentos,
}


class Document:
    @classmethod
    def from_file(cls, filename):
        with open(filename, mode="rb") as fobj:
            return cls(fobj.read())

    def __init__(self, xml_content):
        self._xml = xml_content
        self._tree = parse_xml(self._xml)
        self.__type = None

    @cached_property
    def type(self):
        first_tag = self._tree.xpath("/*[1]")[0].tag
        result = DOCUMENT_TYPES.get(first_tag)
        if result is None:
            raise ValueError(f"Unknown first tag {repr(first_tag)}")
        return result

    @cached_property
    def data(self):
        return self.type.from_tree(self._tree)


def parse_reference_date(fmt, value):
    if fmt == "2":
        value = f"01/{value}"
        fmt = "%d/%m/%Y"
    elif fmt == "3":
        fmt = "%d/%m/%Y"
    elif fmt == "4":
        fmt = "%d/%m/%Y %H:%M"
    elif fmt is None:
        fmt = "%Y-%m-%d %H:%M:%S%z"
    return datetime.datetime.strptime(value, fmt).replace(tzinfo=BRT)


@dataclass
class DocumentMeta:
    id: int
    alta_prioridade: bool
    analisado: bool
    categoria: str
    datahora_entrega: datetime.datetime
    datahora_referencia: datetime.datetime
    fundo: str
    fundo_pregao: str
    modalidade: str
    status: str
    tipo: str
    versao: int
    situacao: str = None
    especie: str = None
    informacoes_adicionais: str = None

    @property
    def url(self):
        return f"https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id={self.id}"

    @classmethod
    def from_json(cls, row):
        # XXX: Os campos abaixo estão sempre em branco e não são coletados:
        #      - arquivoEstruturado
        #      - assuntos
        #      - dda
        #      - formatoEstruturaDocumento
        #      - tipoPedido
        #      - idTemplate (sempre '0')
        #      - numeroEmissao
        #      - ofertaPublica
        #      - idSelectNotificacaoConvenio
        #      - idSelectItemConvenio (sempre '0')
        #      - idEntidadeGerenciadora
        #      - nomeAdministrador
        #      - cnpjAdministrador
        #      - cnpjFundo
        #      - indicadorFundoAtivoB3 (sempre 'False')

        return cls(
            id=row["id"],
            alta_prioridade=row["altaPrioridade"],
            analisado={"N": False, "S": True}[row["analisado"]],
            categoria=row["categoriaDocumento"].replace("  ", " ").strip(),
            datahora_entrega=parse_reference_date("4", row["dataEntrega"]),
            datahora_referencia=parse_reference_date(
                row["formatoDataReferencia"], row["dataReferencia"]
            ),
            especie=row["especieDocumento"].strip(),
            fundo=row["descricaoFundo"].strip(),
            fundo_pregao=row["nomePregao"].strip(),
            informacoes_adicionais=row["informacoesAdicionais"].strip(),
            modalidade=row["descricaoModalidade"].strip(),
            situacao=row["situacaoDocumento"].strip(),
            status=row["descricaoStatus"].strip(),
            tipo=row["tipoDocumento"].strip(),
            versao=row["versao"],
        )

    @classmethod
    def from_dict(cls, row):
        return cls(
            id=int(row["id"]),
            alta_prioridade=parse_bool(row["alta_prioridade"]),
            analisado=parse_bool(row["analisado"]),
            categoria=row["categoria"],
            datahora_entrega=parse_reference_date(None, row["datahora_entrega"]),
            datahora_referencia=parse_reference_date(None, row["datahora_referencia"]),
            especie=row["especie"],
            fundo=row["fundo"],
            fundo_pregao=row["fundo_pregao"],
            informacoes_adicionais=row["informacoes_adicionais"],
            modalidade=row["modalidade"],
            situacao=row["situacao"],
            status=row["status"],
            tipo=row["tipo"],
            versao=int(row["versao"]),
        )
