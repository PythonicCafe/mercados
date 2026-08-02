"""Lista FIIs elegíveis para depósito em garantia na B3.

A partir de 11/05/2026 a B3 passou a aceitar cotas de FIIs como garantia em operações que exigem margem. Os critérios
de elegibilidade, calculados sobre os últimos 84 pregões, são:
- Mediana do volume diário negociado >= R$ 2.000.000,00
- Mediana do número de negócios diário >= 6.000
- Presença em pregão = 100%
- Preço médio de fechamento > R$ 1,00

Referências:
- Anúncio oficial com os critérios detalhados (Bora Investir / B3):
  <https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/fundos-investimento/b3-passa-a-aceitar-fundos-imobiliarios-como-garantia-em-operacoes/>
- Página de garantias aceitas pela Câmara B3:
  <https://www.b3.com.br/pt_br/produtos-e-servicos/compensacao-e-liquidacao/clearing/administracao-de-riscos/garantias/garantias-aceitas/>
- 029-2026-VNC-Ofício Circular - Aceitação de cota de fundo de investimento admitida à negociação na B3 como garantia
  (05/05/2026)
  <https://www.b3.com.br/data/files/90/A3/96/38/4D9FD910E7DB5DD9AC094EA8/OC%20029-2026-VNC%20ACEITACAO%20DE%20COTA%20DE%20FUNDO%20DE%20INVESTIMENTO%20ADMITIDA%20A%20NEGOCIACAO%20NA%20B3%20COMO%20GARANTIA.pdf>
"""

import datetime
import statistics
import sys
from collections import defaultdict
from decimal import Decimal

from mercados.b3 import B3

JANELA_PREGOES = 84
CODIGO_BDI_FII = 12
CODIGO_MERCADO_A_VISTA = 10
VOLUME_MINIMO = Decimal("2_000_000")
NEGOCIOS_MINIMO = 6_000
PRESENCA_MINIMA = 1.0
PRECO_MINIMO = Decimal("1")
b3 = B3()


def negociacoes_fiis(ano):
    """Filtra negociações de FIIs no mercado à vista para o ano informado."""
    resultado = []
    for neg in b3.negociacao_bolsa("ano", datetime.date(ano, 1, 1)):
        if neg.codigo_bdi == CODIGO_BDI_FII and neg.codigo_tipo_mercado == CODIGO_MERCADO_A_VISTA:
            resultado.append(neg)
    return resultado


ano_atual = datetime.datetime.now().year
print(f"Baixando negociações de {ano_atual}...", end="", flush=True, file=sys.stderr)
negociacoes = negociacoes_fiis(ano_atual)
print(f" ok ({len(negociacoes):,} registros)", file=sys.stderr)

datas_pregao = sorted({neg.data for neg in negociacoes})
if len(datas_pregao) < JANELA_PREGOES:
    ano_anterior = ano_atual - 1
    print(
        f"Apenas {len(datas_pregao)} pregões nesse ano, baixando {ano_anterior}...", end="", flush=True, file=sys.stderr
    )
    negociacoes.extend(negociacoes_fiis(ano_anterior))
    datas_pregao = sorted({neg.data for neg in negociacoes})
    print(f" ok ({len(datas_pregao)} pregões no total)", file=sys.stderr)

datas_selecionadas = set(datas_pregao[-JANELA_PREGOES:])
total_pregoes = len(datas_selecionadas)
print(
    f"Janela: {total_pregoes} pregões ({min(datas_selecionadas)} a {max(datas_selecionadas)})",
    file=sys.stderr,
)

por_codigo = defaultdict(list)
for neg in negociacoes:
    if neg.data in datas_selecionadas:
        por_codigo[neg.codigo_negociacao].append(neg)

elegiveis = []
for codigo, negs in por_codigo.items():
    volumes = [neg.volume for neg in negs if neg.volume is not None]
    num_negocios = [neg.negociacoes for neg in negs if neg.negociacoes is not None]
    precos = [neg.preco_ultimo for neg in negs if neg.preco_ultimo is not None]
    if not volumes or not num_negocios or not precos:
        continue
    mediana_volume = statistics.median(volumes)
    mediana_negocios = statistics.median(num_negocios)
    presenca = len(negs) / total_pregoes
    preco_medio = sum(precos) / len(precos)
    if (
        mediana_volume >= VOLUME_MINIMO
        and mediana_negocios >= NEGOCIOS_MINIMO
        and presenca >= PRESENCA_MINIMA
        and preco_medio > PRECO_MINIMO
    ):
        elegiveis.append((codigo, mediana_volume, mediana_negocios, presenca, preco_medio))

elegiveis.sort()
print(f"\nFIIs elegíveis para garantia na B3: {len(elegiveis)}\n")
print(f"{'Código':<10} {'Med. Volume (R$)':>20} {'Med. Negócios':>15} {'Presença':>10} {'Preço Méd. Fech.':>18}")
print("-" * 77)
for codigo, med_vol, med_neg, pres, preco in elegiveis:
    print(f"{codigo:<10} {med_vol:>20,.2f} {med_neg:>15,.0f} {pres:>9.0%} {preco:>18,.2f}")
