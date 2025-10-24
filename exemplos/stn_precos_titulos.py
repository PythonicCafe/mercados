import datetime

from mercados.stn import Tesouro

tesouro = Tesouro()
hoje = datetime.datetime.now().date()
semana_passada = hoje - datetime.timedelta(days=7)
historico = []
for titulo in tesouro.historico_titulos():
    if semana_passada <= titulo.data <= hoje:
        print(f"{titulo.data}\t{titulo.nome} ({titulo.vencimento})\tR$ {titulo.preco:,}")
