import datetime
from decimal import Decimal
from pathlib import Path

from mercados.ibge import IBGE

DATA_PATH = Path(__file__).parent / "data"


def assert_data(arquivo: Path, ultimo_disponivel: datetime.date):
    # Os arquivos foram baixados em 2025-09-29
    with arquivo.open(mode="rb") as fobj:
        content = fobj.read()
    ibge = IBGE()
    resultado = ibge._extrai_planilha_indice(content)
    datas = [taxa.data for taxa in resultado]
    assert datas == sorted(datas)
    assert resultado[0].data == datetime.date(1993, 12, 15)
    assert resultado[0].valor == Decimal("100.00")
    assert resultado[-1].data == ultimo_disponivel
    primeiro_disponivel = datetime.date(1993, 12, 15)
    meses = (
        ultimo_disponivel.year * 12
        + ultimo_disponivel.month
        - (primeiro_disponivel.year * 12 + primeiro_disponivel.month)
        + 1
    )
    assert len(resultado) == meses


def test_extrai_planilha_indice_ipca():
    assert_data(arquivo=DATA_PATH / "ipca_SerieHist.zip", ultimo_disponivel=datetime.date(2025, 8, 15))


def test_extrai_planilha_indice_ipca15():
    assert_data(arquivo=DATA_PATH / "ipca-15_SerieHist.zip", ultimo_disponivel=datetime.date(2025, 9, 15))


def test_extrai_planilha_indice_inpc():
    assert_data(arquivo=DATA_PATH / "inpc_SerieHist.zip", ultimo_disponivel=datetime.date(2025, 8, 15))
