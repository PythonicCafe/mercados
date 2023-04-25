from pprint import pprint

from mercadobr.fundosnet import FundosNet


fnet = FundosNet()
DOCUMENTO_TIPO = []
for values in fnet.types.values():
    for item in values:
        DOCUMENTO_TIPO.append((item["id"], item["descricao"]))

DOCUMENTO_TIPO.sort(key=lambda item: item[1])
DOCUMENTO_TIPO.append((0, "Todos"))
DOCUMENTO_TIPO = tuple(DOCUMENTO_TIPO)
print("DOCUMENTO_TIPO = ", end="")
pprint(DOCUMENTO_TIPO)
