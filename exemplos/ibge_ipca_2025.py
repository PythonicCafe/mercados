import datetime

from mercados.ibge import IBGE

ibge = IBGE()
indice = "IPCA"  # Teste com "IPCA-15" e "INPC"
hoje = datetime.datetime.now().date()
ultimo = None
for taxa in ibge.historico(indice):
    if (hoje - taxa.data).days > 365:
        continue
    atual = taxa.valor
    if ultimo is None:
        variacao_str = "N/A"
    else:
        variacao = 100 * (atual / ultimo - 1)
        variacao_str = f"{variacao:.2f}%"
    print(f"{indice} em {taxa.data}: {atual:.2f} (variação: {variacao_str})")
    ultimo = taxa.valor
