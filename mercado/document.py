import datetime
import decimal
import re
from dataclasses import dataclass
from dataclasses import fields as class_fields
from functools import cached_property

import lxml.etree
from lxml.etree import fromstring as parse_xml
from rows.fields import camel_to_snake, slug


BRT = datetime.timezone(-datetime.timedelta(hours=3))


def element_to_dict(element):
    if isinstance(element, lxml.etree._ElementTree):
        element = element.getroot()
    children = element.getchildren()
    if not children:
        return element.text.strip() if element.text is not None else None
    return {child.tag: element_to_dict(child) for child in children}


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
    return datetime.datetime.strptime(value, fmt).replace(tzinfo=BRT)


@dataclass
class DocumentMeta:
    id: int
    datahora_entrega: datetime.datetime
    datahora_referencia: datetime.datetime
    versao: int
    tipo: int
    categoria: int
    modalidade: int
    status: int
    alta_prioridade: bool
    analisado: bool
    indicador_fundo_ativo_b3: bool  # Sempre 'False'
    fundo: str
    fundo_pregao: str
    situacao: str = None
    especie: str = None
    informacoes_adicionais: str = None

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

        # TODO: convert to int: tipo
        #  Informe Mensal Estruturado                                   | 74785
        #  Informe Diário                                               | 69860
        #                                                               | 21252
        #  Rendimentos e Amortizações                                   | 16800
        #  AGE                                                          | 14117
        #  Relatório Gerencial                                          | 13091
        #  Informe Trimestral Estruturado                               | 12336
        #  Informe Trimestral                                           | 11295
        #  Demonstrações Financeiras                                    |  6470
        #  AGO                                                          |  6331
        #  Outros Comunicados Não Considerados Fatos Relevantes         |  5932
        #  Relatório de Agência de Rating                               |  5150
        #  Rentabilidade                                                |  3959
        #  Instrumento Particular de Alteração do Regulamento           |  3742
        #  Informe Anual Estruturado                                    |  3277
        #  AGO/E                                                        |  2530
        #  Informe Mensal                                               |  2315
        #  Balancete                                                    |  2070
        #  Composição da Carteira (CDA)                                 |  1921
        #  Outros Relatórios                                            |  1587
        #  Outros Documentos                                            |  1169
        #  Instrumento Particular de Constituição/Encerramento do Fundo |  1120
        #  Prospecto                                                    |  1069
        #  Instrumento Particular de Emissão de Cotas                   |  1058
        #  Esclarecimentos de consulta B3 / CVM                         |   687
        #  Restritos - ICVM 476                                         |   645
        #  Anúncio de Encerramento                                      |   639
        #  Aviso ao Mercado                                             |   522
        #  Anúncio de Início                                            |   454
        #  Perfil do Fundo                                              |   378
        #  Informe Semestral - DFC e Relatório do Administrador         |   336
        #  Anexo 39-V (art. 10 §1º, inciso I da ICVM 472)               |   253
        #  Formulário de Liberação para Negociação das Cotas            |   140
        #  Relatório Anual                                              |    90
        #  Perfil do Fundo (Estruturado)                                |    79
        #  Demonstração Financeira de Encerramento                      |    71
        #  Formulário de Subscrição de Cotas (Estruturado)              |    67
        #  Relação das demandas judiciais ou extrajudiciais             |    59
        #  Aviso de Modificação de Oferta                               |    55
        #  Relatório do Representante de Cotistas                       |    15
        #  Demonstrações Financeiras de Devedores ou Coobrigados        |    13
        #  Manifestação do Administrador / Gestor                       |     5
        #  Edital de Oferta Pública de Aquisição de Cotas               |     5
        #  Formulário de Liberação para Negociação das Cotas            |     4
        #  Press - Release                                              |     2
        #  Material de Divulgação                                       |     1
        #  Informe Anual                                                |     1

        # TODO: convert to int: categoria
        #  Informes Periódicos                          | 184848
        #  Assembleia                                   |  22978
        #  Relatórios                                   |  19896
        #  Aviso aos Cotistas - Estruturado             |  16800
        #  Regulamento                                  |   9005
        #  Comunicado ao Mercado                        |   6881
        #  Aviso aos Cotistas                           |   6052
        #  Atos de Deliberação do Administrador         |   5920
        #  Fato Relevante                               |   5613
        #  Outras Informações                           |   5250
        #  Oferta Pública de Distribuição de Cotas      |   4180
        #  Laudo de Avaliação (Conclusão de Negócio)    |    320
        #  Oferta Pública de Aquisição de Cotas         |     10
        #  Documentos de Oferta de Distribuição Pública |      4

        # TODO: convert to int: modalidade
        #  AP         | Apresentação                 | 243035
        #  RE         | Reapresentação Espontânea    |  43753
        #  RC         | Reapresentação por Exigência |    969

        # TODO: convert to int: situacao
        #  A                 | 239796
        #  I                 |  44079
        #  C                 |   3882

        # TODO: convert to int: status
        #  AC     | Ativo com visualização     | 239796
        #  IC     | Inativo com visualização   |  44079
        #  CC     | Cancelado com visualização |   3882

        return cls(
            id=row["id"],
            versao=row["versao"],
            datahora_entrega=parse_reference_date("4", row["dataEntrega"]),
            datahora_referencia=parse_reference_date(
                row["formatoDataReferencia"], row["dataReferencia"]
            ),
            tipo=row["tipoDocumento"],
            categoria=row["categoriaDocumento"],
            modalidade=row["descricaoModalidade"],
            status=row["descricaoStatus"],
            situacao=row["situacaoDocumento"],
            especie=row["especieDocumento"],
            alta_prioridade=row["altaPrioridade"],
            analisado={"N": False, "S": True}[row["analisado"]],
            fundo=row["descricaoFundo"],
            fundo_pregao=row["nomePregao"],
            informacoes_adicionais=row["informacoesAdicionais"],
            indicador_fundo_ativo_b3=row["indicadorFundoAtivoB3"],
        )
