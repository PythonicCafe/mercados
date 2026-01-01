import datetime
import re
import time
from functools import cached_property
from urllib.parse import urljoin

from lxml.html import document_fromstring

from mercados import choices
from mercados.document import DocumentMeta
from mercados.utils import BRT, USER_AGENT, create_session, parse_date, remove_acentos, remove_espacos

_REGEXP_CSRF_TOKEN = re.compile("""csrf_token ?= ?["']([^"']+)["']""")
_REGEXP_CERTIFICADO_DESCRICAO = re.compile(
    r"^(.*) (CR|CRI|CRA|DEB|OTS) Emissão:(.*) Série(?:\(s\))?:(.*) ([0-9]{2}/[0-9]{4}) (.*)$"
)
_REGEXP_XML_ENCODING = re.compile('encoding="([^"]+)"')
_MODELOS_NOMES_ARQUIVOS = {
    "id": "{doc_id}{extension}",
    "id-partes": "{p4}/{p3}/{p2}/{p1}/{doc_id8}",
    "data": "{year}/{month}/{day}/{doc_id}",
}
_DESCRICAO_CLI = "Busca e baixa documentos publicados no FundosNET"


def parse_certificado_descricao(value):
    result = _REGEXP_CERTIFICADO_DESCRICAO.findall(value)
    if not result:
        raise ValueError(f"Valor informado não segue padrão de descrição de certificado: {repr(value)}")
    return {key: value for key, value in zip("nome tipo emissao serie data codigo".split(), result[0])}


def assert_in(nome_variavel, valor, valores_possiveis):
    if valor not in valores_possiveis:
        valores = ", ".join(valores_possiveis)
        raise ValueError(f"Valor inválido para `{nome_variavel}`: {repr(valor)} (esperado: {valores})")


def format_document_path(pattern: str, doc: DocumentMeta, content_type: str):
    doc_id = int(doc.id)
    doc_id8 = f"{int(doc_id):08d}"
    extension = ""
    if content_type is not None:
        extension = {
            "application/pdf": "pdf",
            "application/x-zip-compressed": "zip",
            "application/zip": "zip",
            "text/xml": "xml",
        }.get(content_type)
        if not extension and "/" in content_type:
            extension = content_type.split("/")[-1]
        if extension:
            extension = f".{extension}"
    return pattern.format(
        **{
            "doc_id": doc_id,
            "doc_id8": doc_id8,
            "p4": doc_id8[-2:],
            "p3": doc_id8[-4:-2],
            "p2": doc_id8[-6:-4],
            "p1": doc_id8[-8:-6],
            "year": doc.datahora_entrega.year,
            "month": f"{doc.datahora_entrega.month:02d}",
            "day": f"{doc.datahora_entrega.day:02d}",
            "extension": extension,
        }
    )


# TODO: implementar crawler/parser para antes de 2016
# <https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/ResultListaPartic.aspx?TPConsulta=9>


class FundosNet:
    """Scraper de metadados dos documentos publicados no FundoNet

    https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM
    """

    base_url = "https://fnet.bmfbovespa.com.br/fnet/publico/"

    def __init__(
        self, user_agent: str = USER_AGENT, proxy: str | None = None, timeout: float = 15.0, verify_ssl: bool = False
    ) -> None:
        self._user_agent = user_agent
        self._proxy = proxy
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session = None
        self.draw = 0

    @property
    def session(self):
        if self._session is None:
            self._session = create_session(user_agent=self._user_agent, proxy=self._proxy)
            self._session.headers["CSRFToken"] = self.get_csrf_token()
        return self._session

    def baixa_xml(self, url: str, timeout: float | None = None, max_tries: int = 5, wait_between_errors: float = 0.5):
        """Baixa um XML do FundosNet a partir da URL e decodifica-o corretamente

        Serão feitas, no total, `max_tries` tentativas, pois em alguns casos a CloudFlare retorna um erro HTTP 5xx.
        """
        if timeout is None:
            timeout = self.timeout
        tried = 0
        while tried < max_tries:
            # Forçar o cabeçalho `Accept` faz com que a resposta não seja enviada em base64
            response = self.session.get(url, headers={"Accept": "application/xhtml+xml"}, timeout=timeout)
            tried += 1
            if response.status_code < 500:
                break
            else:
                time.sleep(wait_between_errors)
        response.raise_for_status()
        content = response.content
        first_line = content.split(b"\n", maxsplit=1)[0].decode("ascii")
        result = _REGEXP_XML_ENCODING.findall(first_line)
        encoding = result[0] if result else "utf-8"
        return content.decode(encoding)

    def request(self, method, path, headers=None, params=None, data=None, json=None, xhr=False):
        params = params or {}
        headers = headers or {}
        if xhr:
            self.draw += 1
            params["d"] = self.draw
            headers["X-Requested-With"] = "XMLHttpRequest"
        return self.session.request(
            method,
            urljoin(self.base_url, path),
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

    @cached_property
    def main_page(self):
        response = self.request("GET", "abrirGerenciadorDocumentosCVM", xhr=False)
        return response.text

    def get_csrf_token(self):
        # TODO: expires crsf_token after some time
        matches = _REGEXP_CSRF_TOKEN.findall(self.main_page)
        if not matches:
            raise RuntimeError("Cannot find CSRF token")

        return matches[0]

    @cached_property
    def categories(self):
        tree = document_fromstring(self.main_page)
        return {
            option.xpath("./text()")[0].strip(): int(option.xpath("./@value")[0])
            for option in tree.xpath("//select[@id = 'categoriaDocumento']/option")
        }

    @cached_property
    def fund_types(self):
        # TODO: add `(0, "Todos")`?
        tree = document_fromstring(self.main_page)
        options = tree.xpath("//select[@id = 'tipoFundo']/option")
        result = {}
        for option in options:
            key = option.xpath("./text()")[0].strip()
            value = option.xpath("./@value")[0].strip()
            if not value:
                key = "Todos"
            else:
                value = int(value)
            result[key] = value
        return result

    @cached_property
    def types(self):
        result = {}
        for categoria_id in self.categories.values():
            result[categoria_id] = []
            for tipo in choices.FUNDO_TIPO:
                if tipo[0] == 0:
                    continue
                response = self.request(
                    "GET",
                    "listarTodosTiposPorCategoriaETipoFundo",
                    params={"idTipoFundo": tipo[0], "idCategoria": categoria_id},
                    xhr=True,
                )
                for row in response.json():
                    row["descricao"] = row["descricao"].strip()
                    result[categoria_id].append(row)
        return result

    def paginate(self, path, params=None, xhr=True, items_per_page=200):
        params = params or {}
        params["s"] = 0  # rows to skip
        params["l"] = items_per_page  # page length
        params["_"] = int(time.time() * 1000)
        total_rows, finished = None, False
        while not finished:
            response = self.request("GET", path, params=params, xhr=xhr)
            if response.status_code == 404:  # Finished (wrong page?)
                return
            response_data = response.json()
            if total_rows is None:
                total_rows = response_data["recordsTotal"]
            data = response_data["data"]
            yield from data
            params["s"] += len(data)
            params["_"] = int(time.time() * 1000)
            finished = params["s"] >= total_rows

    def fundos(self):
        yield from self._listar_fundos(certs=False)

    def certificados(self):
        for certificado in self._listar_fundos(certs=True):
            certificado.update(**parse_certificado_descricao(certificado["text"]))
            yield certificado

    def _listar_fundos(self, certs: bool):
        params = {
            "term": "",
            "page": 1,
            "idTipoFundo": "0",
            "idAdm": "0",
            "paraCerts": str(certs).lower(),
            "_": int(time.time() * 1000),
        }
        while True:
            response = self.request("GET", "listarFundos", xhr=True, params=params)
            data = response.json()
            yield from data["results"]
            if data["more"]:
                params["page"] += 1
            else:
                break

    # TODO: unificar métodos de busca
    def busca(
        self,
        categoria="Todos",
        tipo="Todos",
        tipo_fundo="Todos",
        cnpj=None,
        situacao=None,
        inicio=None,
        fim=None,
        campo_ordenacao="dataEntrega",
        ordenacao="desc",
        itens_por_pagina=200,
    ):
        # TODO: traduzir parâmetros e nome do método para Português
        ordenacao_choices = ("asc", "desc")
        campo_ordenacao_choices = (
            "denominacaoSocial",
            "CategoriaDescricao",
            "tipoDescricao",
            "especieDocumento",
            "dataReferencia",
            "dataEntrega",
            "situacaoDocumento",
            "versao",
            "modalidade",
        )
        ordenacao = str(ordenacao or "").strip().lower()
        assert_in("ordenacao", ordenacao, ordenacao_choices)
        assert_in("campo_ordenacao", campo_ordenacao, campo_ordenacao_choices)
        assert_in("categoria", categoria, choices.DOCUMENTO_CATEGORIA_DICT)
        categoria_id = choices.DOCUMENTO_CATEGORIA_DICT[categoria]
        if tipo != "Todos":
            assert_in("tipo", tipo, choices.DOCUMENTO_TIPO_DICT)
        tipo_id = choices.DOCUMENTO_TIPO_DICT[tipo]
        assert_in("tipo_fundo", tipo_fundo, choices.FUNDO_TIPO_DICT)
        tipo_fundo_id = choices.FUNDO_TIPO_DICT[tipo_fundo]
        situacao_choices = "AIC"
        situacao = str(situacao or "").upper().strip()
        if situacao:
            assert_in("situacao", situacao, situacao_choices)
        if tipo_fundo_id == 0:
            tipo_fundo_id = ""
        if isinstance(inicio, str):
            inicio = parse_date("iso-date", inicio)
        if isinstance(fim, str):
            fim = parse_date("iso-date", fim)
        # TODO: filter other fields, like:
        # - administrador
        # - cnpj
        # - cnpjFundo
        # - idEspecieDocumento
        # - situacao
        # (there are others)
        # TODO: get all possible especie
        # TODO: get all administradores https://fnet.bmfbovespa.com.br/fnet/publico/buscarAdministrador?term=&page=2&paginaCertificados=false&_=1655592601540
        params = {
            f"o[0][{campo_ordenacao}]": ordenacao,
            "idCategoriaDocumento": categoria_id,
            "idTipoDocumento": tipo_id,
            "tipoFundo": tipo_fundo_id,
            "idEspecieDocumento": "0",
            "dataInicial": inicio.strftime("%d/%m/%Y") if inicio else "",
            "dataFinal": fim.strftime("%d/%m/%Y") if fim else "",
        }
        if cnpj is not None:
            params["cnpj"] = params["cnpjFundo"] = cnpj
        if situacao:
            params["situacao"] = situacao
        result = self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params=params,
            xhr=True,
            items_per_page=itens_por_pagina,
        )
        for row in result:
            yield DocumentMeta.from_json(row)

    def busca_certificado(
        self,
        inicio=None,
        fim=None,
        campo_ordenacao="dataEntrega",
        ordenacao="desc",
        itens_por_pagina=200,
    ):
        assert ordenacao in ("asc", "desc")
        assert campo_ordenacao in (
            "denominacaoSocial",
            "CategoriaDescricao",
            "tipoDescricao",
            "especieDocumento",
            "dataReferencia",
            "dataEntrega",
            "situacaoDocumento",
            "versao",
            "modalidade",
        )
        # TODO: filtrar por outros campos
        if isinstance(inicio, str):
            inicio = parse_date("iso-date", inicio)
        if isinstance(fim, str):
            fim = parse_date("iso-date", fim)
        params = {
            f"o[0][{campo_ordenacao}]": ordenacao,
            "idCategoriaDocumento": "0",
            "idTipoDocumento": "0",
            "idEspecieDocumento": "0",
            "dataInicial": inicio.strftime("%d/%m/%Y") if inicio else "",
            "dataFinal": fim.strftime("%d/%m/%Y") if fim else "",
            "paginaCertificados": "true",
        }
        result = self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params=params,
            xhr=True,
            items_per_page=itens_por_pagina,
        )
        for row in result:
            yield DocumentMeta.from_json(row)

    def _extrai_dados_protocolo(self, content: bytes):
        tree = document_fromstring(content)
        tabelas = tree.xpath("//table[caption]")
        row = {}
        for tabela in tabelas:
            titulo = remove_espacos(tabela.xpath("string(./caption)"))
            if titulo in ("Informações do Documento", "Informações Adicionais"):
                titulo = "doc"
            else:
                titulo = titulo.lower()
            for tr in tabela.xpath(".//tr"):
                tds = []
                for td in tr.xpath(".//td"):
                    tds.append(td.xpath("string(.)").strip())
                assert len(tds) == 2, f"Valor incorreto de células na tabela: {len(tds)}"
                if tds[0].lower() == "nome":
                    key = titulo
                else:
                    key = f"{titulo}_{tds[0]}".lower().replace(" ", "_")
                key = remove_acentos(key)
                for item in ("da", "de", "do"):
                    key = key.replace(f"_{item}_", "_")
                if key.startswith("doc_"):
                    key = key[4:]
                row[key] = remove_espacos(tds[1]) or None
        for key in ("data_entrega", "data_reapresentacao", "data_cancelamento"):
            if key not in row:
                continue
            row[key] = datetime.datetime.strptime(row[key], "%d/%m/%Y %H:%M").replace(tzinfo=BRT)
        for key in ("motivo_reapresentacao", "data_reapresentacao", "data_cancelamento", "motivo_cancelamento"):
            if key not in row:
                row[key] = None
        return row

    def dados_protocolo(self, doc_id):
        """Coleta informações do protocolo de entrega para um determinado documento"""
        response = self.request("GET", "visualizarProtocoloDocumentoCVM", xhr=False, params={"idDocumento": doc_id})
        return self._extrai_dados_protocolo(response.content)


def _configura_parser_cli(parser):
    from pathlib import Path

    from mercados.utils import parse_iso_date

    # TODO: dividir em vários subcomandos
    modelos_str = "; ".join(f"{key}: {value}" for key, value in _MODELOS_NOMES_ARQUIVOS.items())
    categoria_choices = sorted([item[1] for item in choices.DOCUMENTO_CATEGORIA])
    tipo_choices = [item[1] for item in choices.DOCUMENTO_TIPO]
    parser.add_argument(
        "-m",
        "--modelo-nome-arquivo",
        default="id",
        metavar="campo",
        choices=["id", "id-partes", "data"],
        help=f"Modelo para usar no nome do arquivo a ser baixado. Opções: {modelos_str}",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        help="Se especificado, baixa os documentos encontrados nessa pasta",
    )
    parser.add_argument(
        "-i",
        "--inicio",
        "--data-inicial",
        metavar="data",
        type=parse_iso_date,
        default=datetime.date(2016, 1, 1),
        help="Data de início (de publicação do documento) para a busca no formato YYYY-MM-DD",
    )
    parser.add_argument(
        "-f",
        "--fim",
        "--data-final",
        metavar="data",
        type=parse_iso_date,
        default=datetime.datetime.now().date(),
        help="Data de fim (de publicação do documento) para a busca no formato YYYY-MM-DD",
    )
    parser.add_argument(
        "-c",
        "--categoria",
        type=str,
        choices=categoria_choices,
        metavar="categoria",
        help=f"Filtra pela categoria do documento. Opções: {'; '.join(categoria_choices)}",
    )
    parser.add_argument(
        "-t",
        "--tipo",
        type=str,
        choices=tipo_choices,
        metavar="tipo",
        help=f"Filtra pelo tipo de documento. Opções: {'; '.join(tipo_choices)}",
    )
    parser.add_argument("csv_filename", type=Path, help="Arquivo CSV com os documentos encontrados")


def main(args):
    import csv
    from pathlib import Path

    from mercados.utils import day_range

    data_inicial = args.inicio
    data_final = args.fim
    tipo = args.tipo
    categoria = args.categoria
    download_path = args.path
    modelo_nome = args.modelo_nome_arquivo
    csv_filename = args.csv_filename
    datas_a_pesquisar = [
        dia
        for dia in day_range(data_inicial, data_final + datetime.timedelta(days=1))
        if dia.day == 1 or dia in (data_inicial, data_final)
    ]
    modelo_nome_arquivo = _MODELOS_NOMES_ARQUIVOS[modelo_nome]
    if download_path:
        download_path.mkdir(parents=True, exist_ok=True)
    csv_filename.parent.mkdir(parents=True, exist_ok=True)
    filtros = {}
    if categoria:
        filtros["categoria"] = categoria
    if tipo:
        filtros["tipo"] = tipo

    fnet = FundosNet()
    with csv_filename.open(mode="w") as csv_fobj:
        writer = None
        for inicio, fim in zip(datas_a_pesquisar, datas_a_pesquisar[1:]):
            fim = fim - datetime.timedelta(days=1) if fim != data_final else fim
            filtros["inicio"] = inicio
            filtros["fim"] = fim
            resultado = fnet.busca(**filtros)
            for documento in resultado:
                row = documento.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
                if download_path:
                    response = fnet.session.get(documento.url, verify=False)
                    content_type = response.headers.get("Content-Type")
                    filename = download_path / Path(format_document_path(modelo_nome_arquivo, documento, content_type))
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    with filename.open(mode="wb") as fobj:
                        fobj.write(response.content)
    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=_DESCRICAO_CLI)
    _configura_parser_cli(parser)
    args = parser.parse_args()
    sys.exit(main(args))
