import copy
import datetime
import decimal
import re
from dataclasses import dataclass
from dataclasses import fields as class_fields

import xmltodict

from .utils import camel_to_snake, clean_xml_dict, parse_bool, parse_br_decimal, parse_date, parse_int, slug

REGEXP_NUMBERS = re.compile("[^0-9]+")


def clean_cnpj(value):
    """
    >>> clean_cnpj('12.345.678/0001-91')
    '12345678000191'
    >>> clean_cnpj('2.345.678/0001-91')
    '02345678000191'
    >>> print(clean_cnpj('Invalid value'))
    None
    """
    value = REGEXP_NUMBERS.sub("", str(value or ""))  # TODO: CNPJ will change in 2026 (add alpha)
    if not value:
        return None
    if len(value) < 14:
        value = "0" * (14 - len(value)) + value
    elif len(value) > 14:  # XXX: may warn if len(value) != 14 (or invalid value)
        value = None
    return value


def clean_dict(obj):
    if obj is None:
        return None
    return {key: value for key, value in obj.items() if value}


def fix_date(value):
    if value is None:
        return None
    elif value.startswith("22021-"):
        value = value[1:]
    elif value.startswith("20005-"):
        value = value.replace("20005-", "2005-")
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


def fix_segmento(value):
    if not value:
        return value
    return {
        "hibrido": "Híbrido",
        "hospital": "Hospital",
        "hotel": "Hotel",
        "lajes_corporativas": "Lajes Corporativas",
        "logistica": "Logística",
        "outros": "Outros",
        "residencial": "Residencial",
        "shoppings": "Shoppings",
        "titulos_e_valores_mobiliarios": "Títulos e Valores Mobiliários",
        "titulos_e_val_mob": "Títulos e Valores Mobiliários",
    }[slug(value)]


def fix_mandato(value):
    if not value:
        return value
    return {
        "renda": "Renda",
        "hibrido": "Híbrido",
        "titulos_e_valores_mobiliarios": "Títulos e Valores Mobiliários",
        "desenvolvimento_para_renda": "Desenvolvimento para Renda",
        "desenvolvimento_para_venda": "Desenvolvimento para Venda",
    }[slug(value)]


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
    tipo_amortizacao: str = None

    @classmethod
    def check_content(cls, data):
        return "InformeRendimentos" in data

    @classmethod
    def from_xml(cls, xml):
        return cls.from_data(xmltodict.parse(xml))

    @classmethod
    def check_xml(cls, xml):
        if xml is None:
            return False
        data = xmltodict.parse(xml)
        return (
            "DadosEconomicoFinanceiros" in data
            and "DadosGerais" in data["DadosEconomicoFinanceiros"]
            and "InformeRendimentos" in data["DadosEconomicoFinanceiros"]
        )

    @classmethod
    def from_data(cls, original_data):
        result = []
        data = original_data.pop("DadosEconomicoFinanceiros", {}) or {}
        original_data = {
            key: value for key, value in original_data.items() if not key.startswith("@")  # Remove namespace info
        }
        assert not original_data

        gerais = data.pop("DadosGerais", {}) or {}
        row = {
            "fundo": gerais.pop("NomeFundo"),
            "fundo_cnpj": clean_cnpj(gerais.pop("CNPJFundo")),
            "administrador": gerais.pop("NomeAdministrador"),
            "administrador_cnpj": clean_cnpj(gerais.pop("CNPJAdministrador")),
            "responsavel": gerais.pop("ResponsavelInformacao"),
            "telefone": gerais.pop("TelefoneContato"),
            "codigo_isin": gerais.pop("CodISINCota", ""),
            "codigo_negociacao": fix_codigo_negociacao(gerais.pop("CodNegociacaoCota", "") or ""),
            "data_informacao": gerais.pop("DataInformacao", ""),
            "ano": gerais.pop("Ano", ""),
        }
        assert not gerais, f"gerais: {gerais}"

        informe_rendimentos = data.pop("InformeRendimentos", {}) or {}
        rendimentos, amortizacoes = [], []
        for key in list(informe_rendimentos.keys()):
            if key == "Rendimento":
                rendimento = informe_rendimentos.pop(key, {}) or {}
                if clean_dict(rendimento):
                    rendimentos.append(rendimento)
            elif key == "Amortizacao":
                amortizacao = informe_rendimentos.pop(key, {}) or {}
                amortizacao = clean_dict(amortizacao)
                if amortizacao and list(amortizacao.keys()) != ["@tipo"]:
                    amortizacoes.append(amortizacao)
            elif key == "Provento":
                value = informe_rendimentos.pop(key)
                if isinstance(value, dict):
                    value = [value]
                for provento in value:
                    provento_base = {
                        "codigo_isin": provento.pop("CodISIN"),
                        "codigo_negociacao": provento.pop("CodNegociacao"),
                    }
                    if "Rendimento" in provento:
                        rendimento = provento.pop("Rendimento", {}) or {}
                        if clean_dict(rendimento):
                            rendimentos.append({**provento_base, **rendimento})
                    if "Amortizacao" in provento:
                        amortizacao = clean_dict(provento.pop("Amortizacao", {}) or {})
                        if amortizacao and list(amortizacao.keys()) != ["@tipo"]:
                            amortizacoes.append({**provento_base, **amortizacao})
                    assert not provento, f"provento: {provento}"
        assert not informe_rendimentos, f"informe_rendimentos: {informe_rendimentos}"

        # TODO: parse periodo_referencia
        for rendimento in rendimentos:
            part = {
                "tipo": "Rendimento",
                "ato_societario_aprovacao": fix_ato(rendimento.pop("AtoSocietarioAprovacao", "")),
                "data_aprovacao": fix_date(rendimento.pop("DataAprovacao", "")),
                "data_base": fix_date(rendimento.pop("DataBase", "")),
                "data_pagamento": fix_date(rendimento.pop("DataPagamento", "")),
                "valor_por_cota": rendimento.pop("ValorProventoCota", "") or rendimento.pop("ValorProvento"),
                "periodo_referencia": str(rendimento.pop("PeriodoReferencia", "") or "").lower(),
                "ano": fix_year(rendimento.pop("Ano", "")),
                "isento_ir": rendimento.pop("RendimentoIsentoIR", "false") or "false",
            }
            for key in ("codigo_isin", "codigo_negociacao"):
                if key in rendimento:
                    part[key] = rendimento.pop(key)
            if not part["ano"]:
                del part["ano"]
            result.append(make_data_object(cls, {**row, **part}))
            assert not rendimento, f"rendimento: {rendimento}"

        for amortizacao in amortizacoes:
            part = {
                "tipo": "Amortização",
                "ato_societario_aprovacao": fix_ato(amortizacao.pop("AtoSocietarioAprovacao", "")),
                "data_aprovacao": fix_date(amortizacao.pop("DataAprovacao", "")),
                "data_base": fix_date(amortizacao.pop("DataBase", "")),
                "data_pagamento": fix_date(amortizacao.pop("DataPagamento", "")),
                "valor_por_cota": amortizacao.pop("ValorProventoCota", "") or amortizacao.pop("ValorProvento"),
                "periodo_referencia": str(amortizacao.pop("PeriodoReferencia", "") or "").lower(),
                "ano": fix_year(amortizacao.pop("Ano", "")),
                "isento_ir": amortizacao.pop("RendimentoIsentoIR", "false") or "false",
                "tipo_amortizacao": amortizacao.pop("@tipo", None),
            }
            for key in ("codigo_isin", "codigo_negociacao"):
                if key in amortizacao:
                    part[key] = amortizacao.pop(key)
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
    def check_content(cls, data):
        return "DireitoPreferencia" in data

    @classmethod
    def from_xml(cls, xml):
        return cls.from_data(xmltodict.parse(xml))

    @classmethod
    def check_xml(cls, xml):
        if xml is None:
            return False
        data = xmltodict.parse(xml)
        return "DadosGerais" in data and "DadosCota" in data and "DireitoPreferencia" in data

    @classmethod
    def from_data(cls, data):
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
        row.update(camel_dict(ndp.pop("ExercicioNegociacaoDireitoB3", {}), "dp_negociacao_b3_"))
        row.update(
            camel_dict(
                ndp.pop("ExercicioNegociacaoDireitoEscriturador", {}),
                "dp_negociacao_escriturador_",
            )
        )
        assert not ndp, f"ndp: {ndp}"

        sobras = data.pop("SobrasSubscricao", {}) or {}
        row.update(camel_dict(sobras.pop("ExercicioSobrasSubscricaoB3", {}), "sobras_b3_"))
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
        row.update({"montante_adicional_dt_liquidacao": montante_adicional.pop("DtLiquidacao", None)})
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
                key.replace("_dt_", "_data_").replace("_fim_prazo", "_fim").replace("_inicio_prazo", "_inicio"): value
                for key, value in row.items()
            },
        )


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
        informacoes_adicionais = row["informacoesAdicionais"].strip()
        fundo_pregao = row["nomePregao"].strip()
        if informacoes_adicionais.endswith(";"):
            informacoes_adicionais = informacoes_adicionais[:-1].strip()
        if informacoes_adicionais == fundo_pregao or not informacoes_adicionais:
            informacoes_adicionais = None
        # TODO: pop every item and check if dict is empty in the end
        return cls(
            id=row["id"],
            alta_prioridade=row["altaPrioridade"],
            analisado={"N": False, "S": True}[row["analisado"]],
            categoria=row["categoriaDocumento"].replace("  ", " ").strip(),
            datahora_entrega=parse_date("4", row["dataEntrega"], full=True),
            datahora_referencia=parse_date(row["formatoDataReferencia"], row["dataReferencia"], full=True),
            especie=row["especieDocumento"].strip(),
            fundo=row["descricaoFundo"].strip(),
            fundo_pregao=fundo_pregao,
            informacoes_adicionais=informacoes_adicionais,
            modalidade=row["descricaoModalidade"].strip(),
            situacao=row["situacaoDocumento"].strip(),
            status=row["descricaoStatus"].strip(),
            tipo=row["tipoDocumento"].strip(),
            versao=row["versao"],
        )

    @classmethod
    def from_dict(cls, row):
        obj = cls(
            id=int(row["id"]),
            alta_prioridade=parse_bool(row["alta_prioridade"]),
            analisado=parse_bool(row["analisado"]),
            categoria=row["categoria"],
            datahora_entrega=parse_date("iso-datetime-tz", row["datahora_entrega"]),
            datahora_referencia=parse_date("iso-datetime-tz", row["datahora_referencia"]),
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
        assert not row
        return obj


@dataclass
class InformeFII:
    fundo: str
    fundo_cnpj: str
    administrador: str
    administrador_cnpj: str
    data_funcionamento: datetime.date
    cotas_emitidas: decimal.Decimal
    publico_alvo: str
    exclusivo: bool
    vinculo_familiar_cotistas: bool
    prazo_duracao: str
    encerramento_exercicio: str
    mercado_negociacao_bolsa: bool
    mercado_negociacao_mbo: bool
    mercado_negociacao_mb: bool
    adm_bvmf: bool
    adm_cetip: bool
    logradouro: str
    numero: str
    bairro: str
    municipio: str
    uf: str
    cep: str
    telefone_1: str
    site: str
    email: str
    competencia: str
    tipo: str
    dados: dict
    codigo_isin: str = None
    gestao_tipo: str = None
    segmento: str = None
    mandato: str = None
    complemento: str = None
    telefone_2: str = None
    data_prazo: datetime.date = None
    telefone_3: str = None
    enquadra_nota_seis: bool = None
    data_encerramento_trimestre: datetime.date = None

    @classmethod
    def from_xml(cls, xml):
        return cls.from_data(xmltodict.parse(xml))

    @classmethod
    def check_xml(cls, xml):
        if xml is None:
            return False
        data = xmltodict.parse(xml)
        return (
            "DadosEconomicoFinanceiros" in data
            and "DadosGerais" in data["DadosEconomicoFinanceiros"]
            and (
                "InformeMensal" in data["DadosEconomicoFinanceiros"]
                or "InformeTrimestral" in data["DadosEconomicoFinanceiros"]
                or "InformeAnual" in data["DadosEconomicoFinanceiros"]
            )
        )

    @classmethod
    def from_data(cls, original_data):
        copied = clean_xml_dict(copy.deepcopy(original_data))
        data = {key: value for key, value in copied["DadosEconomicoFinanceiros"].items() if not key.startswith("@")}
        gerais = data.pop("DadosGerais")
        informe_mensal = data.pop("InformeMensal", {}) or {}
        informe_trimestral = data.pop("InformeTrimestral", {}) or {}
        informe_anual = data.pop("InformeAnual", {}) or {}
        assert not data, f"data: {data}"

        if informe_mensal:
            tipo = "Informe Mensal"
        elif informe_trimestral:
            tipo = "Informe Trimestral"
        elif informe_anual:
            tipo = "Informe Anual"
        else:
            raise ValueError("Tipo de informe desconhecido")

        autorregulacao = gerais.pop("Autorregulacao")
        entidade_administradora = gerais.pop("EntidadeAdministradora")
        mercado_negociacao = gerais.pop("MercadoNegociacao")
        row = {
            "fundo": gerais.pop("NomeFundo"),
            "fundo_cnpj": clean_cnpj(gerais.pop("CNPJFundo")),
            "administrador": gerais.pop("NomeAdministrador"),
            "administrador_cnpj": clean_cnpj(gerais.pop("CNPJAdministrador")),
            "data_funcionamento": parse_date("iso-date", fix_date(gerais.pop("DataFuncionamento"))),
            "publico_alvo": gerais.pop("PublicoAlvo"),
            "codigo_isin": gerais.pop("CodigoISIN", None),
            "cotas_emitidas": parse_br_decimal(gerais.pop("QtdCotasEmitidas")),
            "exclusivo": parse_bool(gerais.pop("FundoExclusivo")),
            "vinculo_familiar_cotistas": parse_bool(gerais.pop("VinculoFamiliarCotistas")),
            "mandato": fix_mandato(autorregulacao.pop("Mandato", None)),
            "segmento": fix_segmento(autorregulacao.pop("SegmentoAtuacao", None)),
            "gestao_tipo": autorregulacao.pop("TipoGestao", None),
            "prazo_duracao": gerais.pop("PrazoDuracao"),
            "data_prazo": parse_date("iso-date", gerais.pop("DataPrazoDuracao", None)),
            "encerramento_exercicio": gerais.pop("EncerramentoExercicio"),
            "mercado_negociacao_bolsa": parse_bool(mercado_negociacao.pop("Bolsa")),
            "mercado_negociacao_mbo": parse_bool(mercado_negociacao.pop("MBO")),
            "mercado_negociacao_mb": parse_bool(mercado_negociacao.pop("MB")),
            "adm_bvmf": parse_bool(entidade_administradora.pop("BVMF")),
            "adm_cetip": parse_bool(entidade_administradora.pop("CETIP")),
            "logradouro": gerais.pop("Logradouro"),
            "numero": gerais.pop("Numero"),
            "complemento": gerais.pop("Complemento", ""),
            "bairro": gerais.pop("Bairro"),
            "municipio": gerais.pop("Cidade"),
            "uf": gerais.pop("Estado"),
            "cep": gerais.pop("CEP"),
            "telefone_1": gerais.pop("Telefone1"),
            "telefone_2": gerais.pop("Telefone2", None),
            "telefone_3": gerais.pop("Telefone3", None),
            "site": gerais.pop("Site"),
            "email": gerais.pop("Email"),
            "competencia": gerais.pop("Competencia"),
            "tipo": tipo,
            "enquadra_nota_seis": parse_bool(gerais.pop("EnquadraNotaSeis", None)),
            "data_encerramento_trimestre": parse_date("iso-date", gerais.pop("DataEncerTrimestre", None)),
            "dados": informe_mensal or informe_trimestral or informe_anual,
        }

        assert not gerais, f"gerais: {gerais}"
        assert not autorregulacao, f"autorregulacao: {autorregulacao}"
        assert not mercado_negociacao, f"mercado_negociacao: {mercado_negociacao}"
        assert not entidade_administradora, f"entidade_administradora: {entidade_administradora}"

        return [cls(**row)]

    @property
    def informe_mensal(self):
        informe_mensal = copy.deepcopy(self.dados)
        cotistas = informe_mensal.pop("Cotistas")
        resumo = informe_mensal.pop("Resumo")
        # TODO: there are way more data in `informe_mensal` we're ignoring
        # here, so needs parsing
        return InformeMensalFII(
            cotistas=parse_int(cotistas.pop("@total", None)),
            cotistas_pessoa_fisica=parse_int(cotistas.pop("PessoaFisica", None)),
            patrimonio_liquido=parse_br_decimal(resumo.pop("PatrimonioLiquido")),
            ativo=parse_br_decimal(resumo.pop("Ativo")),
            cotas_emitidas=parse_br_decimal(resumo.pop("NumCotasEmitidas")),
            patrimonio_por_cota=parse_br_decimal(resumo.pop("ValorPatrCotas")),
        )


@dataclass
class InformeMensalFII:
    ativo: decimal.Decimal
    cotas_emitidas: decimal.Decimal
    patrimonio_liquido: decimal.Decimal
    patrimonio_por_cota: decimal.Decimal
    cotistas: int = None
    cotistas_pessoa_fisica: int = None
