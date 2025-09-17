import datetime
from pathlib import Path

from mercados.fundosnet import FundosNet
from mercados.utils import BRT


def test_dados_protocolo_977453():
    filename = Path(__file__).parent / "data" / "protocolo_977453.html"
    with filename.open(mode="rb") as fobj:
        content = fobj.read()
    fnet = FundosNet()
    result = fnet._extrai_dados_protocolo(content)
    expected = {
        "administrador": "BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTV",
        "administrador_cnpj": "59281253000123",
        "data_cancelamento": None,
        "data_entrega": datetime.datetime(2025, 8, 25, 18, 10, 0, tzinfo=BRT),
        "data_reapresentacao": None,
        "data_referencia": "31/07/2025",
        "fundo": "FUNDO DE INVESTIMENTO IMOBILIÁRIO VBI CRÉDITO MULTIESTRATÉGIA - RESPONSABILIDADE LIMITADA",
        "fundo_cnpj": "51802350000102",
        "identificacao_documento": "Relatórios - Relatório Gerencial",
        "locais_publicacao": "CVM Web",
        "motivo_cancelamento": None,
        "motivo_reapresentacao": None,
        "protocolo_recebimento": "51802350000102-REL25082025V01-000977453",
        "versao": "1",
    }
    assert result == expected
