import datetime
import decimal
import re
from dataclasses import dataclass, fields as class_fields
from functools import cached_property

from lxml.etree import fromstring as parse_xml
from rows.fields import slug

import lxml.etree


REGEXP_CAMELCASE_1 = re.compile("(.)([A-Z][a-z]+)")
REGEXP_CAMELCASE_2 = re.compile("([a-z0-9])([A-Z])")

def camel_to_snake(value):
    # Adapted from <https://stackoverflow.com/a/1176023/1299446>
    return slug(REGEXP_CAMELCASE_2.sub(r"\1_\2", REGEXP_CAMELCASE_1.sub(r"\1_\2", value)))


def element_to_dict(element):
    if isinstance(element, lxml.etree._ElementTree):
        element = element.getroot()
    children = element.getchildren()
    if not children:
        return element.text.strip() if element.text is not None else None
    return {
        child.tag: element_to_dict(child)
        for child in children
    }


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
        row.update(camel_dict(dp.pop("ExercicioDireitoPreferenciaEscriturador", {}), "dp_escriturador_"))
        row.update({"dp_escriturador_dt_liquidacao": dp.pop("DtLiquidacao", None)})
        assert not dp

        ndp = data.pop("NegociacaoDireitoPreferencia", {}) or {}
        row.update(camel_dict(ndp.pop("ExercicioNegociacaoDireitoB3", {}), "dp_negociacao_b3_"))
        row.update(camel_dict(ndp.pop("ExercicioNegociacaoDireitoEscriturador", {}), "dp_negociacao_escriturador_"))
        assert not ndp

        sobras = data.pop("SobrasSubscricao", {}) or {}
        row.update(camel_dict(sobras.pop("ExercicioSobrasSubscricaoB3", {}), "sobras_b3_"))
        row.update(camel_dict(sobras.pop("ExercicioSobrasSubscricaoEscriturador", {}), "sobras_escriturador_"))
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
        row.update(camel_dict(montante_adicional.pop("ExercicioMontanteAdicionalB3", {}), "montante_adicional_exercicio_b3_"))
        row.update(camel_dict(montante_adicional.pop("ExercicioMontanteAdicionalEscriturador", {}), "montante_adicional_exercicio_escriturador_"))
        row.update({"montante_adicional_dt_liquidacao": montante_adicional.pop("DtLiquidacao", None)})
        assert not montante_adicional

        for key in list(data):
            value = data[key]
            if not isinstance(value, dict):
                row[camel_to_snake(key)] = value
                del data[key]

        assert not data, data
        return make_data_object(cls, {key.replace("_dt_", "_data_").replace("_fim_prazo", "_fim").replace("_inicio_prazo", "_inicio"): value for key, value in row.items()})


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
