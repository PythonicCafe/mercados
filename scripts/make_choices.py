from pprint import pprint

from mercadobr.fundosnet import FundosNet


fnet = FundosNet()
categorias = [(b, a) for a, b in fnet.categories.items()]
DOCUMENTO_CATEGORIA = tuple(sorted(categorias, key=lambda item: item[1]))
print("DOCUMENTO_CATEGORIA = ", end="")
pprint(DOCUMENTO_CATEGORIA)

tipos = [(0, "Todos")]
for value in fnet.types.values():
    for item in value:
        key = (item["id"], item["descricao"])
        if key not in tipos:
            tipos.append(key)
DOCUMENTO_TIPO = tuple(sorted(tipos, key=lambda item: item[1]))
print("DOCUMENTO_TIPO = ", end="")
pprint(DOCUMENTO_TIPO)
