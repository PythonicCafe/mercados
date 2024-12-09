#!/bin/bash
# Roda diversos comandos para ver se vai dar algum erro, mas sem de fato testar a funcionalidade. Previne que pelo
# menos alguns erros mais grosseiros sejam identificados antes que implementemos os testes automatizados mais
# específicos.

export PYTHONPATH=.
export DATA_PATH="data/test"
rm -rf "${DATA_PATH}"


# CVM
echo mercadobr.cvm noticias
python -m mercadobr.cvm noticias 2024-11-01 "${DATA_PATH}/cvm-noticias.csv"

echo mercadobr.cvm rad-empresas
python -m mercadobr.cvm rad-empresas "${DATA_PATH}/cvm-rad-empresas.csv"

echo mercadobr.cvm rad-busca
python -m mercadobr.cvm rad-busca -e 'MARCOPOLO S.A. (REGISTRO ATIVO)' -e 'VULCABRAS S.A. (REGISTRO ATIVO)' -i 2024-01-01 -f 2024-12-31 "${DATA_PATH}/cvm-rad-documento.csv"

echo mercadobr.cvm informe-diario-fundo
python -m mercadobr.cvm informe-diario-fundo 2024-12-06 "${DATA_PATH}/cvm-informe-diario-fundo-2024-12-06.csv"


# FundosNET
echo mercadobr.fundosnet
python -m mercadobr.fundosnet -i 2024-10-01 -f 2024-10-03 "${DATA_PATH}/fnet.csv"


# BCB
echo mercadobr.bcb ajustar-selic dia
python -m mercadobr.bcb ajustar-selic dia 2024-01-01 2024-12-01 1000.00

echo mercadobr.bcb ajustar-selic mês
python -m mercadobr.bcb ajustar-selic mês 2024-01-01 2024-11-30 1000.00

echo mercadobr.bcb serie-temporal
python -m mercadobr.bcb serie-temporal -i 2024-10-01 -f 2024-12-31 -F md CDI


# B3

echo mercadobr.b3 negociacao-bolsa
python -m mercadobr.b3 negociacao-bolsa dia 2024-12-06 ${DATA_PATH}/b3-negociacao-bolsa-2024-12-06.csv

echo mercadobr.b3 negociacao-balcao
python -m mercadobr.b3 negociacao-balcao "${DATA_PATH}/negociacao-balcao.csv"

echo mercadobr.b3 intraday-baixar
python -m mercadobr.b3 intraday-baixar 2024-12-06 "${DATA_PATH}/intraday-2024-12-06.zip"

echo mercadobr.b3 intraday-converter
python -m mercadobr.b3 intraday-converter -c XPML11 "${DATA_PATH}/intraday-2024-12-06.zip" "${DATA_PATH}/intraday-XPML11-2024-12-06.csv"

echo mercadobr.b3 fundo-listado
python -m mercadobr.b3 fundo-listado "${DATA_PATH}/fundo-listado.csv"

echo mercadobr.b3 cra-documents
python -m mercadobr.b3 cra-documents "${DATA_PATH}/cra-documents.csv"

echo mercadobr.b3 cri-documents
python -m mercadobr.b3 cri-documents "${DATA_PATH}/cri-documents.csv"

echo mercadobr.b3 debentures
python -m mercadobr.b3 debentures "${DATA_PATH}/debentures.csv"

echo mercadobr.b3 fiagro-dividends
python -m mercadobr.b3 fiagro-dividends "${DATA_PATH}/fiagro-dividends.csv"

echo mercadobr.b3 fiagro-documents
python -m mercadobr.b3 fiagro-documents "${DATA_PATH}/fiagro-documents.csv"

echo mercadobr.b3 fiagro-subscriptions
python -m mercadobr.b3 fiagro-subscriptions "${DATA_PATH}/fiagro-subscriptions.csv"

echo mercadobr.b3 fii-dividends
python -m mercadobr.b3 fii-dividends "${DATA_PATH}/fii-dividends.csv"

echo mercadobr.b3 fii-documents
python -m mercadobr.b3 fii-documents "${DATA_PATH}/fii-documents.csv"

echo mercadobr.b3 fii-subscriptions
python -m mercadobr.b3 fii-subscriptions "${DATA_PATH}/fii-subscriptions.csv"

echo mercadobr.b3 fiinfra-dividends
python -m mercadobr.b3 fiinfra-dividends "${DATA_PATH}/fiinfra-dividends.csv"

echo mercadobr.b3 fiinfra-documents
python -m mercadobr.b3 fiinfra-documents "${DATA_PATH}/fiinfra-documents.csv"

echo mercadobr.b3 fiinfra-subscriptions
python -m mercadobr.b3 fiinfra-subscriptions "${DATA_PATH}/fiinfra-subscriptions.csv"

echo mercadobr.b3 fip-dividends
python -m mercadobr.b3 fip-dividends "${DATA_PATH}/fip-dividends.csv"

echo mercadobr.b3 fip-documents
python -m mercadobr.b3 fip-documents "${DATA_PATH}/fip-documents.csv"

echo mercadobr.b3 fip-subscriptions
python -m mercadobr.b3 fip-subscriptions "${DATA_PATH}/fip-subscriptions.csv"

# TODO: implementar para mercadobr.cota_fundo (caso o arquivo continue na biblioteca)
# TODO: implementar para mercadobr.rad (caso o arquivo continue na biblioteca)
