#!/bin/bash
# Roda diversos comandos para ver se vai dar algum erro, mas sem de fato testar a funcionalidade. Previne que pelo
# menos alguns erros mais grosseiros sejam identificados antes que implementemos os testes automatizados mais
# específicos.

export PYTHONPATH=.
export DATA_PATH="data/test"
ontem=$(date -d "yesterday" +%Y-%m-%d)
dia_semana=$(date -d "$ontem" +%u)
if [ "$dia_semana" -eq 7 ]; then  # Domingo
  DATA_INICIAL=$(date -d "$ontem -2 days" +%Y-%m-%d)
elif [ "$dia_semana" -eq 6 ]; then  # Sábado
  DATA_INICIAL=$(date -d "$ontem -1 days" +%Y-%m-%d)
else
  DATA_INICIAL=$ontem
fi
DATA_ANTERIOR=$(date -d "$DATA_INICIAL -15 days" +%Y-%m-%d)

rm -rf "${DATA_PATH}"


# CVM
echo mercados.cvm noticias
python -m mercados.cvm noticias 2024-11-01 "${DATA_PATH}/cvm-noticias.csv"

echo mercados.cvm rad-empresas
python -m mercados.cvm rad-empresas "${DATA_PATH}/cvm-rad-empresas.csv"

echo mercados.cvm rad-busca
python -m mercados.cvm rad-busca -e 'MARCOPOLO S.A. (REGISTRO ATIVO)' -e 'VULCABRAS S.A. (REGISTRO ATIVO)' -i 2024-01-01 -f 2024-12-31 "${DATA_PATH}/cvm-rad-documento.csv"

echo mercados.cvm contas-fundos
python -m mercados.cvm contas-fundos "${DATA_PATH}/cvm-contas-fundos.csv"

echo "mercados.cvm informe-diario-fundo [1]"
python -m mercados.cvm informe-diario-fundo 2024-12-06 "${DATA_PATH}/cvm-informe-diario-fundo-2024-12_1.csv"

echo "mercados.cvm informe-diario-fundo [2]"
python -m mercados.cvm informe-diario-fundo 2024-12 "${DATA_PATH}/cvm-informe-diario-fundo-2024-12_2.csv"

echo "mercados.cvm balancete-fundo-investimento [1]"
python -m mercados.cvm balancete-fundo-investimento 2025-06-01 "${DATA_PATH}/cvm-balancete-fundo-investimento-2025-06_1.csv"

echo "mercados.cvm balancete-fundo-investimento [2]"
python -m mercados.cvm balancete-fundo-investimento 2025-06 "${DATA_PATH}/cvm-balancete-fundo-investimento-2025-06_2.csv"

echo "mercados.cvm balancete-fundo-estruturado [1]"
python -m mercados.cvm balancete-fundo-estruturado 2025-06-01 "${DATA_PATH}/cvm-balancete-fundo-estruturado-2025-06_1.csv"

echo "mercados.cvm balancete-fundo-estruturado [2]"
python -m mercados.cvm balancete-fundo-estruturado 2025-06 "${DATA_PATH}/cvm-balancete-fundo-estruturado-2025-06_2.csv"


# FundosNET
echo mercados.fundosnet
python -m mercados.fundosnet -i 2024-10-01 -f 2024-10-03 "${DATA_PATH}/fnet-documento.csv"


# BCB
echo mercados.bcb ajustar-selic dia
python -m mercados.bcb ajustar-selic dia 2024-01-01 2024-12-01 1000.00

echo mercados.bcb ajustar-selic mês
python -m mercados.bcb ajustar-selic mês 2024-01-01 2024-11-30 1000.00

echo mercados.bcb serie-temporal
python -m mercados.bcb serie-temporal -i 2024-10-01 -f 2024-12-31 -F md CDI


# B3

echo mercados.b3 valor-indice
python -m mercados.b3 valor-indice IBOVESPA 2025 "${DATA_PATH}/b3-valor-indice-IBOVESPA-2025.csv"

echo mercados.b3 carteira-indice
python -m mercados.b3 carteira-indice IFIX dia "${DATA_PATH}/b3-carteira-indice-IFIX-dia.csv"

echo mercados.b3 ultimas-cotacoes
python -m mercados.b3 ultimas-cotacoes POMO4 "${DATA_PATH}/b3-ultimas-cotacoes.csv"

echo mercados.b3 negociacao-bolsa
python -m mercados.b3 negociacao-bolsa dia 2024-12-06 "${DATA_PATH}/b3-negociacao-bolsa-2024-12-06.csv"

echo mercados.b3 negociacao-balcao
python -m mercados.b3 negociacao-balcao "${DATA_PATH}/b3-negociacao-balcao.csv"

echo mercados.b3 intradiaria-baixar
python -m mercados.b3 intradiaria-baixar "$DATA_INICIAL" "${DATA_PATH}/b3-intradiaria-${DATA_INICIAL}.zip"

echo mercados.b3 intradiaria-converter
python -m mercados.b3 intradiaria-converter -c XPML11 "${DATA_PATH}/b3-intradiaria-${DATA_INICIAL}.zip" "${DATA_PATH}/b3-intradiaria-XPML11-${DATA_INICIAL}.csv"

echo mercados.b3 bdr
python -m mercados.b3 bdr "${DATA_PATH}/b3-bdr.csv"

echo mercados.b3 fundo-listado
python -m mercados.b3 fundo-listado "${DATA_PATH}/b3-fundo-listado.csv"

echo mercados.b3 fundo-listado detalhe
python -m mercados.b3 fundo-listado --detalhe "${DATA_PATH}/b3-fundo-listado-detalhe.csv"

echo mercados.b3 cra-documents # TODO: não funciona!
python -m mercados.b3 cra-documents "${DATA_PATH}/b3-cra-documents.csv"

echo mercados.b3 cri-documents # TODO: não funciona!
python -m mercados.b3 cri-documents "${DATA_PATH}/b3-cri-documents.csv"

echo mercados.b3 debentures
python -m mercados.b3 debentures "${DATA_PATH}/b3-debentures.csv"

echo mercados.b3 fiagro-dividends
python -m mercados.b3 fiagro-dividends "${DATA_PATH}/b3-fiagro-dividends.csv"

echo mercados.b3 fiagro-documents
python -m mercados.b3 fiagro-documents "${DATA_PATH}/b3-fiagro-documents.csv" # TODO: funciona parcialmente

echo mercados.b3 fiagro-subscriptions
python -m mercados.b3 fiagro-subscriptions "${DATA_PATH}/b3-fiagro-subscriptions.csv" # TODO: não funciona!

echo mercados.b3 fii-dividends
python -m mercados.b3 fii-dividends "${DATA_PATH}/b3-fii-dividends.csv"

echo mercados.b3 fii-documents
python -m mercados.b3 fii-documents "${DATA_PATH}/b3-fii-documents.csv" # TODO: testar

echo mercados.b3 fii-subscriptions
python -m mercados.b3 fii-subscriptions "${DATA_PATH}/b3-fii-subscriptions.csv"

echo mercados.b3 fiinfra-dividends
python -m mercados.b3 fiinfra-dividends "${DATA_PATH}/b3-fiinfra-dividends.csv"

echo mercados.b3 fiinfra-documents
python -m mercados.b3 fiinfra-documents "${DATA_PATH}/b3-fiinfra-documents.csv" # TODO: testar

echo mercados.b3 fiinfra-subscriptions
python -m mercados.b3 fiinfra-subscriptions "${DATA_PATH}/b3-fiinfra-subscriptions.csv"

echo mercados.b3 fip-dividends
python -m mercados.b3 fip-dividends "${DATA_PATH}/b3-fip-dividends.csv"

echo mercados.b3 fip-documents
python -m mercados.b3 fip-documents "${DATA_PATH}/b3-fip-documents.csv" # TODO: testar

echo mercados.b3 fip-subscriptions
python -m mercados.b3 fip-subscriptions "${DATA_PATH}/b3-fip-subscriptions.csv"


# B3 - Clearing
TICKER="ABEV3"
rm -f $DATA_PATH/clearing-*.csv

echo mercados.b3 clearing-acoes-custodiadas
python -m mercados.b3 clearing-acoes-custodiadas "$DATA_INICIAL" "$DATA_PATH/b3-clearing-acoes-custodiadas.csv"

echo mercados.b3 clearing-creditos-de-proventos
python -m mercados.b3 clearing-creditos-de-proventos "$DATA_INICIAL" "$DATA_PATH/b3-clearing-creditos-de-proventos.csv"

echo mercados.b3 clearing-custodia-fungivel
python -m mercados.b3 clearing-custodia-fungivel "$DATA_INICIAL" "$DATA_PATH/b3-clearing-custodia-fungivel.csv"

echo mercados.b3 clearing-emprestimos-registrados
python -m mercados.b3 clearing-emprestimos-registrados --codigo_negociacao "$TICKER" "$DATA_ANTERIOR" "$DATA_INICIAL" "$DATA_PATH/b3-clearing-emprestimos-registrados.csv"

echo mercados.b3 clearing-emprestimos-negociados
python -m mercados.b3 clearing-emprestimos-negociados --codigo_negociacao "$TICKER" --doador 'BTG PACTUAL CTVM S/A' "$DATA_INICIAL" "$DATA_PATH/b3-clearing-emprestimos-negociados.csv"

echo mercados.b3 clearing-emprestimos-em-aberto
python -m mercados.b3 clearing-emprestimos-em-aberto --codigo_negociacao "$TICKER" "$DATA_ANTERIOR" "$DATA_INICIAL" "$DATA_PATH/b3-clearing-emprestimos-em-aberto.csv"

echo mercados.b3 clearing-opcoes-flexiveis
python -m mercados.b3 clearing-opcoes-flexiveis "$DATA_INICIAL" "$DATA_PATH/b3-clearing-opcoes-flexiveis.csv"

echo mercados.b3 clearing-prazo-deposito-titulos
python -m mercados.b3 clearing-prazo-deposito-titulos "$DATA_INICIAL" "$DATA_PATH/b3-clearing-prazo-deposito-titulos.csv"

echo mercados.b3 clearing-posicoes-em-aberto
python -m mercados.b3 clearing-posicoes-em-aberto "$DATA_INICIAL" "$DATA_PATH/b3-clearing-posicoes-em-aberto.csv"

echo mercados.b3 clearing-swap
python -m mercados.b3 clearing-swap "$DATA_INICIAL" "$DATA_PATH/b3-clearing-swap.csv"

echo mercados.b3 clearing-termo-eletronico
python -m mercados.b3 clearing-termo-eletronico "$DATA_INICIAL" "$DATA_PATH/b3-clearing-termo-eletronico.csv"

# TODO: implementar para mercados.cota_fundo (caso o arquivo continue na biblioteca)
# TODO: implementar para mercados.rad (caso o arquivo continue na biblioteca)
