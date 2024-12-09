"""Raspador para pegar a cota de fundos na CVM -- prefira usar `InformeDiario` de `mercados.cvm`"""

import datetime
import io
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

import rows
from lxml.html import document_fromstring, tostring

from .utils import create_session


def clean_cnpj(value):
    # TODO: move to mercados.utils
    if value is None:
        return None
    for char in ".-/ ":
        value = value.replace(char, "")
    value = value.strip()
    assert len(value) == 14
    return value


def format_cnpj(cnpj):
    """
    >>> format_cnpj('123456789000191')
    '12.345.678/0001-91'
    """
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"


@dataclass
class CotaFundo:
    fundo: str
    fundo_cnpj: str
    administrador: str
    administrador_cnpj: str
    data: datetime.date
    cota: Decimal
    captacao: Decimal
    resgate: Decimal
    patrimonio_liquido: Decimal
    total_carteira: Decimal
    cotistas: int
    data_proxima_informacao: datetime.date


class BRDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


class BRMoneyField(rows.fields.DecimalField):
    @classmethod
    def deserialize(cls, value):
        value = value.replace(".", "").replace(",", ".").strip()
        return super().deserialize(value)


class CVMFundo:
    base_url = "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/ResultBuscaPartic.aspx"

    def __init__(self):
        self.session = create_session()

    def _parse_dados_fundo(self, tree):
        dados_fundo = [
            item.strip()
            for item in tree.xpath("//tr[contains(.//td//text(), 'Nome do Fundo')]//text()")
            if item.strip()
        ]
        assert dados_fundo[0] == "Nome do Fundo:"
        assert dados_fundo[2] == "CNPJ:"
        dados_adm = [
            item.strip()
            for item in tree.xpath("//tr[contains(.//td//text(), 'Administrador')]//text()")
            if item.strip()
        ]
        assert dados_adm[0] == "Administrador:"
        assert dados_adm[2] == "CNPJ:"
        return {
            "fundo": dados_fundo[1],
            "fundo_cnpj": dados_fundo[3],
            "administrador": dados_adm[1],
            "administrador_cnpj": dados_adm[3],
        }

    def dados(self, cnpj, competencia):
        params = {
            "TpConsulta": "1",
            "CNPJNome": cnpj,
            "COMPTC": competencia.strftime("%m/%Y") if competencia is not None else "",
        }
        response = self.session.get(self.base_url, params=params, allow_redirects=True)
        tree = document_fromstring(response.text)
        meta = self._parse_dados_fundo(tree)
        assert clean_cnpj(meta["fundo_cnpj"]) == clean_cnpj(cnpj)

        table_html = tostring(tree.xpath("//table[@id = 'dgDocDiario']")[0])
        table = rows.import_from_html(
            io.BytesIO(table_html),
            force_types={
                "dia": rows.fields.IntegerField,
                "quota_r": BRMoneyField,
                "captacao_no_dia_r": BRMoneyField,
                "resgate_no_dia_r": BRMoneyField,
                "patrimonio_liquido_r": BRMoneyField,
                "total_da_carteira_r": BRMoneyField,
                "n_total_de_cotistas": rows.fields.IntegerField,
                "data_da_proxima_informacao_do_pl": BRDateField,
            },
        )
        for row in table:
            if not row.quota_r:
                continue
            yield CotaFundo(
                fundo=meta["fundo"],
                fundo_cnpj=meta["fundo_cnpj"],
                administrador=meta["administrador"],
                administrador_cnpj=meta["administrador_cnpj"],
                data=datetime.date(competencia.year, competencia.month, row.dia),
                cota=row.quota_r,
                captacao=row.captacao_no_dia_r,
                resgate=row.resgate_no_dia_r,
                patrimonio_liquido=row.patrimonio_liquido_r,
                total_carteira=row.total_da_carteira_r,
                cotistas=row.n_total_de_cotistas,
                data_proxima_informacao=row.data_da_proxima_informacao_do_pl,
            )

    def competencias(self, cnpj):
        """Consulta datas de competência disponíveis para um fundo"""
        params = {
            "TpConsulta": "1",
            "CNPJNome": cnpj,
            "COMPTC": "",
        }
        response = self.session.get(self.base_url, params=params, allow_redirects=True)
        tree = document_fromstring(response.text)
        datas_competencias = []
        for competencia in tree.xpath("//select[@name = 'ddComptc']/option/@value"):
            competencia = competencia.strip()
            if not competencia:
                continue
            mes, ano = competencia.split("/")
            datas_competencias.append(datetime.date(int(ano), int(mes), 1))
        return sorted(datas_competencias)


if __name__ == "__main__":
    import argparse

    from rows.utils import CsvLazyDictWriter
    from tqdm import tqdm

    parser = argparse.ArgumentParser()
    parser.add_argument("cnpj")
    parser.add_argument("csv_filename")
    args = parser.parse_args()
    cnpj = format_cnpj(clean_cnpj(args.cnpj))
    filename = Path(args.csv_filename).absolute()
    if not filename.parent.exists():
        filename.parent.mkdir(parents=True)

    cvm = CVMFundo()
    datas = cvm.competencias(cnpj)

    writer = CsvLazyDictWriter(filename)
    for data in tqdm(datas):
        for row in cvm.dados(cnpj, data):
            writer.writerow(asdict(row))
    writer.close()
