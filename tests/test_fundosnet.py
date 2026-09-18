import datetime
from pathlib import Path
from unittest.mock import MagicMock

from mercados.fundosnet import FundosNet
from mercados.utils import BRT


def test_dados_protocolo_977453() -> None:
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


def test_get_csrf_token_sem_token_retorna_none_e_inicia_sessao():
    html_sem_csrf = """
    <html>
      <head><title>Gerenciador de Documentos</title></head>
      <body>
        <script>
          const csrf_token = $("meta[name='_csrf']").attr("content") || '';
          const csrfHeader = $("meta[name='_csrf_header']").attr("content") || '';
        </script>
      </body>
    </html>
    """
    fnet = FundosNet()
    fnet.request = MagicMock(return_value=MagicMock(text=html_sem_csrf))

    assert fnet.get_csrf_token() is None
    assert "CSRFToken" not in fnet.session.headers


def test_get_csrf_token_extrai_de_meta_tag():
    html_meta = """
    <html>
      <head>
        <meta name="_csrf" content="token-via-meta-tag-12345" />
      </head>
      <body></body>
    </html>
    """
    fnet = FundosNet()
    fnet.request = MagicMock(return_value=MagicMock(text=html_meta))

    assert fnet.get_csrf_token() == "token-via-meta-tag-12345"
    assert fnet.session.headers.get("CSRFToken") == "token-via-meta-tag-12345"


def test_get_csrf_token_legado_script():
    html_legado = """
    <html>
      <body>
        <script>
          var csrf_token = 'token-legado-script-67890';
        </script>
      </body>
    </html>
    """
    fnet = FundosNet()
    fnet.request = MagicMock(return_value=MagicMock(text=html_legado))

    assert fnet.get_csrf_token() == "token-legado-script-67890"
    assert fnet.session.headers.get("CSRFToken") == "token-legado-script-67890"
