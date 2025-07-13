import datetime

from mercados.b3 import B3

b3 = B3()
negocios = b3.negociacao_bolsa("dia", datetime.date(2024, 12, 9))
for negocio in negocios:
    if negocio.codigo_negociacao in ("XPML11", "CPTI11", "ENDD11", "KNCA11", "ITSA4", "PETRX8"):
        print(negocio.codigo_negociacao, negocio.preco_abertura, negocio.preco_ultimo)
