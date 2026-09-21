import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from mercados.fundosnet import FundosNet, FundosNetError
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


def test_paginate_retry_sucesso_apos_504():
    fnet = FundosNet()
    resposta_504 = MagicMock(status_code=504, text="Gateway Timeout")
    resposta_200 = MagicMock(
        status_code=200,
        text='{"recordsTotal": 1, "data": [{"id": 1}]}',
        json=MagicMock(return_value={"recordsTotal": 1, "data": [{"id": 1}]}),
    )
    fnet.request = MagicMock(side_effect=[resposta_504, resposta_200])

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == [{"id": 1}]
    assert fnet.request.call_count == 2


def test_paginate_retry_sucesso_apos_resposta_200_com_erro():
    fnet = FundosNet()
    resposta_erro = MagicMock(
        status_code=200,
        text='{"error": "Internal error"}',
        json=MagicMock(return_value={"error": "Internal error"}),
    )
    resposta_valida = MagicMock(
        status_code=200,
        text='{"recordsTotal": 1, "data": [{"id": 2}]}',
        json=MagicMock(return_value={"recordsTotal": 1, "data": [{"id": 2}]}),
    )
    fnet.request = MagicMock(side_effect=[resposta_erro, resposta_valida])

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == [{"id": 2}]
    assert fnet.request.call_count == 2


def test_paginate_esgotamento_de_tentativas_lanca_fundosnet_error():
    fnet = FundosNet()
    resposta_500 = MagicMock(status_code=500, text="Internal Server Error")
    fnet.request = MagicMock(return_value=resposta_500)

    with pytest.raises(FundosNetError) as exc_info:
        list(fnet.paginate("pesquisar", max_retries=3, retry_delay=0.0))

    erro = exc_info.value
    erro_msg = str(erro)
    assert "pesquisar" in erro_msg
    assert "s=0" in erro_msg
    assert "l=200" in erro_msg
    assert "status=500" in erro_msg
    assert "Internal Server Error" in erro_msg
    assert erro.status_code == 500
    assert erro.url is not None and erro.url.endswith("pesquisar")
    assert erro.params == {"s": 0, "l": 200, "_": erro.params["_"]}
    assert fnet.request.call_count == 3


def test_paginate_retry_sucesso_apos_json_invalido():
    fnet = FundosNet()
    resposta_invalida = MagicMock(
        status_code=200,
        text="<html>Bad Gateway</html>",
        json=MagicMock(side_effect=ValueError("Expecting value")),
    )
    resposta_valida = MagicMock(
        status_code=200,
        text='{"recordsTotal": 1, "data": [{"id": 3}]}',
        json=MagicMock(return_value={"recordsTotal": 1, "data": [{"id": 3}]}),
    )
    fnet.request = MagicMock(side_effect=[resposta_invalida, resposta_valida])

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == [{"id": 3}]
    assert fnet.request.call_count == 2


def test_paginate_retry_sucesso_apos_request_exception():
    fnet = FundosNet()
    resposta_valida = MagicMock(
        status_code=200,
        text='{"recordsTotal": 1, "data": [{"id": 4}]}',
        json=MagicMock(return_value={"recordsTotal": 1, "data": [{"id": 4}]}),
    )
    fnet.request = MagicMock(side_effect=[requests.exceptions.ConnectionError("Connection aborted"), resposta_valida])

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == [{"id": 4}]
    assert fnet.request.call_count == 2


def test_paginate_retry_sucesso_apos_chave_faltante():
    fnet = FundosNet()
    resposta_sem_total = MagicMock(
        status_code=200,
        text='{"draw": 1}',
        json=MagicMock(return_value={"draw": 1}),
    )
    resposta_valida = MagicMock(
        status_code=200,
        text='{"recordsTotal": 1, "data": [{"id": 5}]}',
        json=MagicMock(return_value={"recordsTotal": 1, "data": [{"id": 5}]}),
    )
    fnet.request = MagicMock(side_effect=[resposta_sem_total, resposta_valida])

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == [{"id": 5}]
    assert fnet.request.call_count == 2


def test_paginate_termina_em_404():
    fnet = FundosNet()
    resposta_404 = MagicMock(status_code=404, text="Not Found")
    fnet.request = MagicMock(return_value=resposta_404)

    itens = list(fnet.paginate("pesquisar", retry_delay=0.0))
    assert itens == []
    assert fnet.request.call_count == 1
