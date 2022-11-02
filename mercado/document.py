import datetime
import decimal
from dataclasses import dataclass
from dataclasses import fields as class_fields
from functools import cached_property

import lxml.etree
from lxml.etree import fromstring as parse_xml
from rows.fields import camel_to_snake

BRT = datetime.timezone(-datetime.timedelta(hours=3))


def element_to_dict(element):
    if isinstance(element, lxml.etree._ElementTree):
        element = element.getroot()
    children = element.getchildren()
    if not children:
        return element.text.strip() if element.text is not None else None
    return {child.tag: element_to_dict(child) for child in children}


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
        if value is None:
            continue
        elif field.type is bool:
            value = {"true": True, "false": False}.get(str(value or "").strip().lower())
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
        assert not cota

        dp = data.pop("DireitoPreferencia", {}) or {}
        row.update(camel_dict(dp.pop("ExercicioDireitoPreferenciaB3", {}), "dp_b3_"))
        row.update(
            camel_dict(
                dp.pop("ExercicioDireitoPreferenciaEscriturador", {}),
                "dp_escriturador_",
            )
        )
        row.update({"dp_escriturador_dt_liquidacao": dp.pop("DtLiquidacao", None)})
        assert not dp

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
        assert not ndp

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
        assert not sobras

        dda = data.pop("SistemaDDA", {}) or {}
        row.update(camel_dict(dda.pop("PeriodoSubscricao", {}), "dda_subscricao_"))
        row.update(camel_dict(dda.pop("PeriodoReserva", {}), "dda_reserva_"))
        row.update(camel_dict(dda.pop("PeriodoAlocacao", {}), "dda_alocacao_"))
        row.update({"dda_dt_liquidacao": dda.pop("DtLiquidacao", None)})
        row.update({"dda_chamada_capital": dda.pop("ChamadaCapital", None)})
        assert not dda

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
        assert not montante_adicional

        for key in list(data):
            value = data[key]
            if not isinstance(value, dict):
                row[camel_to_snake(key)] = value
                del data[key]

        assert not data, data
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
    "DireitoPreferenciaSubscricaoCotas": OfertaPublica,  # TODO: change to dataclass
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
