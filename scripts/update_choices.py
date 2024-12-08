"""Extrai opções disponíveis nos filtros do FundosNET e monta lista de valores possíveis"""

from pprint import pprint

from mercadobr.fundosnet import FundosNet


def print_choices(name, values):
    print(f"{name} = ", end="")
    pprint(tuple(values))


fnet = FundosNet()

DOCUMENTO_CATEGORIA = [(value, key) for key, value in fnet.categories.items()]
DOCUMENTO_CATEGORIA.sort(key=lambda item: item[1])
print_choices("DOCUMENTO_CATEGORIA", DOCUMENTO_CATEGORIA)

DOCUMENTO_TIPO = []
for values in fnet.types.values():
    for item in values:
        values = (item["id"], item["descricao"])
        if values not in DOCUMENTO_TIPO:
            DOCUMENTO_TIPO.append(values)
DOCUMENTO_TIPO.sort(key=lambda item: item[1])
DOCUMENTO_TIPO.append((0, "Todos"))
print_choices("DOCUMENTO_TIPO", DOCUMENTO_TIPO)


# TODO: implementar para `choices.AMORTIZACAO_TIPO`
# TODO: implementar para `choices.ATIVO_TIPO`
# TODO: implementar para `choices.ATIVO_TIPO_BDI`
# TODO: implementar para `choices.BALCAO_ORIGEM`
# TODO: implementar para `choices.DOCUMENTO_ESPECIE`
# TODO: implementar para `choices.DOCUMENTO_MODALIDADE`
# TODO: implementar para `choices.DOCUMENTO_SITUACAO`
# TODO: implementar para `choices.DOCUMENTO_STATUS`
# TODO: implementar para `choices.FUNDO_TIPO`
# TODO: implementar para `choices.INDICE_CORRECAO`
# TODO: implementar para `choices.INFORME_FII_GESTAO_TIPO`
# TODO: implementar para `choices.INFORME_FII_MANDATO`
# TODO: implementar para `choices.INFORME_FII_PRAZO_DURACAO`
# TODO: implementar para `choices.INFORME_FII_PUBLICO_ALVO`
# TODO: implementar para `choices.INFORME_FII_SEGMENTO`
# TODO: implementar para `choices.INFORME_FII_TIPO`
# TODO: implementar para `choices.MERCADO_TIPO`
# TODO: implementar para `choices.RENDA_FIXA_TIPO`
# TODO: implementar para `choices.RENDIMENTO_TIPO`
# TODO: implementar forma de atualizar o arquivo `choices.py` automaticamente
