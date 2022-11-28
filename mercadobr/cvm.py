import csv
import tempfile
from pathlib import Path

import requests
from lxml.html import document_fromstring

from .utils import download_files


class CVM:
    def __init__(self):
        # TODO: trocar user agent
        self._session = requests.Session()

    @property
    def noticias(self):
        url = "https://www.gov.br/cvm/pt-br/assuntos/noticias"
        params = {"b_size": 60, "b_start:int": 0}
        finished = False
        while not finished:
            response = self._session.get(url, params=params)
            tree = document_fromstring(response.text)
            items = tree.xpath("//ul[contains(@class, 'noticias')]/li")
            for li in items:
                # TODO: criar dataclass (e converter data)
                yield {
                    "titulo": li.xpath(".//h2/a/text()")[0].strip(),
                    "link": li.xpath(".//h2/a/@href")[0].strip(),
                    "data": li.xpath(".//span[@class = 'data']/text()")[0].strip(),
                    "descricao": " ".join(item.strip() for item in li.xpath(".//span[@class = 'descricao']/text()") if item.strip()),
                }
            params["b_start:int"] += 60
            finished = len(items) != params["b_size"]

    def cadastro_fundos(self):
        # TODO: criar dataclass
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
