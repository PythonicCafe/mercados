import csv
import datetime
from pathlib import Path
from mercados.cvm import CVM

cnpj_fundo = "18302338000163"  # Ártica Long Term FIA
csv_filename = Path("data") / "cota-artica-long-term.csv"
csv_filename.parent.mkdir(exist_ok=True, parents=True)
inicio = datetime.date(2019, 9, 1)  # Mês em que migrou de clube para fundo (dados de clube não ficam disponíveis)
fim = datetime.datetime.now().date()
atual = inicio
print(f"Salvando dados em {csv_filename}")
cvm = CVM()
with csv_filename.open(mode="w") as fobj:
    writer = None
    while atual <= fim:
        print(f"Coletando para o mês {atual.month:02d}/{atual.year}")
        for informe in cvm.informe_diario_fundo(atual):
            # O método `informe_diario_fundo` ignora o campo "dia" da data passada e retorna todos os informes diários
            # de todos os fundos para o ano/mês
            if informe.fundo_cnpj == cnpj_fundo:
                row = informe.serialize()  # Transforma em dicionário
                if writer is None:
                    writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
        atual = (atual.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)  # Próximo mês
