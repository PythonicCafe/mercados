import csv
import datetime
import io
import re
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import urljoin

from lxml.html import document_fromstring

from .utils import (
    BRT,
    REGEXP_CNPJ_SEPARATORS,
    REGEXP_SPACES,
    create_session,
    download_files,
    parse_date,
    parse_iso_date,
    slug,
)

REGEXP_ASSUNTO = re.compile("^<spanOrder>(.*)</spanOrder>(.*)$", flags=re.DOTALL)
REGEXP_EMPRESAS = re.compile("{ key:'([^']+)', value:'([^']+)'}", flags=re.DOTALL)
REGEXP_DATAHORA = re.compile(
    r"^<spanOrder>[0-9]+</spanOrder> ([0-9]+/[0-9]+/[0-9]+)\s?([0-9]+:[0-9]+)?$", flags=re.DOTALL
)
REGEXP_SEM_PARAMETROS = re.compile(r"^[a-zA-Z0-9_]+\(\)$", flags=re.DOTALL)
REGEXP_PARAMETROS = re.compile(r"^([a-zA-Z0-9_]+)\((.*?)\)$", flags=re.DOTALL)
REGEXP_PARAMETROS_INTERNA = re.compile(r"'(.*?)'|(\d+)", flags=re.DOTALL)
REGEXP_INFO_FUNCTION = re.compile('''class='fi-info'[^>]*onmouseover="([^>]*)"''', flags=re.DOTALL)


@dataclass
class InformeDiarioFundo:
    fundo_cnpj: str
    data_competencia: datetime.date
    valor_captado: Decimal
    valor_resgatado: Decimal
    patrimonio_liquido: Decimal
    valor_cota: Decimal
    valor_carteira: Decimal = None
    fundo_tipo: str = None
    cotistas: int = None

    @classmethod
    def from_dict(cls, row):
        cnpj_fundo = row["cnpj_fundo"] if "cnpj_fundo" in row else row["cnpj_fundo_classe"]
        tp_fundo = row.get("tp_fundo") if "tp_fundo" in row else row.get("tp_fundo_classe")  # Não existe para 201901
        return cls(
            data_competencia=parse_iso_date(row["dt_comptc"]),
            cotistas=int(row["nr_cotst"]) if row["nr_cotst"] else None,  # Não existe em alguns registros de 2004
            fundo_tipo=tp_fundo,
            fundo_cnpj=REGEXP_CNPJ_SEPARATORS.sub("", cnpj_fundo).strip(),
            valor_captado=Decimal(row["captc_dia"]) if row["captc_dia"] else None,
            valor_resgatado=Decimal(row["resg_dia"]) if row["resg_dia"] else None,
            patrimonio_liquido=Decimal(row["vl_patrim_liq"]) if row["vl_patrim_liq"] else None,
            valor_cota=Decimal(row["vl_quota"]) if row["vl_quota"] else None,
            valor_carteira=Decimal(row["vl_total"]) if row["vl_total"] else None,
        )


@dataclass
class Noticia:
    titulo: str
    link: str
    data: datetime.date
    descricao: str


class CVM:
    def __init__(self):
        # TODO: trocar user agent
        self.session = create_session()

    def noticias(self):
        url = "https://www.gov.br/cvm/pt-br/assuntos/noticias"
        params = {"b_size": 60, "b_start:int": 0}
        finished = False
        while not finished:
            response = self.session.get(url, params=params)
            tree = document_fromstring(response.text)
            items = tree.xpath("//ul[contains(@class, 'noticias')]/li")
            for li in items:
                row = {
                    "titulo": li.xpath(".//h2/a/text()")[0].strip(),
                    "link": li.xpath(".//h2/a/@href")[0].strip(),
                    "data": li.xpath(".//span[@class = 'data']/text()")[0].strip(),
                    "descricao": " ".join(
                        item.strip() for item in li.xpath(".//span[@class = 'descricao']/text()") if item.strip()
                    ),
                }
                row["data"] = parse_date("br-date", row["data"])
                yield Noticia(**row)
            params["b_start:int"] += 60
            finished = len(items) != params["b_size"]

    def url_informe_diario_fundo(self, data: datetime.date):
        if (data.year, data.month) >= (2021, 1):
            return (
                f"https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{data.year}{data.month:02d}.zip"
            )
        else:
            return f"https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/HIST/inf_diario_fi_{data.year}.zip"

    def _le_zip_informe_diario(self, zip_filename):
        zf = zipfile.ZipFile(zip_filename)
        # TODO: verificar se lista de arquivos contém nomes corretos?
        for file_info in zf.filelist:
            with io.TextIOWrapper(zf.open(file_info.filename, mode="r"), encoding="iso-8859-1") as fobj:
                for row in csv.DictReader(fobj, delimiter=";"):
                    yield InformeDiarioFundo.from_dict({key.lower(): value for key, value in row.items()})

    def informe_diario_fundo(self, data: datetime.date):
        url = self.url_informe_diario_fundo(data)
        response = self.session.get(url)
        zip_fobj = io.BytesIO(response.content)
        yield from self._le_zip_informe_diario(zip_fobj)

    def __cadastro_fundos(self):
        # TODO: criar dataclass e finalizar implementação
        url = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
        with tempfile.NamedTemporaryFile(suffix=".csv") as temp:
            download_filename = Path(temp.name)
            download_files([url], [download_filename])
            with download_filename.open(encoding="iso-8859-1") as fobj:
                reader = csv.DictReader(fobj, delimiter=";")
                for row in reader:
                    yield {
                        # "dt_cancel"::date AS "dt_cancel",
                        # "dt_const"::date AS "dt_const",
                        # "dt_fim_exerc"::date AS "dt_fim_exerc",
                        # "dt_ini_ativ"::date AS "dt_ini_ativ",
                        # "dt_ini_classe"::date AS "dt_ini_classe",
                        # "dt_ini_exerc"::date AS "dt_ini_exerc",
                        # "dt_ini_sit"::date AS "dt_ini_sit",
                        # "dt_patrim_liq"::date AS "dt_patrim_liq",
                        # "dt_reg"::date AS "dt_reg",
                        # "admin"::varchar(84) AS "admin",
                        # "auditor"::varchar(73) AS "auditor",
                        # "cd_cvm"::int AS "cd_cvm",
                        # "classe"::varchar(23) AS "classe",
                        # "cnpj_admin"::varchar(18) AS "cnpj_admin",
                        # "cnpj_auditor"::varchar(18) AS "cnpj_auditor",
                        # "cnpj_controlador"::varchar(18) AS "cnpj_controlador",
                        # "cnpj_custodiante"::varchar(18) AS "cnpj_custodiante",
                        # "cnpj_fundo"::varchar(18) AS "cnpj_fundo",
                        # "condom"::varchar(7) AS "condom",
                        # "controlador"::varchar(80) AS "controlador",
                        # "cpf_cnpj_gestor"::varchar(18) AS "cpf_cnpj_gestor",
                        # "custodiante"::varchar(80) AS "custodiante",
                        # "denom_social"::varchar(100) AS "denom_social",
                        # "diretor"::varchar(44) AS "diretor",
                        # "entid_invest"::varchar(1) AS "entid_invest",
                        # "fundo_cotas"::varchar(1) AS "fundo_cotas",
                        # "fundo_exclusivo"::varchar(1) AS "fundo_exclusivo",
                        # "gestor"::varchar(97) AS "gestor",
                        # "inf_taxa_adm"::text AS "inf_taxa_adm",
                        # "inf_taxa_perfm"::text AS "inf_taxa_perfm",
                        # "pf_pj_gestor"::varchar(2) AS "pf_pj_gestor",
                        # "publico_alvo"::varchar(13) AS "publico_alvo",
                        # "rentab_fundo"::varchar(55) AS "rentab_fundo",
                        # "sit"::varchar(23) AS "sit",
                        # "taxa_adm"::varchar(7) AS "taxa_adm",
                        # "taxa_perfm"::varchar(5) AS "taxa_perfm",
                        # "tp_fundo"::varchar(11) AS "tp_fundo",
                        # "trib_lprazo"::varchar(3) AS "trib_lprazo",
                        # "vl_patrim_liq"::varchar(15) AS "vl_patrim_liq"
                    }


def extrai_datahora(valor, timezone=BRT):
    resultado = REGEXP_DATAHORA.findall(valor)
    if not resultado:
        return None
    data, hora = resultado[0]
    if not hora:
        return datetime.datetime.strptime(data, "%d/%m/%Y").replace(tzinfo=timezone)
    else:
        return datetime.datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M").replace(tzinfo=timezone)


def extrai_parametros(valor):
    result = REGEXP_PARAMETROS.match(valor.replace("\xa0", " "))
    if not result:
        raise ValueError(f"`valor` não está no formato de chamada de função JS: {repr(valor)}")
    function_name = result.group(1)
    params_str = result.group(2)
    params = REGEXP_PARAMETROS_INTERNA.findall(params_str)
    return function_name, [param[0] if param[0] else param[1] for param in params]


@dataclass
class DocumentoEmpresa:
    codigo_empresa: str
    empresa: str
    categoria: str
    datahora_entrega: datetime.datetime
    situacao: str
    modalidade: str
    url_download: str
    id: int = None
    protocolo: str = None
    url_visualizacao: str = None
    versao: int = None
    subcategoria: str = None
    assunto: str = None
    datahora_referencia: datetime.datetime = None
    especie: str = None
    tipo: str = None
    detalhe_publicacao: str = None

    def serialize(self):
        return {"uuid": self.uuid, **asdict(self)}

    @property
    def uuid(self):
        "Usa URLid do Brasil.IO para criar um ID único offline, mesmo que o documento não tenha ID próprio"
        unique_data = [
            self.id,
            self.codigo_empresa,
            self.modalidade,
            self.categoria,
            self.tipo,
            self.especie,
            self.datahora_entrega.isoformat() if self.datahora_entrega else None,
        ]
        values = [slug(value) if value is not None else "" for value in unique_data]
        internal_id = "-".join(values)
        return uuid.uuid5(uuid.NAMESPACE_URL, f"https://id.brasil.io/cvm-rad-doc/v1/{internal_id}/")

    @classmethod
    def from_data(cls, data):
        header = [
            "codigo_empresa",
            "empresa",
            "categoria",
            "subcategoria",
            "assunto",
            "datahora_referencia",
            "datahora_entrega",
            "situacao",
            "versao",
            "modalidade",
            "campo_11",
            "campo_12",
        ]
        values = [value.strip() for value in data.split("$&")]
        row = dict(zip(header, values))
        row["versao"] = int(row["versao"]) if row["versao"] not in ("", "-") else None
        row["datahora_referencia"] = extrai_datahora(row["datahora_referencia"])
        row["datahora_entrega"] = extrai_datahora(row["datahora_entrega"])
        row["especie"] = None
        if row["assunto"]:
            row["assunto"], row["especie"] = [item.strip() for item in REGEXP_ASSUNTO.findall(row["assunto"])[0]]
            row["assunto"] = row["assunto"] if row["assunto"] not in ("", "-") else None
            row["especie"] = row["especie"] if row["especie"] not in ("", "-") else None
        html = row["campo_11"]
        tree = document_fromstring(html)
        search_on_click = tree.xpath("//i[@class='fi-page-search']/@onclick")
        row["url_visualizacao"] = ""
        if search_on_click:
            search_function, search_params = extrai_parametros(search_on_click[0])
            if search_params:
                assert search_function in (
                    "OpenPopUpVer",
                    "VisualizaArquivo_ITR_DFP_IAN",
                ), f"Dados para link de visualização não reconhecidos: {search_function}, {search_params}"
                if search_function == "OpenPopUpVer":
                    # params: ['frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega=66913']
                    row["url_visualizacao"] = urljoin("https://www.rad.cvm.gov.br/ENET/", search_params[0])
                elif search_function == "VisualizaArquivo_ITR_DFP_IAN":
                    # params: ['2', '09/03/1998', 'CONSULTA', 'FUTURETEL S.A. - EM LIQUIDAÇÃO', 'FUTURETEL', '17388',
                    #          'L']
                    sDescTPDoc, sDataEncerra, sFuncao, sRazao, sPregao, sCodCVM, sMoeda = search_params
                    # XXX: 'http://siteempresas.bovespa.com.br' vem de `$('#siteDXW').val()`, que pode mudar
                    # TODO: `sRazao` e `sPregao` usam a função JS `escape()` e aqui não estamos escapando
                    row["url_visualizacao"] = (
                        "http://siteempresas.bovespa.com.br/"
                        f"/dxw/FrDXW.asp?moeda={sMoeda}&tipo={sDescTPDoc}&data={sDataEncerra}&"
                        f"razao={sRazao}&site=C&pregao={sPregao}&ccvm={sCodCVM}"
                    )
        download_documento = tree.xpath("//i[@class='fi-download']/@onclick")[0]
        download_function, download_params = extrai_parametros(download_documento)
        assert download_function in (
            "OpenDownloadDocumentos",
            "VisualizaArquivo_ITR_DFP_IAN",
        ), f"Função de download desconhecida: {download_function}"
        if download_function == "OpenDownloadDocumentos":
            row["id"], _, row["protocolo"], row["tipo"] = download_params
            row["id"] = int(row["id"])
            row["url_download"] = (
                "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&"
                f"numSequencia={row['id']}&numVersao={row['versao']}&numProtocolo={row['protocolo']}&"
                f"descTipo={row['tipo']}&CodigoInstituicao=1"
            )
        elif download_function == "VisualizaArquivo_ITR_DFP_IAN":
            sDescTPDoc, sDataEncerra, sFuncao, sRazao, sPregao, sCodCVM, sMoeda = download_params
            row["id"] = None  # TODO: deveríamos preencher?
            row["protocolo"] = None  # TODO: deveríamos preencher?
            row["tipo"] = None  # TODO: deveríamos preencher? (sDescTPDoc is a number, not a string as expected)
            # XXX: 'http://siteempresas.bovespa.com.br' vem de `$('#siteDXW').val()`, que pode mudar
            # TODO: `sRazao` usa a função JS `escape()` e aqui não estamos escapando
            row["url_download"] = (
                "http://siteempresas.bovespa.com.br/"
                f"/dxw/download.asp?moeda={sMoeda}&tipo={sDescTPDoc}&data={sDataEncerra}&"
                f"razao={sRazao}&site=C&ccvm={sCodCVM}"
            )
        info_publicacao = REGEXP_INFO_FUNCTION.findall(html)
        if info_publicacao:
            info_function, info_params = extrai_parametros(info_publicacao[0])
            assert info_function == "mostraLocaisPublicacao", f"Função de info desconhecida: {info_function}"
            row["detalhe_publicacao"] = "\n".join("|".join(line.split("@!@")) for line in info_params[1].split("#$#"))
        else:
            row["detalhe_publicacao"] = ""
        del row["campo_11"]
        del row["campo_12"]
        row = {key: value if value not in ("", "-", None) else None for key, value in row.items()}
        return cls(**row)


class RAD:
    # TODO: métodos deveriam ser movidos para classe CVM?
    def __init__(self):
        self.session = create_session()
        self._empresas = self._categorias = None

    def _extract_rows(self, raw_data):
        records = raw_data.split("$&&*")
        for record in records:
            if not record.strip():
                continue
            yield DocumentoEmpresa.from_data(record)

    def empresas(self):
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        response = self.session.get(url)
        tree = document_fromstring(response.content.decode("utf-8"))
        fake_json_data = tree.xpath("//input[@name = 'hdnEmpresas']/@value")[0]
        result = {}
        for code, name in REGEXP_EMPRESAS.findall(fake_json_data):
            other_code, real_name = name.split(" - ", maxsplit=1)
            assert code == f"C_{other_code}", f"Codes differs: {code}, {name}"
            result[other_code] = real_name
        return result

    def categorias(self):
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        response = self.session.get(url)
        tree = document_fromstring(response.content.decode("utf-8"))
        options = {}
        for option in tree.xpath("//select[@id = 'cboCategorias']//option"):
            value = option.xpath(".//@value")[0]
            label = " ".join(item.strip() for item in option.xpath(".//text()") if item.strip())
            options[REGEXP_SPACES.sub(" ", label)] = value
        return options

    # TODO: pegar código da empresa a partir de outros dados (CNPJ, razão social)

    def busca(
        self,
        data_inicio: datetime.date,
        data_fim: datetime.date,
        categorias: list = None,
        empresas: list = None,
        hora_inicio="00:00",
        hora_fim="23:59",
    ):
        """Busca documentos disponíveis no RAD/CVM (desde março/1998)"""
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx/ListarDocumentos"
        if empresas is not None:
            if self._empresas is None:
                self._empresas = self.empresas()
            codigos_empresas = "," + ",".join(codigo for codigo, nome in self._empresas.items() if nome in empresas)
        else:
            codigos_empresas = ""

        if categorias is None:
            categorias = ["TODAS"]
        if self._categorias is None:
            self._categorias = self.categorias()
        codigos_categorias = []
        for categoria in categorias:
            codigo = self._categorias[categoria]
            if codigo.startswith("9000"):
                codigo = int(codigo[4:])
                categoria = f"EST_{codigo}"
            else:
                codigo = int(codigo)
                categoria = f"IPE_{codigo}_-1_-1"
            codigos_categorias.append(categoria)
        categorias = ",".join(codigos_categorias)

        form_data = {
            "dataDe": data_inicio.strftime("%d/%m/%Y") if data_inicio else "",
            "dataAte": data_fim.strftime("%d/%m/%Y") if data_fim else "",
            "empresa": codigos_empresas,
            "setorAtividade": "-1",
            "categoriaEmissor": "-1",
            "situacaoEmissor": "-1",
            "tipoParticipante": "-1",
            "dataReferencia": "",
            "categoria": categorias,
            "periodo": "2",
            "horaIni": hora_inicio,
            "horaFim": hora_fim,
            "palavraChave": "",
            "ultimaDtRef": "false",
            "tipoEmpresa": "0",
            "token": "",
            "versaoCaptcha": "",
        }
        # TODO: fazer paginação?
        response = self.session.post(url, json=form_data)
        data = response.json()
        erro = data["d"]["msgErro"]
        if erro:
            raise RuntimeError(f"Erro ao efetuar busca: {erro}")
        raw_data = data["d"]["dados"]
        return list(self._extract_rows(raw_data))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Captura e trata dados da CVM")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_noticias = subparsers.add_parser("noticias", help="Baixa notícias do site da CVM a partir de hoje")
    parser_noticias.add_argument("data_minima", type=parse_iso_date, help="Data mínima para baixar")
    parser_noticias.add_argument("csv_filename", type=Path, help="Nome do CSV para salvar os dados")

    parser_informe_diario_fundo = subparsers.add_parser(
        "informe-diario-fundo", help="Baixa informes diários dos fundos para uma determinada data"
    )
    parser_informe_diario_fundo.add_argument("data", type=parse_iso_date, help="Data de referência do informe")
    parser_informe_diario_fundo.add_argument("csv_filename", type=Path, help="Nome do CSV para salvar os dados")

    parser_rad_empresas = subparsers.add_parser("rad-empresas", help="Baixa lista de empresas disponíveis no RAD")
    parser_rad_empresas.add_argument("csv_filename", type=Path, help="Nome do CSV para salvar os dados")

    parser_rad_busca = subparsers.add_parser("rad-busca", help="Busca por documentos publicados por empresas")
    parser_rad_busca.add_argument(
        "--empresa",
        "-e",
        type=str,
        action="append",
        help="Nome de empresa para filtrar. Precisa ser o mesmo nome retornado por rad-empresas",
    )
    parser_rad_busca.add_argument(
        "--data-inicial", "-i", type=parse_iso_date, help="Data mínima de publicação do documento"
    )
    parser_rad_busca.add_argument(
        "--data-final", "-f", type=parse_iso_date, help="Data máxima de publicação do documento"
    )
    parser_rad_busca.add_argument("csv_filename", type=Path, help="Nome do CSV para salvar os dados")

    args = parser.parse_args()

    if args.command == "noticias":
        csv_filename = args.csv_filename
        csv_filename.parent.mkdir(parents=True, exist_ok=True)
        data_minima = args.data_minima

        cvm = CVM()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for noticia in cvm.noticias():
                if noticia.data < data_minima:
                    break
                row = asdict(noticia)
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif args.command == "rad-empresas":
        csv_filename = args.csv_filename
        csv_filename.parent.mkdir(parents=True, exist_ok=True)

        rad = RAD()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for key, value in rad.empresas().items():
                row = {"codigo": key, "nome": value}
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif args.command == "rad-busca":
        csv_filename = args.csv_filename
        csv_filename.parent.mkdir(parents=True, exist_ok=True)
        empresas = args.empresa
        inicio = args.data_inicial
        fim = args.data_final

        rad = RAD()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for documento in rad.busca(data_inicio=inicio, data_fim=fim, empresas=empresas):
                row = documento.serialize()
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    elif args.command == "informe-diario-fundo":
        data = args.data
        csv_filename = args.csv_filename
        csv_filename.parent.mkdir(parents=True, exist_ok=True)

        cvm = CVM()
        with csv_filename.open(mode="w") as csv_fobj:
            writer = None
            for informe in cvm.informe_diario_fundo(data):
                row = asdict(informe)
                if writer is None:
                    writer = csv.DictWriter(csv_fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
