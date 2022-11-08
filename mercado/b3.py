import base64
import csv
import io
import json
from urllib.parse import urljoin

import requests
from rows.utils.date import date_range


class B3:
    funds_call_url = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/"

    def __init__(self):
        self._session = requests.Session()

    def _make_url_params(self, params):
        return base64.b64encode(json.dumps(params).encode("utf-8")).decode("ascii")

    def request(self, url, url_params=None, params=None, method="GET"):
        if url_params is not None:
            url_params = self._make_url_params(url_params)
            url = urljoin(url, url_params)
        response = self._session.request(method, url, params=params)
        return response.json()

    def paginate(self, base_url, url_params=None, params=None, method="GET"):
        url_params = url_params or {}
        if "pageNumber" not in url_params:
            url_params["pageNumber"] = 1
        if "pageSize" not in url_params:
            url_params["pageSize"] = 500
        finished = False
        while not finished:
            response = self.request(base_url, url_params, params=params, method=method)
            if isinstance(response, list):
                yield from response
                finished = True
            elif isinstance(response, dict):
                if "results" in response:
                    yield from response["results"]
                    finished = url_params["pageNumber"] >= response["page"]["totalPages"]
                    url_params["pageNumber"] += 1
                else:
                    yield response

    def fiinfras(self):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedFundsSIG/"),
            url_params={"typeFund": 27},
        )

    def fiinfra_detail(self, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetDetailFundSIG/"),
            url_params={"typeFund": 27, "identifierFund": identificador},
        )

    def fiinfra_dividends(self, cnpj, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedSupplementFunds/"),
            url_params={"cnpj": cnpj, "identifierFund": identificador, "typeFund": 27},
        )

    def fiinfra_documents(self, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedPreviousDocuments/"),
            url_params={"identifierFund": identificador, "type": 1},
        )

    def fips(self):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedFundsSIG/"),
            url_params={"typeFund": 21},
        )

    def fip_detail(self, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetDetailFundSIG/"),
            url_params={"typeFund": 21, "identifierFund": identificador},
        )

    def fip_dividends(self, cnpj, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedSupplementFunds/"),
            url_params={"cnpj": cnpj, "identifierFund": identificador, "typeFund": 21},
        )

    def fip_documents(self, identificador):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedPreviousDocuments/"),
            url_params={"identifierFund": identificador, "type": 1},
        )

    def securitizadoras(self):
        yield from self.paginate(urljoin(self.funds_call_url, "GetListedSecuritization/"))

    def cris(self, cnpj_securitizadora):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedCertified/"),
            url_params={"dateInitial": "", "cnpj": cnpj_securitizadora, "type": "CRI"},
        )

    def cras(self, cnpj_securitizadora):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedCertified/"),
            url_params={"dateInitial": "", "cnpj": cnpj_securitizadora, "type": "CRA"},
        )

    def certificate_documents(self, identificador, start_date, end_date):  # CRI or CRA
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedDocumentsTypeHistory/"),
            url_params={
                "cnpj": identificador,
                "dateInitial": start_date.strftime("%Y-%m-%d"),
                "dateFinal": end_date.strftime("%Y-%m-%d"),
            },
        )

    def debentures(self):
        response = self._session.get(
            "https://sistemaswebb3-balcao.b3.com.br/featuresDebenturesProxy/DebenturesCall/GetDownload",
            verify=False,
        )
        decoded_data = base64.b64decode(response.text).decode("ISO-8859-1")
        reader = csv.DictReader(io.StringIO(decoded_data), delimiter=";")
        yield from reader

    def negociacao_balcao(self, date):
        response = self._session.get(
            "https://bvmf.bmfbovespa.com.br/NegociosRealizados/Registro/DownloadArquivoDiretorio",
            params={"data": date.strftime("%d-%m-%Y")},
        )
        decoded_data = base64.b64decode(response.text).decode("ISO-8859-1")
        csv_data = decoded_data[decoded_data.find("\n") + 1:]
        reader = csv.DictReader(io.StringIO(csv_data), delimiter=";")
        for row in reader:
            for field in ('Cod. Isin', 'Data Liquidacao'):
                if field not in row:
                    row[field] = None
            yield row


if __name__ == "__main__":
    import argparse
    import datetime

    from rows.utils import CsvLazyDictWriter
    from tqdm import tqdm

    from utils import parse_date


    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "cra-documents",
            "cri-documents",
            "debentures",
            "fiinfra-dividends",
            "fiinfra-documents",
            "fiinfra-subscriptions",
            "fip-dividends",
            "fip-documents",
            "fip-subscriptions",
            "negociacao-balcao",
        ],
    )
    args = parser.parse_args()

    if args.command == "cri-documents":
        writer = CsvLazyDictWriter("cri-documents.csv.gz")
        current_year = datetime.datetime.now().year
        b3 = B3()
        securitizadoras = b3.securitizadoras()
        progress = tqdm()
        for securitizadora in securitizadoras:
            progress.desc = securitizadora["companyName"]
            for cri in b3.cris(securitizadora["cnpj"]):
                start_date = parse_date("iso-datetime-tz", cri["issueDate"])
                base_row = {**securitizadora, **cri}
                for year in range(start_date.year, current_year + 1):
                    start, stop = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
                    documents = list(b3.certificate_documents(cri["identificationCode"], start_date=start, end_date=stop))
                    for doc in documents:
                        writer.writerow({**base_row, **doc})
                    progress.update(len(documents))
        progress.close()
        writer.close()

    if args.command == "cra-documents":
        writer = CsvLazyDictWriter("cra-documents.csv.gz")
        current_year = datetime.datetime.now().year
        b3 = B3()
        securitizadoras = b3.securitizadoras()
        progress = tqdm()
        for securitizadora in securitizadoras:
            progress.desc = securitizadora["companyName"]
            for cra in b3.cras(securitizadora["cnpj"]):
                start_date = parse_date("iso-datetime-tz", cra["issueDate"])
                base_row = {**securitizadora, **cra}
                for year in range(start_date.year, current_year + 1):
                    start, stop = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
                    documents = list(b3.certificate_documents(cra["identificationCode"], start_date=start, end_date=stop))
                    for doc in documents:
                        writer.writerow({**base_row, **doc})
                    progress.update(len(documents))
        progress.close()
        writer.close()

    elif args.command == "fiinfra-dividends":
        b3 = B3()
        writer = CsvLazyDictWriter("fiinfra-dividends.csv.gz")
        for fiinfra in tqdm(b3.fiinfras()):
            detalhes = next(b3.fiinfra_detail(fiinfra["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder")
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            data = next(b3.fiinfra_dividends(cnpj=detail_fund["cnpj"], identificador=fiinfra["acronym"]))
            dividends = data.pop("cashDividends")
            subscriptions = data.pop("subscriptions")
            stockDividends = data.pop("stockDividends")
            for dividend in dividends:
                writer.writerow({**base_fund_data, **data, **dividend})
        writer.close()


    elif args.command == "fiinfra-documents":
        b3 = B3()
        writer = CsvLazyDictWriter("fiinfra-documents.csv.gz")
        for fiinfra in tqdm(b3.fiinfras()):
            detalhes = next(b3.fiinfra_detail(fiinfra["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder")
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            for doc in b3.fiinfra_documents(identificador=fiinfra["acronym"]):
                doc["url"] = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla={fiinfra['acronym']}&strData={doc['date']}"
                writer.writerow({**base_fund_data, **doc})
        writer.close()

    elif args.command == "fiinfra-subscriptions":
        b3 = B3()
        writer = CsvLazyDictWriter("fiinfra-subscriptions.csv.gz")
        for fiinfra in tqdm(b3.fiinfras()):
            detalhes = next(b3.fiinfra_detail(fiinfra["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder")
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            data = next(b3.fiinfra_dividends(cnpj=detail_fund["cnpj"], identificador=fiinfra["acronym"]))
            dividends = data.pop("cashDividends")
            subscriptions = data.pop("subscriptions")
            stockDividends = data.pop("stockDividends")
            for subscription in subscriptions:
                writer.writerow({**base_fund_data, **data, **subscription})
        writer.close()

    elif args.command == "fip-dividends":
        b3 = B3()
        writer = CsvLazyDictWriter("fip-dividends.csv.gz")
        for fip in tqdm(b3.fips()):
            detalhes = next(b3.fip_detail(fip["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder") or {}
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            data = next(b3.fip_dividends(cnpj=detail_fund["cnpj"], identificador=fip["acronym"]))
            dividends = data.pop("cashDividends")
            subscriptions = data.pop("subscriptions")
            stockDividends = data.pop("stockDividends")
            for dividend in dividends:
                writer.writerow({**base_fund_data, **data, **dividend})
        writer.close()

    elif args.command == "fip-documents":
        b3 = B3()
        writer = CsvLazyDictWriter("fip-documents.csv.gz")
        for fip in tqdm(b3.fips()):
            detalhes = next(b3.fip_detail(fip["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder") or {}
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            for doc in b3.fip_documents(identificador=fip["acronym"]):
                doc["url"] = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla={fip['acronym']}&strData={doc['date']}"
                writer.writerow({**base_fund_data, **doc})
        writer.close()

    elif args.command == "fip-subscriptions":
        b3 = B3()
        writer = CsvLazyDictWriter("fip-subscriptions.csv.gz")
        for fip in tqdm(b3.fips()):
            detalhes = next(b3.fip_detail(fip["acronym"]))
            detail_fund = detalhes.pop("detailFund")
            share_holder = detalhes.pop("shareHolder") or {}
            detail_fund["codes"] = ", ".join(detail_fund["codes"])
            base_fund_data = {**detail_fund, **share_holder}
            data = next(b3.fip_dividends(cnpj=detail_fund["cnpj"], identificador=fip["acronym"]))
            dividends = data.pop("cashDividends")
            subscriptions = data.pop("subscriptions")
            stockDividends = data.pop("stockDividends")
            for subscription in subscriptions:
                writer.writerow({**base_fund_data, **data, **subscription})
        writer.close()

    elif args.command == "debentures":
        b3 = B3()
        writer = CsvLazyDictWriter("debentures.csv.gz")
        for row in tqdm(b3.debentures()):
            writer.writerow(row)
        writer.close()

    elif args.command == "negociacao-balcao":
        b3 = B3()
        today = datetime.datetime.now().date()
        start_date = datetime.date(today.year, 1, 1)
        end_date = today + datetime.timedelta(days=1)
        writer = CsvLazyDictWriter(f"negociacao-balcao-{today.year}.csv.gz")
        progress = tqdm()
        for date in date_range(start_date, end_date):
            progress.desc = str(date)
            for row in b3.negociacao_balcao(date):
                writer.writerow(row)
                progress.update()
        progress.close()
        writer.close()
