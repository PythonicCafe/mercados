import csv
import datetime

from mercados.b3 import B3

ativo = "XPML11"
csv_filename = f"b3-aluguel-{ativo}.csv"
b3 = B3()
data_final = datetime.datetime.now().date()  # Hoje
data_inicial = data_final - datetime.timedelta(days=30)  # 1 mês atrás
data = data_final
with open(csv_filename, mode="w") as fobj:
    writer = None
    print(f"Capturando dados de aluguel para {ativo}")
    while data >= data_inicial:
        dados = b3.clearing_emprestimos_registrados(data_inicial=data, data_final=data, codigo_negociacao=ativo)
        resultado = sorted(dados, key=lambda item: item.data, reverse=True)  # Ordena dados pela data (decrescente)
        for item in resultado:
            print(f"  {item}")
            row = item.serialize()  # Transforma `item` (que é uma dataclass) em um dicionário
            if writer is None:
                writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow(row)
        data -= datetime.timedelta(days=1)
