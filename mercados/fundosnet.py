import datetime
import re
import time
from functools import cached_property
from urllib.parse import urljoin

from lxml.html import document_fromstring

from . import choices
from .document import DocumentMeta
from .utils import create_session

REGEXP_CSRF_TOKEN = re.compile("""csrf_token ?= ?["']([^"']+)["']""")
REGEXP_CERTIFICADO_DESCRICAO = re.compile(
    r"^(.*) (CR|CRI|CRA|DEB|OTS) Emissão:(.*) Série(?:\(s\))?:(.*) ([0-9]{2}/[0-9]{4}) (.*)$"
)


def parse_certificado_descricao(value):
    result = REGEXP_CERTIFICADO_DESCRICAO.findall(value)
    if not result:
        raise ValueError(f"Valor informado não segue padrão de descrição de certificado: {repr(value)}")
    return {key: value for key, value in zip("nome tipo emissao serie data codigo".split(), result[0])}


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

    def __init__(self, timeout=5, verify_ssl=False):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = create_session()
        self.session.headers["CSRFToken"] = self.csrf_token
        self.draw = 0

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

    @cached_property
    def csrf_token(self):
        # TODO: expires crsf_token after some time
        matches = REGEXP_CSRF_TOKEN.findall(self.main_page)
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
        for category_id in self.categories.values():
            result[category_id] = []
            for tipo in choices.FUNDO_TIPO:
                if tipo[0] == 0:
                    continue
                response = self.request(
                    "GET",
                    "listarTodosTiposPorCategoriaETipoFundo",
                    params={"idTipoFundo": tipo[0], "idCategoria": category_id},
                    xhr=True,
                )
                for row in response.json():
                    row["descricao"] = row["descricao"].strip()
                    result[category_id].append(row)
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

    # TODO: unify search methods
    def search(
        self,
        category="Todos",
        type_="Todos",
        fund_type="Todos",
        start_date=None,
        end_date=None,
        ordering_field="dataEntrega",
        order="desc",
        items_per_page=200,
    ):
        assert order in ("asc", "desc")
        assert ordering_field in (
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
        assert category in choices.DOCUMENTO_CATEGORIA_DICT
        category_id = choices.DOCUMENTO_CATEGORIA_DICT[category]
        assert type_ == "Todos" or type_ in choices.DOCUMENTO_TIPO_DICT
        type_id = choices.DOCUMENTO_TIPO_DICT[type_]
        assert fund_type in choices.FUNDO_TIPO_DICT
        fund_type_id = choices.FUNDO_TIPO_DICT[fund_type]
        if fund_type_id == 0:
            fund_type_id = ""
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
            f"o[0][{ordering_field}]": order,
            "idCategoriaDocumento": category_id,
            "idTipoDocumento": type_id,
            "tipoFundo": fund_type_id,
            "idEspecieDocumento": "0",
            "dataInicial": start_date.strftime("%d/%m/%Y") if start_date else "",
            "dataFinal": end_date.strftime("%d/%m/%Y") if end_date else "",
        }
        result = self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params=params,
            xhr=True,
            items_per_page=items_per_page,
        )
        for row in result:
            yield DocumentMeta.from_json(row)

    def search_certificate(
        self,
        start_date=None,
        end_date=None,
        ordering_field="dataEntrega",
        order="desc",
        items_per_page=200,
    ):
        assert order in ("asc", "desc")
        assert ordering_field in (
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
        # TODO: filter other fields
        params = {
            f"o[0][{ordering_field}]": order,
            "idCategoriaDocumento": "0",
            "idTipoDocumento": "0",
            "idEspecieDocumento": "0",
            "dataInicial": start_date.strftime("%d/%m/%Y") if start_date else "",
            "dataFinal": end_date.strftime("%d/%m/%Y") if end_date else "",
            "paginaCertificados": "true",
        }
        result = self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params=params,
            xhr=True,
            items_per_page=items_per_page,
        )
        for row in result:
            yield DocumentMeta.from_json(row)


if __name__ == "__main__":
    import argparse
    import csv
    from dataclasses import asdict
    from pathlib import Path

    from .utils import day_range, parse_iso_date

    modelos_nomes_arquivos = {
        "id": "{doc_id}{extension}",
        "id-partes": "{p4}/{p3}/{p2}/{p1}/{doc_id8}",
        "data": "{year}/{month}/{day}/{doc_id}",
    }
    modelos_str = "; ".join(f"{key}: {value}" for key, value in modelos_nomes_arquivos.items())
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modelo-nome-arquivo",
        "-m",
        default="id",
        choices=["id", "id-partes", "data"],
        help=f"Modelo para usar no nome do arquivo a ser baixado.\n{modelos_str}",
    )
    parser.add_argument(
        "--download-path", "-d", type=Path, help="Se especificado, baixa os documentos encontrados nessa pasta"
    )
    parser.add_argument(
        "--data-inicial",
        "-i",
        type=parse_iso_date,
        default=datetime.date(2016, 1, 1),
        help="Data de início (de publicação do documento) para a busca",
    )
    parser.add_argument(
        "--data-final",
        "-f",
        type=parse_iso_date,
        default=datetime.datetime.now().date(),
        help="Data de fim (de publicação do documento) para a busca",
    )
    parser.add_argument(
        "--categoria",
        "-c",
        type=str,
        choices=[item[1] for item in choices.DOCUMENTO_CATEGORIA],
        metavar="",
        help="Filtra pela categoria do documento",
    )
    parser.add_argument(
        "--tipo",
        "-t",
        type=str,
        choices=[item[1] for item in choices.DOCUMENTO_TIPO],
        metavar="",
        help="Filtra pelo tipo de documento",
    )
    parser.add_argument("csv_filename", type=Path, help="Arquivo CSV com os documentos encontrados")
    args = parser.parse_args()
    data_inicial, data_final = args.data_inicial, args.data_final
    datas_a_pesquisar = [
        dia
        for dia in day_range(data_inicial, data_final + datetime.timedelta(days=1))
        if dia.day == 1 or dia in (data_inicial, data_final)
    ]
    modelo_nome_arquivo = modelos_nomes_arquivos[args.modelo_nome_arquivo]
    download_path = args.download_path
    if download_path:
        download_path.mkdir(parents=True, exist_ok=True)
    csv_filename = args.csv_filename
    csv_filename.parent.mkdir(parents=True, exist_ok=True)
    filters = {}
    if args.categoria:
        filters["category"] = args.categoria
    if args.tipo:
        filters["type_"] = args.tipo

    fnet = FundosNet()
    with csv_filename.open(mode="w") as csv_fobj:
        writer = None
        for inicio, fim in zip(datas_a_pesquisar, datas_a_pesquisar[1:]):
            fim = fim - datetime.timedelta(days=1) if fim != data_final else fim
            filters["start_date"] = inicio  # TODO: renomear parâmetro para Português
            filters["end_date"] = fim  # TODO: renomear parâmetro para Português
            resultado = fnet.search(**filters)
            for documento in resultado:
                row = asdict(documento)
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
