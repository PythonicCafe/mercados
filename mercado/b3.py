import base64
import json
from urllib.parse import urljoin

import requests


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
                yield from response["results"]
                finished = url_params["pageNumber"] >= response["page"]["totalPages"]
                url_params["pageNumber"] += 1

    def securitizadoras(self):
        yield from self.paginate(urljoin(self.funds_call_url, "GetListedSecuritization/"))

    def cris(self, cnpj_securitizadora):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedCertified/"),
            url_params={"dateInitial": "", "cnpj": cnpj_securitizadora, "type": "CRI"},
        )

    def documents(self, identificador_cri, start_date, end_date):
        yield from self.paginate(
            base_url=urljoin(self.funds_call_url, "GetListedDocumentsTypeHistory/"),
            url_params={
                "cnpj": identificador_cri,
                "dateInitial": start_date.strftime("%Y-%m-%d"),
                "dateFinal": end_date.strftime("%Y-%m-%d"),
            },
        )


if __name__ == "__main__":
    import datetime

    from rows.utils import CsvLazyDictWriter
    from tqdm import tqdm

    from utils import parse_date


    writer = CsvLazyDictWriter("cri-documents.csv.gz")
    current_year = datetime.datetime.now().year
    b3 = B3()
    securitizadoras = b3.securitizadoras()
    progress = tqdm()
    for securitizadora in securitizadoras:
        progress.desc = securitizadora["companyName"]
        cris = b3.cris(securitizadora["cnpj"])
        for cri in cris:
            start_date = parse_date("iso-datetime-tz", cri["issueDate"])
            for year in range(start_date.year, current_year + 1):
                start, stop = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
                documents = list(b3.documents(cri["identificationCode"], start_date=start, end_date=stop))
                for doc in documents:
                    writer.writerow(doc)
                progress.update(len(documents))
    progress.close()
    writer.close()
