SELECT
  quatot::bigint AS quantidade,
  CASE
    WHEN ptoexe = '0000000000000' THEN NULL::bigint
    ELSE ptoexe::bigint
  END AS pontos_strike,

  TO_DATE(date_of_exchange, 'yyyymmdd') AS data,
  CASE
    WHEN datven = '99991231' THEN NULL::date
    ELSE TO_DATE(datven, 'yyyymmdd')
  END AS data_vencimento,
  totneg::integer AS negociacoes,
  fatcot::integer AS lote,

  indopc::smallint AS indice_correcao,
  dismes::smallint AS distribuicao,
  codbdi::smallint AS codigo_bdi,
  tpmerc::smallint AS codigo_tipo_mercado,
  CASE
    WHEN prazot = '' THEN NULL::smallint
    ELSE prazot::smallint
  END AS prazo_termo,

  codisi::char(12) AS codigo_isin,
  codneg::char(12) AS codigo_negociacao,
  modref AS moeda,
  nomres AS nome_pregao,
  especi AS tipo_papel,
  preabe::decimal(13, 2) / 100 AS preco_abertura,
  premax::decimal(13, 2) / 100 AS preco_maximo,
  premin::decimal(13, 2) / 100 AS preco_minimo,
  premed::decimal(13, 2) / 100 AS preco_medio,
  preult::decimal(13, 2) / 100 AS preco_ultimo,
  preofc::decimal(13, 2) / 100 AS preco_melhor_oferta_compra,
  preofv::decimal(13, 2) / 100 AS preco_melhor_oferta_venda,
  voltot::decimal(18, 2) / 100 AS volume,
  preexe::decimal(13, 2) / 100 AS preco_execucao
FROM (
  SELECT
    TRIM(SUBSTR(t, 3, 8)) AS date_of_exchange,
    TRIM(SUBSTR(t, 11, 2)) AS codbdi,
    TRIM(SUBSTR(t, 13, 12)) AS codneg,
    TRIM(SUBSTR(t, 25, 3)) AS tpmerc,
    TRIM(SUBSTR(t, 28, 12)) AS nomres,
    TRIM(SUBSTR(t, 40, 10)) AS especi,
    TRIM(SUBSTR(t, 50, 3)) AS prazot,
    TRIM(SUBSTR(t, 53, 4)) AS modref,
    TRIM(SUBSTR(t, 57, 13)) AS preabe,
    TRIM(SUBSTR(t, 70, 13)) AS premax,
    TRIM(SUBSTR(t, 83, 13)) AS premin,
    TRIM(SUBSTR(t, 96, 13)) AS premed,
    TRIM(SUBSTR(t, 109, 13)) AS preult,
    TRIM(SUBSTR(t, 122, 13)) AS preofc,
    TRIM(SUBSTR(t, 135, 13)) AS preofv,
    TRIM(SUBSTR(t, 148, 5)) AS totneg,
    TRIM(SUBSTR(t, 153, 18)) AS quatot,
    TRIM(SUBSTR(t, 171, 18)) AS voltot,
    TRIM(SUBSTR(t, 189, 13)) AS preexe,
    TRIM(SUBSTR(t, 202, 1)) AS indopc,
    TRIM(SUBSTR(t, 203, 8)) AS datven,
    TRIM(SUBSTR(t, 211, 7)) AS fatcot,
    TRIM(SUBSTR(t, 218, 13)) AS ptoexe,
    TRIM(SUBSTR(t, 231, 12)) AS codisi,
    TRIM(SUBSTR(t, 243, 3)) AS dismes
  FROM {original_table}
  WHERE SUBSTR(t, 1, 2) = '01'
) AS t
