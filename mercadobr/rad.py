import datetime
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

import requests
from lxml.html import document_fromstring


@dataclass
class DocumentoRad:
    codigo_cvm: str
    empresa: str
    categoria: str
    tipo: str
    data_referencia: datetime.date
    datahora_entrega: datetime.datetime
    status: str
    modalidade: str
    sequencia: int
    protocolo: int
    desc_tipo: str
    versao: int = None
    especie: str = None

    @property
    def download_url(self):
        return f"https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&numSequencia={self.sequencia}&numVersao={self.versao}&numProtocolo={self.protocolo}&descTipo={self.desc_tipo}&CodigoInstituicao=1"


def parse_datetime(value):
    return datetime.datetime.strptime(value.split("</spanOrder>")[1].strip() + ":00-0300", "%d/%m/%Y %H:%M:%S%z")


def parse_reference_date(value):
    return datetime.datetime.strptime("01/" + value.split("</spanOrder>")[1].strip(), "%d/%m/%Y").date()


class Rad:
    base_url = "https://www.rad.cvm.gov.br/ENET/"

    def __init__(self):
        self._session = requests.Session()

    def categorias(self):
        url = urljoin(self.base_url, "frmConsultaExternaCVM.aspx")
        response = self._session.get(url, verify=False)
        tree = document_fromstring(response.text)
        options = {}
        for option in tree.xpath("//select[@id = 'cboCategorias']//option"):
            value = option.xpath(".//@value")[0]
            label = " ".join(item.strip() for item in option.xpath(".//text()") if item.strip())
            options[label] = value
        return options

    # TODO: pegar código da empresa a partir de outros dados (CNPJ, razão
    # social)

    def busca(
        self, data_inicio: datetime.date, data_fim: datetime.date, categorias: list = None, empresas: list = None
    ):
        if not categorias:
            categorias = ["TODAS"]
        else:
            todas_categorias = self.categorias()
            new = []
            for categoria in categorias:
                codigo = todas_categorias[categoria]
                if codigo.startswith("9000"):
                    codigo = int(codigo[4:])
                    categoria = f"EST_{codigo}"
                else:
                    codigo = int(codigo)
                    categoria = f"IPE_{codigo}_-1_-1"
                new.append(categoria)
            categorias = new
        categorias = ",".join(categorias)

        if not empresas:
            empresas = []
        empresas = "," + ",".join([f"{int(x):06d}" for x in empresas])

        url = urljoin(self.base_url, "frmConsultaExternaCVM.aspx/ListarDocumentos")
        data = {
            "dataDe": data_inicio.strftime("%d/%m/%Y"),
            "dataAte": data_fim.strftime("%d/%m/%Y"),
            "empresa": empresas,
            "setorAtividade": "-1",
            "categoriaEmissor": "-1",
            "situacaoEmissor": "-1",
            "tipoParticipante": "-1",
            "dataReferencia": "",
            "categoria": categorias,
            "periodo": "2",
            "horaIni": "",
            "horaFim": "",
            "palavraChave": "",
            "ultimaDtRef": "false",
            "tipoEmpresa": "0",
            "token": "",
            "versaoCaptcha": "",
        }
        # TODO: fazer paginação?
        response = self._session.post(url, json=data, verify=False)
        data = response.json()
        for line in data["d"]["dados"].split("$&&*"):
            fields = line.split("$&")
            if len(fields) != 12:
                continue
            (
                codigo_cvm,
                empresa,
                categoria,
                tipo,
                especie,
                data_referencia,
                datahora_entrega,
                status,
                versao,
                modalidade,
                acoes,
                _,
            ) = fields
            sequencia, _, protocolo, desc_tipo = (
                acoes.split("OpenDownloadDocumentos(")[1].split(")")[0].replace("'", "").split(",")
            )
            especie = especie.split("</spanOrder>")[1].strip()
            if especie == "-":
                especie = None
            yield DocumentoRad(
                codigo_cvm=codigo_cvm,
                empresa=empresa,
                categoria=categoria,
                tipo=tipo,
                especie=especie,
                data_referencia=parse_reference_date(data_referencia),
                datahora_entrega=parse_datetime(datahora_entrega),
                status=status,
                versao=int(versao) if versao and versao != "-" else None,
                modalidade=modalidade,
                sequencia=int(sequencia),
                protocolo=int(protocolo),
                desc_tipo=desc_tipo,
            )


if __name__ == "__main__":
    from pathlib import Path

    from rows.utils import CsvLazyDictWriter
    from rows.utils.download import Download, Downloader
    from tqdm import tqdm

    rad = Rad()
    codigo = "008397"  # mangels
    categoria = "Valores Mobiliários Negociados e Detidos"
    data_inicio = datetime.date(1994, 1, 1)
    data_fim = datetime.datetime.today().date()
    csv_filename = "mangels2.csv"
    download_path = Path(__file__).parent / "data" / "download"
    if not download_path.exists():
        download_path.mkdir(parents=True)
    quiet = False

    downloader = Downloader.subclasses()["aria2c"](
        path=download_path,
        quiet=quiet,
        check_certificate=False,
    )
    writer = CsvLazyDictWriter(csv_filename)
    results = rad.busca(data_inicio, data_fim, categorias=[categoria], empresas=[codigo])
    for item in tqdm(results):
        filename = f"{item.codigo_cvm.replace('-', '')}_{item.sequencia}_{item.protocolo}.pdf"
        writer.writerow({**asdict(item), "download_url": item.download_url})
        downloader.add(Download(url=item.download_url, filename=filename))
    writer.close()
    downloader.run()
