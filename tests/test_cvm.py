import datetime
from unittest.mock import MagicMock

import pytest

from mercados.cvm import RAD, DocumentoEmpresa


def cria_registro_cru(
    codigo_empresa: str = "017388",
    empresa: str = "EMPRESA TESTE S.A.",
    categoria: str = "Emissor Estrangeiro  (entidade de investimentos)",
    subcategoria: str = "Assembleia  Geral",
    assunto: str = "<spanOrder>1  livre</spanOrder> AGO   - Ordinária",
    datahora_referencia: str = "<spanOrder>20260901</spanOrder> 01/09/2026",
    datahora_entrega: str = "<spanOrder>20260901</spanOrder> 01/09/2026 12:00",
    situacao: str = "Ativo  Normal",
    versao: str = "1",
    modalidade: str = "AP  Geral",
    tipo: str = "IPE  Outros",
    detalhe_publicacao: str = "CVM@!@Portal  Web#$#B3@!@Site  B3",
) -> str:
    campo_11 = (
        f"<i class='fi-download' onclick=\"OpenDownloadDocumentos('12345', '1', '67890', '{tipo}')\"></i>"
        "<i class='fi-page-search' onclick=\"OpenPopUpVer('frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega=67890')\"></i>"
        f"<i class='fi-info' onmouseover=\"mostraLocaisPublicacao(1, '{detalhe_publicacao}')\"></i>"
    )
    campos = [
        codigo_empresa,
        empresa,
        categoria,
        subcategoria,
        assunto,
        datahora_referencia,
        datahora_entrega,
        situacao,
        versao,
        modalidade,
        campo_11,
        "campo12",
    ]
    return "$&".join(campos)


def test_from_data_normaliza_categoria() -> None:
    registro = cria_registro_cru(categoria="Emissor Estrangeiro  (entidade de investimentos)")
    doc = DocumentoEmpresa.from_data(registro)
    assert doc.categoria == "Emissor Estrangeiro (entidade de investimentos)"


@pytest.mark.parametrize(
    "campo, valor_cru, valor_esperado",
    [
        (
            "categoria",
            "Emissor Estrangeiro  (entidade de investimentos)",
            "Emissor Estrangeiro (entidade de investimentos)",
        ),
        ("subcategoria", "Assembleia  Geral  Extraordinária", "Assembleia Geral Extraordinária"),
        ("situacao", "Ativo   Normal", "Ativo Normal"),
        ("modalidade", "Reapresentação   Espontânea", "Reapresentação Espontânea"),
        ("especie", "<spanOrder>1</spanOrder> AGO   - Ordinária", "AGO - Ordinária"),
        ("tipo", "IPE   Outros", "IPE Outros"),
    ],
)
def test_from_data_normaliza_campos_categoricos(campo: str, valor_cru: str, valor_esperado: str) -> None:
    kwargs = {}
    if campo == "especie":
        kwargs["assunto"] = valor_cru
    else:
        kwargs[campo] = valor_cru
    registro = cria_registro_cru(**kwargs)
    doc = DocumentoEmpresa.from_data(registro)
    assert getattr(doc, campo) == valor_esperado


def test_consistencia_categoria_com_rad_categorias() -> None:
    html_dropdown = """
    <html><body>
    <select id="cboCategorias">
      <option value="109">
         Emissor Estrangeiro  (entidade de investimentos)
      </option>
    </select>
    </body></html>
    """
    rad = RAD()
    mock_response = MagicMock()
    mock_response.content = html_dropdown.encode("utf-8")
    mock_response.raise_for_status.return_value = None
    rad.session.get = MagicMock(return_value=mock_response)

    categorias = rad.categorias()
    assert "Emissor Estrangeiro (entidade de investimentos)" in categorias

    registro = cria_registro_cru(categoria="Emissor Estrangeiro  (entidade de investimentos)")
    doc = DocumentoEmpresa.from_data(registro)
    assert doc.categoria in categorias


def test_from_data_nao_altera_texto_livre() -> None:
    registro = cria_registro_cru(
        assunto="<spanOrder>1  livre</spanOrder> AGO - Ordinária",
        detalhe_publicacao="CVM@!@Portal  Web#$#B3@!@Site  B3",
    )
    doc = DocumentoEmpresa.from_data(registro)
    assert doc.assunto == "1  livre"
    assert doc.detalhe_publicacao == "CVM|Portal  Web\nB3|Site  B3"


def test_uuid_com_e_sem_espacos_multiplos_sao_iguais() -> None:
    registro_com_espacos = cria_registro_cru(
        categoria="Emissor Estrangeiro  (entidade de investimentos)",
        subcategoria="Assembleia  Geral",
        assunto="<spanOrder>1  livre</spanOrder> AGO   - Ordinária",
        situacao="Ativo  Normal",
        modalidade="AP  Geral",
        tipo="IPE  Outros",
    )
    registro_sem_espacos = cria_registro_cru(
        categoria="Emissor Estrangeiro (entidade de investimentos)",
        subcategoria="Assembleia Geral",
        assunto="<spanOrder>1  livre</spanOrder> AGO - Ordinária",
        situacao="Ativo Normal",
        modalidade="AP Geral",
        tipo="IPE Outros",
    )
    doc_com_espacos = DocumentoEmpresa.from_data(registro_com_espacos)
    doc_sem_espacos = DocumentoEmpresa.from_data(registro_sem_espacos)
    assert doc_com_espacos.uuid == doc_sem_espacos.uuid


def test_rad_busca_categorias_none_envia_filtro_vazio() -> None:
    rad = RAD()
    rad.session.post = MagicMock(return_value=MagicMock(json=lambda: {"d": {"dados": "", "msgErro": ""}}))
    list(rad.busca(datetime.date(2026, 9, 1), datetime.date(2026, 9, 2), categorias=None))
    form_enviado = rad.session.post.call_args[1]["json"]
    assert form_enviado["categoria"] == ""


def test_rad_busca_categorias_vazia_envia_filtro_vazio() -> None:
    rad = RAD()
    rad.session.post = MagicMock(return_value=MagicMock(json=lambda: {"d": {"dados": "", "msgErro": ""}}))
    list(rad.busca(datetime.date(2026, 9, 1), datetime.date(2026, 9, 2), categorias=[]))
    form_enviado = rad.session.post.call_args[1]["json"]
    assert form_enviado["categoria"] == ""


def test_rad_busca_categorias_todas_filtra_alguns_documentos() -> None:
    rad = RAD()
    rad._categorias = {"TODAS": "-1"}
    rad.session.post = MagicMock(return_value=MagicMock(json=lambda: {"d": {"dados": "", "msgErro": ""}}))
    list(rad.busca(datetime.date(2026, 9, 1), datetime.date(2026, 9, 2), categorias=["TODAS"]))
    form_enviado = rad.session.post.call_args[1]["json"]
    assert form_enviado["categoria"] == "IPE_-1_-1_-1"
