import csv
import datetime

from mercados.b3 import B3

indice_escolhido = "IFIX"
ano_inicial = 2010
ano_atual = datetime.datetime.now().year

b3 = B3()
print("Índices disponíveis:")
for indice in b3.indices:
    print(f"- {indice}")

with open(f"{indice_escolhido}.csv", mode="w") as fobj:
    writer = csv.DictWriter(fobj, fieldnames=["data", "valor"])
    writer.writeheader()
    for ano in range(ano_inicial, ano_atual + 1):
        print(f"Coletando dados do {indice_escolhido} para {ano}")
        for taxa in b3.valor_indice(indice_escolhido, ano):
            writer.writerow({"data": taxa.data, "valor": taxa.valor})
