"""
Busca debêntures das Americanas S.A. negociadas em balcão para janeiro de 2026

Encontrará registros nos dias 2026-01-07 e 2026-01-30.
"""

import datetime

from mercados.b3 import B3

b3 = B3()
data = datetime.date(2026, 1, 5)
while data < datetime.date(2026, 2, 1):
    print(f"Buscando debêntures para {data}")
    for negocio in b3.negociacao_balcao(data):
        if negocio.instrumento == "DEB" and negocio.codigo_isin.startswith("BRAMER"):  # Debêntures das Americanas S.A.
            print(negocio)
    data += datetime.timedelta(days=1)
