import datetime
import decimal
from pathlib import Path

from mercados.document import InformeRendimentos


def assert_informe_rendimentos(document_id, expected):
    filename = Path(__file__).parent / "data" / f"document-{document_id:06d}.xml"
    with filename.open() as fobj:
        xml = fobj.read()
    docs = InformeRendimentos.from_xml(xml)
    assert len(docs) == len(expected)
    for a, b in zip(docs, expected):
        assert a == b


def test_informe_12141():
    expected = [
        InformeRendimentos(
            fundo="BRADESCO CARTEIRA IMOBILIARIA ATIVA FII",
            fundo_cnpj="20216935000117",
            administrador="BANCO BRADESCO S/A",
            administrador_cnpj="60746948000112",
            responsavel="DEBORAH CRISTINA LEITE DE LIMA",
            telefone="3684-4398",
            codigo_isin="BRBCIACTF005",
            codigo_negociacao="BCIA11",
            data_informacao=None,
            ano=2017,
            tipo="Rendimento",
            valor_por_cota=decimal.Decimal("0.65"),
            data_aprovacao=datetime.date(2017, 4, 27),
            data_base=datetime.date(2017, 4, 28),
            data_pagamento=datetime.date(2017, 5, 29),
            periodo_referencia="abril",
            isento_ir=True,
            ato_societario_aprovacao=None,
        ),
    ]

    assert_informe_rendimentos(12141, expected)


def test_informe_251698():
    expected = [
        InformeRendimentos(
            fundo="VLJS - VECTOR QUELUZ LAJES CORPORATIVAS FII",
            fundo_cnpj="13842683000176",
            administrador="PLANNER CORRETORA DE VALORES S/A",
            administrador_cnpj="00806535000154",
            responsavel="ANDRÉA AIPP",
            telefone="1130146017",
            codigo_isin="BRVLJSCTF020",
            codigo_negociacao="VLJS11",
            data_informacao=None,
            ano=2021,
            tipo="Rendimento",
            valor_por_cota=decimal.Decimal("28.81922098"),
            data_aprovacao=datetime.date(2021, 12, 30),
            data_base=datetime.date(2021, 12, 30),
            data_pagamento=datetime.date(2022, 1, 28),
            periodo_referencia="12",
            isento_ir=False,
            ato_societario_aprovacao=None,
        ),
    ]

    assert_informe_rendimentos(251698, expected)


def test_informe_370482():
    expected = [
        InformeRendimentos(
            fundo="KINEA RENDIMENTOS IMOBILIÁRIOS FII",
            fundo_cnpj="16706958000132",
            administrador="INTRAG DTVM",
            administrador_cnpj="62418140000131",
            responsavel="WALTER HIROAKI WATANABE",
            telefone="011 30726090",
            data_informacao=datetime.date(2022, 10, 31),
            ano=2022,
            codigo_isin="BRKNCRCTF000",
            codigo_negociacao="KNCR11",
            tipo="Rendimento",
            valor_por_cota=decimal.Decimal("1.1"),
            data_aprovacao=None,
            data_base=datetime.date(2022, 10, 31),
            data_pagamento=datetime.date(2022, 11, 14),
            periodo_referencia="outubro 2022",
            isento_ir=True,
            ato_societario_aprovacao=None,
        ),
        InformeRendimentos(
            fundo="KINEA RENDIMENTOS IMOBILIÁRIOS FII",
            fundo_cnpj="16706958000132",
            administrador="INTRAG DTVM",
            administrador_cnpj="62418140000131",
            responsavel="WALTER HIROAKI WATANABE",
            telefone="011 30726090",
            data_informacao=datetime.date(2022, 10, 31),
            ano=2022,
            codigo_isin="BRKNCRR08M13",
            codigo_negociacao="KNCR14",
            tipo="Rendimento",
            valor_por_cota=decimal.Decimal("1.1"),
            data_aprovacao=None,
            data_base=datetime.date(2022, 10, 31),
            data_pagamento=datetime.date(2022, 11, 14),
            periodo_referencia="outubro 2022",
            isento_ir=True,
            ato_societario_aprovacao=None,
        ),
    ]

    assert_informe_rendimentos(370482, expected)


def test_informe_373030():
    expected = [
        InformeRendimentos(
            fundo="CIDADE JARDIM CONTINENTAL TOWER FII",
            fundo_cnpj="10347985000180",
            administrador="HEDGE INVESTMENTS DTVM LTDA.",
            administrador_cnpj="07253654000176",
            responsavel="Maria Cecilia Carrazedo de Andrade",
            telefone="(11) 5412-5400",
            data_informacao=datetime.date(2022, 11, 7),
            ano=2022,
            codigo_isin="BRCJCTCTF001",
            codigo_negociacao="CJCT11",
            tipo_amortizacao="Parcial",
            tipo="Amortização",
            data_base=datetime.date(2022, 11, 7),
            valor_por_cota=decimal.Decimal("3.5119"),
            data_pagamento=datetime.date(2022, 11, 17),
            periodo_referencia="novembro",
            data_aprovacao=None,
            isento_ir=False,
            ato_societario_aprovacao=None,
        ),
        InformeRendimentos(
            fundo="CIDADE JARDIM CONTINENTAL TOWER FII",
            fundo_cnpj="10347985000180",
            administrador="HEDGE INVESTMENTS DTVM LTDA.",
            administrador_cnpj="07253654000176",
            responsavel="Maria Cecilia Carrazedo de Andrade",
            telefone="(11) 5412-5400",
            data_informacao=datetime.date(2022, 11, 7),
            ano=2022,
            codigo_isin="BRCJCTCTF001",
            codigo_negociacao="CJCT11",
            tipo_amortizacao="Parcial",
            tipo="Amortização",
            data_base=datetime.date(2022, 11, 7),
            valor_por_cota=decimal.Decimal("17.555"),
            data_pagamento=datetime.date(2023, 11, 21),
            periodo_referencia="novembro",
            data_aprovacao=None,
            isento_ir=False,
            ato_societario_aprovacao=None,
        ),
    ]

    assert_informe_rendimentos(373030, expected)


def test_informe_373491():
    expected = [
        InformeRendimentos(
            fundo="IMMOB II FUNDO DE INVESTIMENTO IMOBILIÁRIO - FII",
            fundo_cnpj="32655589000152",
            administrador="BEM DTVM LTDA",
            administrador_cnpj="00066670000100",
            responsavel="DANIEL SILVA SERAFIM",
            telefone="11 2357-8480",
            data_informacao=datetime.date(2022, 11, 8),
            ano=2022,
            codigo_isin="BRIMMOCTF010",
            codigo_negociacao="IMMO13",
            tipo="Rendimento",
            ato_societario_aprovacao="Não",
            data_base=datetime.date(2022, 11, 8),
            valor_por_cota=decimal.Decimal("0.1"),
            data_pagamento=datetime.date(2022, 11, 16),
            periodo_referencia="novembro",
            isento_ir=False,
            data_aprovacao=None,
        ),
        InformeRendimentos(
            fundo="IMMOB II FUNDO DE INVESTIMENTO IMOBILIÁRIO - FII",
            fundo_cnpj="32655589000152",
            administrador="BEM DTVM LTDA",
            administrador_cnpj="00066670000100",
            responsavel="DANIEL SILVA SERAFIM",
            telefone="11 2357-8480",
            data_informacao=datetime.date(2022, 11, 8),
            ano=2022,
            codigo_isin="BRIMMOCTF010",
            codigo_negociacao="IMMO13",
            tipo="Amortização",
            tipo_amortizacao="Parcial",
            ato_societario_aprovacao="Não",
            data_base=datetime.date(2022, 11, 8),
            valor_por_cota=decimal.Decimal("6.44393905"),
            data_pagamento=datetime.date(2022, 11, 16),
            periodo_referencia="novembro",
            isento_ir=False,
            data_aprovacao=None,
        ),
    ]

    assert_informe_rendimentos(373491, expected)


def test_informe_374888():
    expected = [
        InformeRendimentos(
            fundo="VECTOR QUELUZ LAJES CORPORATIVAS FUNDO DE INVESTIMENTO IMOB.",
            fundo_cnpj="13842683000176",
            administrador="PLANNER CORRETORA DE VALORES SA",
            administrador_cnpj="00806535000154",
            responsavel="Regiane Cristina de Souza",
            telefone="1121722574",
            codigo_isin="BRVLJSCTF020",
            codigo_negociacao="VLJS11",
            data_informacao=None,
            ano=2022,
            tipo="Amortização",
            tipo_amortizacao="Parcial",
            ato_societario_aprovacao="05/05/2022",
            data_base=datetime.date(2022, 11, 10),
            valor_por_cota=decimal.Decimal("23.9888159102366"),
            data_pagamento=datetime.date(2022, 11, 21),
            periodo_referencia="novembro",
            isento_ir=False,
            data_aprovacao=datetime.date(2022, 11, 10),
        ),
    ]

    assert_informe_rendimentos(374888, expected)


def test_informe_349275():
    expected = [
        InformeRendimentos(
            fundo="GALAPAGOS RECEBÍVEIS DO AGRONEGÓCIO - FIAGRO - FII",
            fundo_cnpj="37037297000170",
            administrador="Singulare Corretora de Valores e Titulos Mobiliarios S.A",
            administrador_cnpj="62285390000140",
            responsavel="Daniel Doll Lemos",
            telefone="(11) 2827-3905",
            codigo_isin="BRGCRACTF005",
            codigo_negociacao="GCRA11",
            tipo="Rendimento",
            data_aprovacao=datetime.date(2022, 9, 8),
            data_base=datetime.date(2022, 9, 8),
            data_pagamento=datetime.date(2022, 9, 15),
            valor_por_cota=decimal.Decimal("1.2"),
            periodo_referencia="agosto",
            ano=2022,
            isento_ir=True,
        ),
    ]

    assert_informe_rendimentos(349275, expected)


def test_informe_7212():
    expected = [
        InformeRendimentos(
            fundo="Rio Bravo Crédito Imobiliário II FI",
            fundo_cnpj="15769670000144",
            administrador="RIO BRAVO INVESTIMENTOS DTVM LTDA",
            administrador_cnpj="72600026000181",
            responsavel="Wagner Gonzalez",
            telefone="(11) 3509-6654",
            codigo_isin="BRRBVOCTF007",
            codigo_negociacao="RBVO11",
            tipo="Amortização",
            tipo_amortizacao="Parcial",
            data_aprovacao=datetime.date(2016, 12, 12),
            data_base=datetime.date(2016, 12, 12),
            data_pagamento=datetime.date(2016, 12, 20),
            valor_por_cota=decimal.Decimal("9.77628028"),
            periodo_referencia="20/12/2015 – 20/12/2016",
            ano=2016,
            isento_ir=False,
        ),
    ]

    assert_informe_rendimentos(7212, expected)
