import datetime

from mercados.bcb import BancoCentral

hoje = datetime.datetime.now().date()
semana_passada = hoje - datetime.timedelta(days=7)
bc = BancoCentral()
for taxa in bc.serie_temporal("CDI", inicio=semana_passada, fim=hoje):
    print(taxa)
