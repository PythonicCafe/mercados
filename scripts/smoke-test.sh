#!/bin/bash
# Roda diversos comandos para ver se vai dar algum erro, mas sem de fato testar a funcionalidade. Previne que pelo
# menos alguns erros mais grosseiros sejam identificados antes que implementemos os testes automatizados mais
# específicos.

export PYTHONPATH=.
export DATA_PATH="data/test"
rm -rf "${DATA_PATH}"


# CVM
echo mercados.cvm noticias
python -m mercados.cvm noticias 2024-11-01 "${DATA_PATH}/cvm-noticias.csv"

echo mercados.cvm rad-empresas
python -m mercados.cvm rad-empresas "${DATA_PATH}/cvm-rad-empresas.csv"

echo mercados.cvm rad-busca
python -m mercados.cvm rad-busca -e 'MARCOPOLO S.A. (REGISTRO ATIVO)' -e 'VULCABRAS S.A. (REGISTRO ATIVO)' -i 2024-01-01 -f 2024-12-31 "${DATA_PATH}/cvm-rad-documento.csv"

echo mercados.cvm informe-diario-fundo
python -m mercados.cvm informe-diario-fundo 2024-12-06 "${DATA_PATH}/cvm-informe-diario-fundo-2024-12-06.csv"


# FundosNET
echo mercados.fundosnet
python -m mercados.fundosnet -i 2024-10-01 -f 2024-10-03 "${DATA_PATH}/fnet.csv"


# BCB
echo mercados.bcb ajustar-selic dia
python -m mercados.bcb ajustar-selic dia 2024-01-01 2024-12-01 1000.00

echo mercados.bcb ajustar-selic mês
python -m mercados.bcb ajustar-selic mês 2024-01-01 2024-11-30 1000.00

echo mercados.bcb serie-temporal
python -m mercados.bcb serie-temporal -i 2024-10-01 -f 2024-12-31 -F md CDI


# B3

echo mercados.b3 negociacao-bolsa
python -m mercados.b3 negociacao-bolsa dia 2024-12-06 ${DATA_PATH}/b3-negociacao-bolsa-2024-12-06.csv

echo mercados.b3 negociacao-balcao
python -m mercados.b3 negociacao-balcao "${DATA_PATH}/negociacao-balcao.csv"

echo mercados.b3 intraday-baixar
python -m mercados.b3 intraday-baixar 2024-12-06 "${DATA_PATH}/intraday-2024-12-06.zip"

echo mercados.b3 intraday-converter
python -m mercados.b3 intraday-converter -c XPML11 "${DATA_PATH}/intraday-2024-12-06.zip" "${DATA_PATH}/intraday-XPML11-2024-12-06.csv"

echo mercados.b3 fundo-listado
python -m mercados.b3 fundo-listado "${DATA_PATH}/fundo-listado.csv"

echo mercados.b3 cra-documents
python -m mercados.b3 cra-documents "${DATA_PATH}/cra-documents.csv"

echo mercados.b3 cri-documents
python -m mercados.b3 cri-documents "${DATA_PATH}/cri-documents.csv"

echo mercados.b3 debentures
python -m mercados.b3 debentures "${DATA_PATH}/debentures.csv"

echo mercados.b3 fiagro-dividends
python -m mercados.b3 fiagro-dividends "${DATA_PATH}/fiagro-dividends.csv"

echo mercados.b3 fiagro-documents
python -m mercados.b3 fiagro-documents "${DATA_PATH}/fiagro-documents.csv"

echo mercados.b3 fiagro-subscriptions
python -m mercados.b3 fiagro-subscriptions "${DATA_PATH}/fiagro-subscriptions.csv"

echo mercados.b3 fii-dividends
python -m mercados.b3 fii-dividends "${DATA_PATH}/fii-dividends.csv"

echo mercados.b3 fii-documents
python -m mercados.b3 fii-documents "${DATA_PATH}/fii-documents.csv"

echo mercados.b3 fii-subscriptions
python -m mercados.b3 fii-subscriptions "${DATA_PATH}/fii-subscriptions.csv"

echo mercados.b3 fiinfra-dividends
python -m mercados.b3 fiinfra-dividends "${DATA_PATH}/fiinfra-dividends.csv"

echo mercados.b3 fiinfra-documents
python -m mercados.b3 fiinfra-documents "${DATA_PATH}/fiinfra-documents.csv"

echo mercados.b3 fiinfra-subscriptions
python -m mercados.b3 fiinfra-subscriptions "${DATA_PATH}/fiinfra-subscriptions.csv"

echo mercados.b3 fip-dividends
python -m mercados.b3 fip-dividends "${DATA_PATH}/fip-dividends.csv"

echo mercados.b3 fip-documents
python -m mercados.b3 fip-documents "${DATA_PATH}/fip-documents.csv"

echo mercados.b3 fip-subscriptions
python -m mercados.b3 fip-subscriptions "${DATA_PATH}/fip-subscriptions.csv"


# B3 - Clearing
TICKER="ABEV3"
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
rm -f $DATA_PATH/clearing-*.csv

echo mercados.b3 clearing-acoes-custodiadas
python -m mercados.b3 clearing-acoes-custodiadas "$DATA_INICIAL" $DATA_PATH/clearing-acoes-custodiadas.csv

echo mercados.b3 clearing-creditos-de-proventos
python -m mercados.b3 clearing-creditos-de-proventos "$DATA_INICIAL" $DATA_PATH/clearing-creditos-de-proventos.csv

echo mercados.b3 clearing-custodia-fungivel
python -m mercados.b3 clearing-custodia-fungivel "$DATA_INICIAL" $DATA_PATH/clearing-custodia-fungivel.csv

echo mercados.b3 clearing-emprestimos-registrados
python -m mercados.b3 clearing-emprestimos-registrados --ticker "$TICKER" "$DATA_ANTERIOR" "$DATA_INICIAL" $DATA_PATH/clearing-emprestimos-registrados.csv

echo mercados.b3 clearing-emprestimos-negociados
python -m mercados.b3 clearing-emprestimos-negociados --ticker "$TICKER" --doador 'BTG PACTUAL CTVM S/A' "$DATA_INICIAL" $DATA_PATH/clearing-emprestimos-negociados.csv

echo mercados.b3 clearing-emprestimos-em-aberto
python -m mercados.b3 clearing-emprestimos-em-aberto --ticker "$TICKER" "$DATA_ANTERIOR" "$DATA_INICIAL" $DATA_PATH/clearing-emprestimos-em-aberto.csv

echo mercados.b3 clearing-opcoes-flexiveis
python -m mercados.b3 clearing-opcoes-flexiveis "$DATA_INICIAL" $DATA_PATH/clearing-opcoes-flexiveis.csv

echo mercados.b3 clearing-prazo-deposito-titulos
python -m mercados.b3 clearing-prazo-deposito-titulos "$DATA_INICIAL" $DATA_PATH/clearing-prazo-deposito-titulos.csv

echo mercados.b3 clearing-posicoes-em-aberto
python -m mercados.b3 clearing-posicoes-em-aberto "$DATA_INICIAL" $DATA_PATH/clearing-posicoes-em-aberto.csv

echo mercados.b3 clearing-swap
python -m mercados.b3 clearing-swap "$DATA_INICIAL" $DATA_PATH/clearing-swap.csv

echo mercados.b3 clearing-termo-eletronico
python -m mercados.b3 clearing-termo-eletronico "$DATA_INICIAL" $DATA_PATH/clearing-termo-eletronico.csv

# TODO: implementar para mercados.cota_fundo (caso o arquivo continue na biblioteca)
# TODO: implementar para mercados.rad (caso o arquivo continue na biblioteca)
