import datetime

from mercados.b3 import B3
from mercados.document import InformeDiarioFundo
from mercados.fundosnet import FundosNet

fim = datetime.datetime.now().date()
inicio = fim - datetime.timedelta(days=7)
b3 = B3()
fnet = FundosNet()
print("Baixando lista de ETFs da B3")
etfs = list(b3.etfs(detalhe=True))
print(f"Encontrados {len(etfs)} ETFs")
etfs.sort(key=lambda etf: etf.codigo_negociacao)
for etf in etfs:
    etf_cnpj = etf.cnpj
    for doc in fnet.busca(
        cnpj=etf_cnpj,
        situacao="A",
        categoria="Informes Periódicos",
        tipo="Informe Diário",
        inicio=inicio,
        fim=fim,
    ):
        xml = fnet.baixa_xml(doc.url)
        informes = InformeDiarioFundo.from_xml(xml)
        for informe in informes:
            if informe.fundo_cnpj != etf_cnpj:  # O XML pode conter informes de diversos fundos
                continue
            print(f"{etf_cnpj}\t{etf.codigo_negociacao}\t{informe.data_competencia}\t{informe.cota}")
