import csv
import datetime
import re
import time
from collections import OrderedDict
from functools import cached_property
from urllib.parse import urljoin

import requests
import rows
from lxml.html import document_fromstring
from rows.utils.download import Download, Downloader

from . import choices
from .document import DocumentMeta


REGEXP_CSRF_TOKEN = re.compile("""csrf_token ?= ?["']([^"']+)["']""")


class PtBrBoolField(rows.fields.BoolField):
    @classmethod
    def deserialize(cls, value):
        value = str(value or "").strip().lower()
        if value == "s":
            return True
        elif value == "n":
            return False


class PtBrDateTimeField(rows.fields.Field):
    TYPE = (datetime.datetime,)

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        return value.isoformat() if value is not None else ""

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super().deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        return datetime.datetime.strptime(value, "%d/%m/%Y %H:%M")


field_types = OrderedDict(
    [
        ("id", rows.fields.IntegerField),
        ("descricaoFundo", rows.fields.TextField),
        ("categoriaDocumento", rows.fields.TextField),
        ("tipoDocumento", rows.fields.TextField),
        ("especieDocumento", rows.fields.TextField),
        ("dataReferencia", rows.fields.TextField),
        ("dataEntrega", PtBrDateTimeField),
        ("status", rows.fields.TextField),
        ("descricaoStatus", rows.fields.TextField),
        ("analisado", PtBrBoolField),
        ("situacaoDocumento", rows.fields.TextField),
        ("assuntos", rows.fields.TextField),
        ("altaPrioridade", rows.fields.BoolField),
        ("formatoDataReferencia", rows.fields.IntegerField),
        ("versao", rows.fields.IntegerField),
        ("modalidade", rows.fields.TextField),
        ("descricaoModalidade", rows.fields.TextField),
        ("nomePregao", rows.fields.TextField),
        ("informacoesAdicionais", rows.fields.TextField),
        ("arquivoEstruturado", rows.fields.TextField),
        ("formatoEstruturaDocumento", rows.fields.TextField),
        ("nomeAdministrador", rows.fields.TextField),
        ("cnpjAdministrador", rows.fields.TextField),
        ("cnpjFundo", rows.fields.TextField),
        ("idTemplate", rows.fields.IntegerField),
        ("idSelectNotificacaoConvenio", rows.fields.TextField),
        ("idSelectItemConvenio", rows.fields.IntegerField),
        ("indicadorFundoAtivoB3", rows.fields.BoolField),
        ("idEntidadeGerenciadora", rows.fields.TextField),
        ("ofertaPublica", rows.fields.TextField),
        ("numeroEmissao", rows.fields.TextField),
        ("tipoPedido", rows.fields.TextField),
        ("dda", rows.fields.TextField),
    ]
)


# TODO: implementar crawler/parser para antes de 2016
# <https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/ResultListaPartic.aspx?TPConsulta=9>

# https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM
class FundosNet:
    base_url = "https://fnet.bmfbovespa.com.br/fnet/publico/"

    def __init__(self, user_agent="mercado/python"):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.session.headers["CSRFToken"] = self.csrf_token
        self.draw = 0

    def request(
        self, method, path, headers=None, params=None, data=None, json=None, xhr=False
    ):
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
            response = self.request(
                "GET",
                "listarTodosTiposPorCategoria",
                params={"idCategoria": category_id},
                xhr=True,
            )
            result[category_id] = []
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
            response_data = response.json()
            if total_rows is None:
                total_rows = response_data["recordsTotal"]
            data = response_data["data"]
            yield from data
            params["s"] += len(data)
            params["_"] = int(time.time() * 1000)
            finished = params["s"] >= total_rows

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
            "b3CategoriaDescricao",
            "denominacaoSocial",
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
        result = self.paginate(
            path="pesquisarGerenciadorDocumentosDados",
            params={
                f"o[0][{ordering_field}]": order,
                "idCategoriaDocumento": category_id,
                "idTipoDocumento": type_id,
                "tipoFundo": fund_type_id,
                "idEspecieDocumento": "0",
                "dataInicial": start_date.strftime("%d/%m/%Y") if start_date else "",
                "dataFinal": end_date.strftime("%d/%m/%Y") if end_date else "",
            },
            xhr=True,
            items_per_page=items_per_page,
        )
        for row in result:
            yield DocumentMeta.from_json(row)


def download_url(document_id):
    return f"https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id={document_id}"


def download(document_ids, path):
    downloader = Downloader.subclasses()["aria2c"](path=path)
    for doc_id in document_ids:
        downloader.add(Download(url=download_url(doc_id), filename=str(doc_id)))
    downloader.run()


if __name__ == "__main__":
    import argparse
    from dataclasses import asdict
    from pathlib import Path

    from rows.utils import CsvLazyDictWriter, open_compressed
    from rows.utils.date import date_range
    from rows.utils.download import Downloader, Download
    from rows.plugins.utils import ipartition
    from tqdm import tqdm

    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--download-path")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument(
        "--category", choices=[item[1] for item in choices.DOCUMENTO_CATEGORIA]
    )
    parser.add_argument(
        "--document-type", choices=[item[1] for item in choices.DOCUMENTO_TIPO]
    )
    parser.add_argument("output_filename")
    args = parser.parse_args()
    if args.start_date:
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    else:
        start_date = datetime.date(2016, 1, 1)
    if args.end_date:
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        end_date = datetime.datetime.now().date()
    months = list(date_range(start_date, end_date, step="monthly"))
    if months[-1] != end_date:
        months.append(end_date)
    download_path = args.download_path
    if download_path:
        download_path = Path(download_path)
        if not download_path.exists():
            download_path.mkdir(parents=True)

    filters = {}
    if args.category:
        filters["category"] = args.category
    if args.document_type:
        filters["type_"] = args.document_type
    fnet = FundosNet()
    progress = tqdm()
    writer = CsvLazyDictWriter(args.output_filename)
    counter = 0
    for start, stop in zip(months, months[1:]):
        stop = stop - datetime.timedelta(days=1) if stop != end_date else stop
        progress.desc = f"Downloading {start} to {stop}"
        filters["start_date"] = start
        filters["end_date"] = stop
        result = fnet.search(**filters)
        for row in result:
            counter += 1
            writer.writerow(asdict(row))
            progress.update()
    writer.close()

    if download_path:
        progress = tqdm(desc="Downloading files", total=counter)
        fobj = open_compressed(args.output_filename)
        reader = csv.DictReader(fobj)
        for batch in ipartition(reader, args.batch_size):
            downloader = Downloader.subclasses()["aria2c"](path=download_path, quiet=True)
            for row in batch:
                downloader.add(Download(url=download_url(row["id"]), filename=row["id"]))
            downloader.run()
            progress.update(len(batch))
        progress.close()
