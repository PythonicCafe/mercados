"""Baixa e exporta as cotações do último pregão disponível da B3 para códigos selecionados.

A B3 publica um ZIP diário para cada pregão, mas uma consulta pode ocorrer em fim de semana, feriado ou antes da
publicação do arquivo. Este exemplo filtra os códigos de negociação definidos em `CODIGOS_NEGOCIACAO` e tenta a data
de hoje e os sete dias anteriores, até encontrar o último pregão em que ao menos um desses códigos aparece.
"""

import csv
import datetime
from pathlib import Path
from zipfile import BadZipFile

from mercados.b3 import B3, NegociacaoBolsa

DIAS_TESTAR = 8
CODIGOS_NEGOCIACAO = {"POMO4", "XPML11"}


def busca_ultimo_pregao(b3: B3, codigos_negociacao: set[str]) -> tuple[datetime.date, list[NegociacaoBolsa]]:
    """Retorna as cotações do último pregão em que algum código selecionado aparece."""
    hoje = datetime.date.today()
    for dias_atras in range(DIAS_TESTAR):
        data = hoje - datetime.timedelta(days=dias_atras)
        try:
            negociacoes = list(b3.negociacao_bolsa("dia", data))
        except (BadZipFile, ValueError):
            continue
        registros = [negociacao for negociacao in negociacoes if negociacao.codigo_negociacao in codigos_negociacao]
        if registros:
            return data, registros
    codigos = ", ".join(sorted(codigos_negociacao))
    raise RuntimeError(f"Nenhum pregão com os códigos {codigos} foi encontrado nos últimos {DIAS_TESTAR} dias")


b3 = B3()
data, registros = busca_ultimo_pregao(b3, CODIGOS_NEGOCIACAO)
arquivo = Path(f"negocios-b3-{data}.csv")
print(f"Pregão encontrado: {data}")
print(f"Coletados {len(registros)} registros, salvando em {arquivo}.")
with arquivo.open("w", newline="") as fobj:
    writer = csv.DictWriter(fobj, fieldnames=list(registros[0].serialize()))
    writer.writeheader()
    writer.writerows(registro.serialize() for registro in registros)
