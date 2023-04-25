from pprint import pprint

from mercadobr.fundosnet import FundosNet


def print_choices(name, values):
    print(f"{name} = ", end="")
    pprint(tuple(values))

fnet = FundosNet()
DOCUMENTO_TIPO = []
for values in fnet.types.values():
    for item in values:
        DOCUMENTO_TIPO.append((item["id"], item["descricao"]))

DOCUMENTO_TIPO.sort(key=lambda item: item[1])
DOCUMENTO_TIPO.append((0, "Todos"))
print_choices("DOCUMENTO_TIPO", DOCUMENTO_TIPO)

DOCUMENTO_CATEGORIA = [(value, key) for key, value in fnet.categories.items()]
DOCUMENTO_CATEGORIA.sort(key=lambda item: item[1])
print_choices("DOCUMENTO_CATEGORIA", DOCUMENTO_CATEGORIA)
