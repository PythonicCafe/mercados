import base64
import datetime

import requests

from mercados.document import InformeDiarioFundo
from mercados.fundosnet import FundosNet
from mercados.utils import format_dataclass

data_inicial = datetime.date(2025, 7, 1)
data_final = datetime.date(2025, 7, 11)
fnet = FundosNet()
session = requests.Session()

print("Buscando documentos no FundosNET e selecionando informes diários")
documentos = {}
for doc in fnet.search(start_date=data_inicial, end_date=data_final):
    if doc.tipo != "Informe Diário":
        continue
    documentos[doc.id] = doc
    if len(documentos) % 10 == 0:
        print(f"\r{len(documentos):5} encontrados", end="", flush=True)
print(f"\r{len(documentos):5} encontrados", flush=True)

print("Baixando XMLs dos informes selecionados")
xmls = {}
for doc_id, doc in documentos.items():
    response = session.get(doc.url)
    xmls[doc_id] = base64.b64decode(response.content)  # Sim, o contéudo é retornado em base64 :|
    if len(xmls) % 10 == 0:
        print(f"\r{len(xmls):5} baixados", end="", flush=True)
print(f"\r{len(xmls):5} baixados", flush=True)

for doc_id, xml in xmls.items():
    print(f"Extraindo informes do XML de {doc_id}:")
    informes = InformeDiarioFundo.from_xml(xml)
    for rank, informe in enumerate(informes, start=1):
        print(f"#{rank}: {format_dataclass(informe)}")
    print()
