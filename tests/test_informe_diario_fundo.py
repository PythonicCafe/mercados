import datetime
from decimal import Decimal
from pathlib import Path

from mercados.document import CotistaFundo, InformeDiarioFundo


def test_informe_diario_fundo():
    filename = Path(__file__).parent / "data" / "informe-diario-fundo-1.xml"
    with filename.open(mode="rb") as fobj:
        xml = fobj.read()
    doc = InformeDiarioFundo.from_xml(xml)
    expected = [
        InformeDiarioFundo(
            doc_codigo="1",
            doc_data_geracao=datetime.date(2024, 9, 12),
            doc_versao="3.0",
            data_competencia=datetime.date(2024, 9, 12),
            cotistas=90,
            fundo_cnpj="56746166000106",
            carteira=Decimal("12019612.96"),
            cota=Decimal("21.318556700000"),
            patrimonio_liquido=Decimal("12023665.98"),
            captado=Decimal("223844.85"),
            resgatado=Decimal("0.00"),
            saidas_previstas=Decimal("1806.34"),
            ativos_liquidaveis=Decimal("14365.58"),
            cotistas_significativos=[
                CotistaFundo(tipo="PJ", documento="11233045000122", participacao=Decimal("22.0300")),
                CotistaFundo(tipo="PJ", documento="29217282000165", participacao=Decimal("32.5200")),
                CotistaFundo(tipo="PJ", documento="44209582000196", participacao=Decimal("38.7500")),
            ],
            data_proximo_pl=datetime.date(2024, 9, 13),
        )
    ]
    assert doc == expected


def test_informe_diario_fundo_2():
    filename = Path(__file__).parent / "data" / "informe-diario-fundo-2.xml"
    with filename.open(mode="rb") as fobj:
        xml = fobj.read()
    doc = InformeDiarioFundo.from_xml(xml)
    expected = [
        InformeDiarioFundo(
            doc_codigo="1",
            doc_versao=None,
            data_competencia=datetime.date(2025, 7, 2),
            cotistas=391,
            fundo_cnpj="14120533000111",
            carteira=Decimal("33466867.48"),
            cota=Decimal("136.270511060000"),
            patrimonio_liquido=Decimal("34068990.47"),
            captado=Decimal("0.00"),
            resgatado=Decimal("0.00"),
            saidas_previstas=None,
            ativos_liquidaveis=None,
            cotistas_significativos=[],
            data_proximo_pl=None,
            doc_data_geracao=None,
            fundo="CAIXA ETF IBOVESPA FUNDO DE ÍNDICE - RESPONSABILIDADE LIMITADA",
            administradora="CAIXA ECONOMICA FEDERAL",
            administradora_cnpj="00360305000104",
        ),
    ]
    assert doc == expected
