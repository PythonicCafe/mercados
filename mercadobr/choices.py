def reverse_choices(data):
    return {value: key for key, value in data}


# TODO: usar mesmos códigos internos da API do sistema fnet (baixar todas
# categorias, espécies etc.)

AMORTIZACAO_TIPO = (
    (1, "Parcial"),
    (2, "Total"),
)

ATIVO_TIPO = (
    ("BDR", "BDR"),
    ("BNS", "SUBSCRIPTION BONUS FOR MISCELLANEOUS"),
    ("BNS B/A", "SUBSCRIPTION BONUS FOR PREFERRED SHARES"),
    ("BNS ORD", "SUBSCRIPTION BONUS FOR COMMON SHARES"),
    ("BNS P/A", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS A"),
    ("BNS P/B", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS B"),
    ("BNS P/C", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS C"),
    ("BNS P/D", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS D"),
    ("BNS P/E", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS E"),
    ("BNS P/F", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS F"),
    ("BNS P/G", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS G"),
    ("BNS P/H", "SUBSCRIPTION BONUS FOR PREFERRED SHARES CLASS H"),
    ("BNS PRE", "SUBSCRIPTION BONUS FOR PREFERRED SHARES"),
    ("CDA", "COMMON SHARE DEPOSIT CERTIFICATE"),
    ("CI", "INVESTMENT FUND"),
    ("CPA", "ADDITIONAL CONSTRUCTION AND OPERATION POTENTIAL"),
    ("DIR", "SUBSCRIPTION RIGHTS – MISCELLANEOUS (BONUS, DEBENTURES, ETC)"),
    ("DIR ORD", "SUBSCRIPTION RIGHTS TO COMMON SHARES"),
    ("DIR P/A", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS A"),
    ("DIR P/B", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS B"),
    ("DIR P/C", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS C"),
    ("DIR P/D", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS D"),
    ("DIR P/E", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS E"),
    ("DIR P/F", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS F"),
    ("DIR P/G", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS G"),
    ("DIR P/H", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES CLASS H"),
    ("DIR PR", "SUBSCRIPTION RIGHTS TO REDEEMABLE PREF. SHARES"),
    ("DIR PRA", "SUBSCRIPTION RIGHTS TO REDEEMABLE PREF. SHARES CLASS A"),
    ("DIR PRB", "SUBSCRIPTION RIGHTS TO REDEEMABLE PREF. SHARES CLASS B"),
    ("DIR PRC", "SUBSCRIPTION RIGHTS TO REDEEMABLE PREF. SHARES CLASS C"),
    ("DIR PRE", "SUBSCRIPTION RIGHTS TO PREFERRED SHARES"),
    ("LFT", "FINANCIAL TREASURY BILL"),
    ("M1 REC", "RECEIPT OF SUBSCRIPTION TO MISCELLANEOUS"),
    ("ON", "NOMINATIVE COMMON SHARES"),
    ("ON P", "NOMINATIVE COMMON SHARES WITH DIFFERENTIATED RIGHTS"),
    ("ON REC", "RECEIPT OF SUBSCRIPTION FOR COMMON SHARES"),
    ("OR", "NOMINATIVE COMMON REDEEMABLE SHARES"),
    ("OR P", "NOMINATIVE COMMON REDEEMABLE SHARES W/ DIFFERENTIATED RIGHTS"),
    ("PCD", "CONSOLIDATED DEBT POSITION"),
    ("PN", "NOMINATIVE PREFERRED SHARES"),
    ("PN  P", "NOMINATIVE PREFERRED SHARES WITH DIFFERENTIATED RIGHTS"),
    ("PN REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES"),
    ("PNA", "NOMINATIVE PREFERRED SHARES CLASS A"),
    ("PNA P", "NOMINATIVE PREFERRED SHARES CLASS A W/ DIFFERENTIATED RIGHTS"),
    ("PNA REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS A"),
    ("PNB", "NOMINATIVE PREFERRED SHARES CLASS B"),
    ("PNB P", "NOMINATIVE PREFERRED SHARES CLASS B W/ DIFFERENTIATED RIGHTS"),
    ("PNB REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS B"),
    ("PNC", "NOMINATIVE PREFERRED SHARES CLASS C"),
    ("PNC P", "NOMINATIVE PREFERRED SHARES CLASS C W/ DIFFERENTIATED RIGHTS"),
    ("PNC REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS C"),
    ("PND", "NOMINATIVE PREFERRED SHARES CLASS D"),
    ("PND P", "NOMINATIVE PREFERRED SHARES CLASS D W/ DIFFERENTIATED RIGHTS"),
    ("PND", "REC RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS D"),
    ("PNE", "NOMINATIVE PREFERRED SHARES CLASS"),
    ("PNE P", "NOMINATIVE PREFERRED SHARES CLASS E W/ DIFFERENTIATED RIGHTS"),
    ("PNE", "RECRECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS E"),
    ("PNF", "NOMINATIVE PREFERRED SHARES CLASS F"),
    ("PNF P", "NOMINATIVE PREFERRED SHARES CLASS F W/ DIFFERENTIATED RIGHTS"),
    ("PNF REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS F"),
    ("PNG", "NOMINATIVE PREFERRED SHARES CLASS G"),
    ("PNG P", "NOMINATIVE PREFERRED SHARES CLASS G W/ DIFFERENTIATED RIGHTS"),
    ("PNG REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS G"),
    ("PNH", "NOMINATIVE PREFERRED SHARES CLASS H"),
    ("PNH P", "NOMINATIVE PREFERRED SHARES CLASS H W/ DIFFERENTIATED RIGHTS"),
    ("PNH REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES CLASS H"),
    ("PNR", "NOMINATIVE PREFERRED REDEEMABLE SHARES"),
    ("PNV", "NOMINATIVE PREFERRED SHARES WITH VOTING RIGHTS"),
    ("PNV P", "NOMINATIVE PREFERRED SHARES CLASS V W/ DIFFERENTIATED RIGHTS"),
    ("PNV REC", "RECEIPT OF SUBSCRIPTION FOR PREFERRED SHARES W/VOTING RIGHTS"),
    ("PR  P", "NOMINATIVE PREFERRED REDEEMABLE SHARES W/ DIFFERENTIATED RIGHTS"),
    ("PRA", "NOMINATIVE PREFERRED SHARES CLASS A REDEEMABLE"),
    ("PRA P", "NOMINATIVE PREFERRED SHARES CLASS A REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRA REC", "RECEIPT OF SUBSCRIPTION RIGHTS TO REDEEMABLE SHARES CLASS A"),
    ("PRB", "NOMINATIVE PREFERRED SHARES CLASS B REDEEMABLE"),
    ("PRB P", "NOMINATIVE PREFERRED SHARES CLASS B REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRB REC", "RECEIPT OF SUBSCRIPTION RIGHTS TO REDEEMABLE SHARES CLASS B"),
    ("PRC", "NOMINATIVE PREFERRED SHARES CLASS C REDEEMABLE"),
    ("PRC P", "NOMINATIVE PREFERRED SHARES CLASS C REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRC REC", "RECEIPT OF SUBSCRIPTION RIGHTS TO REDEEMABLE SHARES CLASS C"),
    ("PRD", "NOMINATIVE PREFERRED SHARES CLASS D REDEEMABLE"),
    ("PRD P", "NOMINATIVE PREFERRED SHARES CLASS D REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRE", "NOMINATIVE PREFERRED SHARES CLASS E REDEEMABLE"),
    ("PRE P", "NOMINATIVE PREFERRED SHARES CLASS E REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRF", "NOMINATIVE PREFERRED SHARES CLASS F REDEEMABLE"),
    ("PRF P", "NOMINATIVE PREFERRED SHARES CLASS F REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRG", "NOMINATIVE PREFERRED SHARES CLASS G REDEEMABLE"),
    ("PRG P", "NOMINATIVE PREFERRED SHARES CLASS G REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRH", "NOMINATIVE PREFERRED SHARES CLASS H REDEEMABLE"),
    ("PRH P", "NOMINATIVE PREFERRED SHARES CLASS H REDEEMABLE W/ DIFFERENTIATED RIGHTS"),
    ("PRV", "NOMINATIVE PREFERRED SHARES WITH VOTING RIGHTS REDEEMABLE"),
    ("PRV P", "NOMINATIVE PREFERRED SHARES REDEEM. W/ DIFFERENTIATED RIGHTS AND VOTING RIGHTS"),
    ("R", "BASKET OF NOMINATIVE SHARES"),
    ("REC", "RECEIPT OF SUBSCRIPTION MISCELLANEOUS"),
    ("REC PR", "RECEIPT OF SUBSCRIPTION TO REDEEMABLE PREF. SHARES"),
    ("RON", "BASKET OF NOMINATIVE COMMON SHARES"),
    ("TPR", "PERPETUAL BONDS WITH VARIABLE INCOME BASED ON ROYALTIES"),
    ("UNT", "SHARE DEPOSIT CERTIFICATE – MISCELLANEOUS"),
    ("UNT", "UNITS"),
    ("UP", "ROGATORY LETTERS"),
    ("WRT", "DEBENTURE WARRANTS"),
)

INDICE_CORRECAO = (
    (1, "US$"),
    (2, "TJLP"),
    (8, "IGPM (PROTECTED)"),
    (9, "URV"),
)

MERCADO_TIPO = (
    (10, "CASH"),
    (12, "EXERCISE OF CALL OPTIONS"),
    (13, "EXERCISE OF PUT OPTIONS"),
    (17, "AUCTION"),
    (20, "FACTIONARY"),
    (30, "TERM"),
    (50, "FORWARD WITH GAIN RETENTION"),
    (60, "FORWARD WITH CONTINUOUS MOVEMENT"),
    (70, "CALL OPTIONS"),
    (80, "PUT OPTIONS"),
)

ATIVO_TIPO_BDI = (
    (2, "ROUND LOT"),
    (5, "BMFBOVESPA REGULATIONS SANCTION"),
    (6, "STOCKS OF COS. UNDER REORGANIZATION"),
    (7, "EXTRAJUDICIAL RECOVERY"),
    (8, "JUDICIAL RECOVERY"),
    (9, "TEMPORARY ESPECIAL MANAGEMENT"),
    (10, "RIGHTS AND RECEIPTS"),
    (11, "INTERVENTION"),
    (12, "REAL ESTATE FUNDS"),
    (14, "INVESTMENT CERTIFICATES / DEBENTURES / PUBLIC DEBT SECURITIES"),
    (18, "BONDS"),
    (22, "BONUSES (PRIVATE)"),
    (26, "POLICIES / BONUSES / PUBLIC SECURITIES"),
    (32, "EXERCISE OF INDEX CALL OPTIONS"),
    (33, "EXERCISE OF INDEX PUT OPTIONS"),
    (38, "EXERCISE OF CALL OPTIONS"),
    (42, "EXERCISE OF PUT OPTIONS"),
    (46, "AUCTION OF NON-QUOTED SECURITIES"),
    (48, "PRIVATIZATION AUCTION"),
    (49, "AUCTION OF ECONOMICAL RECOVERY FUND OF ESPIRITO SANTO STATE"),
    (50, "AUCTION"),
    (51, "FINOR AUCTION"),
    (52, "FINAM AUCTION"),
    (53, "FISET AUCTION"),
    (54, "AUCTION OF SHARES IN ARREARS"),
    (56, "SALES BY COURT ORDER"),
    (58, "OTHERS"),
    (60, "SHARE SWAP"),
    (61, "GOAL"),
    (62, "TERM"),
    (66, "DEBENTURES WITH MATURITY DATES OF UP TO 3 YEARS"),
    (68, "DEBENTURES WITH MATURITY DATES GREATER THAN 3 YEARS"),
    (70, "FORWARD WITH CONTINUOUS MOVEMENT"),
    (71, "FORWARD WITH GAIN RETENTION"),
    (74, "INDEX CALL OPTIONS"),
    (75, "INDEX PUT OPTIONS"),
    (78, "CALL OPTIONS"),
    (82, "PUT OPTIONS"),
    (83, "DEBENTURES AND PROMISSORY NOTES BOVESPAFIX"),
    (84, "DEBENTURES AND PROMISSORY NOTES SOMAFIX"),
    (90, "REGISTERED TERM VIEW"),
    (96, "FACTIONARY"),
    (99, "GRAND TOTAL"),
)

BALCAO_ORIGEM = (
    (1, "NoMe"),
    (2, "Negociacao - Tela"),
    (3, "Cetip Trader"),
    (4, "Registro"),
    (5, "Pre-registro - Voice"),
)

DOCUMENTO_CATEGORIA = (
    (25, "Acordo de Acionista"),
    (19, "Aditamento de Termo de Securitização"),
    (2, "Assembleia"),
    (37, "Ata da Reunião do Conselho de Administração"),
    (11, "Atos de Deliberação do Administrador"),
    (18, "Averbação ou Registro do Termo de Securitização"),
    (4, "Aviso aos Cotistas"),
    (14, "Aviso aos Cotistas - Estruturado"),
    (20, "Aviso aos Investidores"),
    (3, "Comunicado ao Mercado"),
    (26, "Comunicação de alteração do auditor independente"),
    (27, "Dados Econômico Financeiros"),
    (16, "Documentos de Oferta de Distribuição Pública"),
    (28, "Estatuto Social"),
    (29, "Falência"),
    (1, "Fato Relevante"),
    (39, "Formulário Cadastral"),
    (30, "Formulário de Referência"),
    (42, "Informações da SPE subsidiária integral - exclusivo para S2"),
    (23, "Informações para Registro Provisório de Oferta de CRI"),
    (21, "Informações para Registro de Oferta de CRA"),
    (22, "Informações para Registro de Oferta de CRI"),
    (31, "Informe Mensal de Outros Títulos de Securitização"),
    (32, "Informe Trimestral"),
    (6, "Informes Periódicos"),
    (41, "Instrumento de Emissão e aditamentos"),
    (13, "Laudo de Avaliação (Conclusão de Negócio)"),
    (24, "Listagem e  Admissão à  Negociação  de Cotas"),
    (12, "Oferta Pública de Aquisição de Cotas"),
    (8, "Oferta Pública de Distribuição de Cotas"),
    (10, "Outras Informações"),
    (40, "Outros Títulos de Securitização"),
    (33, "Política de Negociação de Valores Mobiliários"),
    (9, "Políticas de Governança Corporativa"),
    (34, "Recuperação Extrajudicial"),
    (35, "Recuperação Judicial"),
    (5, "Regulamento"),
    (15, "Regulamento de Emissores B3"),
    (36, "Relatório de agência classificadora de risco"),
    (7, "Relatórios"),
    (17, "Termo de Securitização"),
    (0, "Todos"),
    (38, "Valores mobiliários detidos"),
)
DOCUMENTO_ESPECIE = (
    (1, "Ata da Assembleia"),
    (2, "Boletim de voto a distância"),
    (3, "Carta Consulta"),
    (4, "Definitivo"),
    (5, "Edital de Convocação"),
    (6, "Laudo de Avaliação"),
    (7, "Mapa sintético de instruções de voto"),
    (8, "Outros Documentos"),
    (9, "Preliminar"),
    (10, "Proposta do Administrador"),
    (11, "Protocolo e Justificativa de Cisão, Fusão ou Incorporação"),
    (12, "Relatório do Representante de Cotistas"),
    (13, "Sumário das Decisões"),
)
DOCUMENTO_MODALIDADE = (
    ("AP", "Apresentação"),
    ("RE", "Reapresentação Espontânea"),
    ("RC", "Reapresentação por Exigência"),
)
DOCUMENTO_SITUACAO = (
    ("A", "Ativo"),
    ("I", "Inativo"),
    ("C", "Cancelado"),
)
DOCUMENTO_STATUS = (
    ("AC", "Ativo com visualização"),
    ("IC", "Inativo com visualização"),
    ("CC", "Cancelado com visualização"),
)
DOCUMENTO_TIPO = (
    (125, "AG - Especial de Investidores"),
    (3, "AGE"),
    (1, "AGO"),
    (2, "AGO/E"),
    (83, 'ANEXO "11 - I" CVM 600/18'),
    (90, "Anexo 39-V (art. 10 §1º, inciso I da ICVM 472)"),
    (84, "Anexo I - ICVM 414/04"),
    (16, "Anúncio de Encerramento"),
    (72, "Anúncio de Encerramento de Distribuição Pública"),
    (14, "Anúncio de Início"),
    (74, "Anúncio de Início de Distribuição Pública"),
    (127, "Assembleias"),
    (75, "Aviso ao Mercado"),
    (15, "Aviso ao Mercado"),
    (18, "Aviso de Modificação de Oferta"),
    (65, "Balancete"),
    (122, "Com Regime Fiduciário"),
    (63, "Composição da Carteira (CDA)"),
    (78, "Comunicado de Encerramento de Oferta com Esforços Restritos"),
    (80, "Comunicado de Início de Oferta com Esforços Restritos"),
    (128, "Comunicados"),
    (76, "Comunicação de Modificação de Oferta"),
    (129, "Dados Econômico Financeiros"),
    (51, "Demonstração Financeira de Encerramento"),
    (30, "Demonstrações Financeiras"),
    (146, "Demonstrações Financeiras - Encerramento de atividades"),
    (145, "Demonstrações Financeiras - Fusão, cisão e incorporação"),
    (144, "Demonstrações Financeiras - Substituição de administrador"),
    (104, "Demonstrações Financeiras Anuais"),
    (91, "Demonstrações Financeiras de Devedores ou Coobrigados"),
    (105, "Demonstrações Financeiras de Grandes Devedores"),
    (116, "Demonstrações Financeiras de Grandes Devedores"),
    (20, "Divulgação de Fato Relevante"),
    (34, "Edital de Oferta Pública de Aquisição de Cotas"),
    (38, "Edital de Oferta Pública de Aquisição de Cotas - Concorrente"),
    (50, "Esclarecimentos de consulta B3 / CVM"),
    (137, "Formulário Cadastral - Estruturado"),
    (103, "Formulário de Liberação para Negociação das Cotas"),
    (100, "Formulário de Liberação para Negociação das Cotas"),
    (138, "Formulário de Referência - Estruturado"),
    (98, "Formulário de Subscrição de Cotas (Estruturado)"),
    (118, "Informações Trimestrais (ITR)"),
    (6, "Informe Anual"),
    (47, "Informe Anual Estruturado"),
    (64, "Informe Diário"),
    (130, "Informe Mensal"),
    (4, "Informe Mensal"),
    (40, "Informe Mensal Estruturado"),
    (81, "Informe Mensal de CRA"),
    (86, "Informe Mensal de CRI"),
    (8, "Informe Semestral - DFC e Relatório do Administrador"),
    (5, "Informe Trimestral"),
    (45, "Informe Trimestral Estruturado"),
    (32, "Instrumento Particular de Alteração do Regulamento"),
    (31, "Instrumento Particular de Constituição/Encerramento do Fundo"),
    (46, "Instrumento Particular de Emissão de Cotas"),
    (126, "Instrumento de Emissão e aditamentos"),
    (23, "Investimento"),
    (35, "Laudo de Avaliação"),
    (139, "Lâmina de Oferta de FIDC"),
    (140, "Lâmina de Oferta de Fundos Fechados"),
    (141, "Lâmina de Oferta de Securitização"),
    (37, "Manifestação do Administrador / Gestor"),
    (53, "Material de Divulgação"),
    (120, "Mudança de Auditor"),
    (21, "Negociação de Cotas"),
    (25, "Outras Políticas"),
    (49, "Outros Comunicados Não Considerados Fatos Relevantes"),
    (19, "Outros Documentos"),
    (29, "Outros Documentos"),
    (12, "Outros Relatórios"),
    (22, "Participação em Assembleia"),
    (106, "Pedido de Falência"),
    (108, "Pedido de homologação do Plano de Recuperação Extrajudicial"),
    (26, "Perfil do Fundo"),
    (101, "Perfil do Fundo (Estruturado)"),
    (110, "Petição inicial"),
    (111, "Plano de Recuperação Judicial"),
    (10, "Press - Release"),
    (66, "Processo de enforcement"),
    (13, "Prospecto"),
    (82, "Prospecto de Distribuição Pública"),
    (92, "Protocolo Inicial"),
    (93, "Protocolo para Cumprimento de Exigências"),
    (94, "Protocolo para Pedido de Prorrogação/Interrupção"),
    (131, "Registro CVM"),
    (52, "Relatório Anual"),
    (11, "Relatório Anual"),
    (9, "Relatório Gerencial"),
    (71, "Relatório de Agente Fiduciário"),
    (68, "Relatório de Agência de Rating"),
    (7, "Relatório do Representante de Cotistas"),
    (33, "Relação das demandas judiciais ou extrajudiciais"),
    (41, "Rendimentos e Amortizações"),
    (27, "Rentabilidade"),
    (17, "Restritos - ICVM 476"),
    (124, "Sem regime fiduciário"),
    (107, "Sentença denegatória ou concessiva"),
    (109, "Sentença denegatória ou concessiva"),
    (112, "Sentença denegatória ou concessiva"),
    (117, "Suplemento C"),
    (119, "Suplemento D"),
    (0, "Todos"),
)

FUNDO_TIPO = (
    (0, "Todos"),
    (1, "Fundo Imobiliário"),
    (2, "FIDC"),
    (3, "ETF"),
    (4, "ETF RF"),
    (7, "Fundo Setorial"),
)

RENDA_FIXA_TIPO = (
    (1, "LF"),
    (2, "COE"),
    (3, "CRA"),
    (4, "NC"),
    (5, "CFF"),
    (6, "CRI"),
    (7, "DEB"),
)

RENDIMENTO_TIPO = (
    (1, "Rendimento"),
    (2, "Amortização"),
)

INFORME_FII_TIPO = (
    (1, "Informe Mensal"),
    (2, "Informe Trimestral"),
    (3, "Informe Anual"),
)
INFORME_FII_PRAZO_DURACAO = (
    (1, "Indeterminado"),
    (2, "Determinado"),
)
INFORME_FII_PUBLICO_ALVO = (
    (1, "Investidores em Geral"),
    (2, "Investidor Qualificado"),
    (3, "Investidor Profissional"),
    (4, "Investidor Qualificado e Profissional"),
)
INFORME_FII_SEGMENTO = (
    (1, "Híbrido"),
    (2, "Hospital"),
    (3, "Hotel"),
    (4, "Lajes corporativas"),
    (5, "Logística"),
    (6, "Outros"),
    (7, "Residencial"),
    (8, "Shoppings"),
    (9, "Títulos e Valores mobiliários"),
)
INFORME_FII_GESTAO_TIPO = (
    (1, "Ativa"),
    (2, "Passiva"),
)
INFORME_FII_MANDATO = (
    (1, "Renda"),
    (2, "Híbrido"),
    (3, "Títulos e Valores mobiliários"),
    (4, "Desenvolvimento para Renda"),
    (5, "Desenvolvimento para Venda"),
)

INFORME_FII_MANDATO_DICT = reverse_choices(INFORME_FII_MANDATO)
INFORME_FII_GESTAO_TIPO_DICT = reverse_choices(INFORME_FII_GESTAO_TIPO)
INFORME_FII_SEGMENTO_DICT = reverse_choices(INFORME_FII_SEGMENTO)
INFORME_FII_PUBLICO_ALVO_DICT = reverse_choices(INFORME_FII_PUBLICO_ALVO)
INFORME_FII_PRAZO_DURACAO_DICT = reverse_choices(INFORME_FII_PRAZO_DURACAO)
INFORME_FII_TIPO_DICT = reverse_choices(INFORME_FII_TIPO)
AMORTIZACAO_TIPO_DICT = reverse_choices(AMORTIZACAO_TIPO)
ATIVO_TIPO_BDI_DICT = reverse_choices(ATIVO_TIPO_BDI)
ATIVO_TIPO_DICT = reverse_choices(ATIVO_TIPO)
BALCAO_ORIGEM_DICT = reverse_choices(BALCAO_ORIGEM)
DOCUMENTO_CATEGORIA_DICT = reverse_choices(DOCUMENTO_CATEGORIA)
DOCUMENTO_ESPECIE_DICT = reverse_choices(DOCUMENTO_ESPECIE)
DOCUMENTO_MODALIDADE_DICT = reverse_choices(DOCUMENTO_MODALIDADE)
DOCUMENTO_SITUACAO_DICT = reverse_choices(DOCUMENTO_SITUACAO)
DOCUMENTO_STATUS_DICT = reverse_choices(DOCUMENTO_STATUS)
DOCUMENTO_TIPO_DICT = reverse_choices(DOCUMENTO_TIPO)
FUNDO_TIPO_DICT = reverse_choices(FUNDO_TIPO)
INDICE_CORRECAO_DICT = reverse_choices(INDICE_CORRECAO)
MERCADO_TIPO_DICT = reverse_choices(MERCADO_TIPO)
RENDA_FIXA_TIPO_DICT = reverse_choices(RENDA_FIXA_TIPO)
RENDIMENTO_TIPO_DICT = reverse_choices(RENDIMENTO_TIPO)

CATEGORIA_TIPO_ESTRUTURADOS_STR = (
    ("Informes Periódicos", "Informe Mensal Estruturado"),
    ("Informes Periódicos", "Informe Trimestral Estruturado"),
    ("Informes Periódicos", "Informe Anual Estruturado"),
    ("Informes Periódicos", "Composição da Carteira (CDA)"),
    ("Informes Periódicos", "Informe Diário"),
    ("Informes Periódicos", "Balancete"),
    (
        "Oferta Pública de Distribuição de Cotas",
        "Anexo 39-V (art. 10 §1º, inciso I da ICVM 472)",
    ),
    (
        "Oferta Pública de Distribuição de Cotas",
        "Formulário de Subscrição de Cotas (Estruturado)",
    ),
    (
        "Oferta Pública de Distribuição de Cotas",
        "Formulário de Liberação para Negociação das Cotas",
    ),
    ("Outras Informações", "Perfil do Fundo (Estruturado)"),
    ("Aviso aos Cotistas - Estruturado", "Rendimentos e Amortizações"),
    (
        "Documentos de Oferta de Distribuição Pública",
        "Formulário de Liberação para Negociação das Cotas",
    ),
)
CATEGORIA_TIPO_ESTRUTURADOS_IDS = [
    (DOCUMENTO_CATEGORIA_DICT[categoria], DOCUMENTO_TIPO_DICT[tipo])
    for categoria, tipo in CATEGORIA_TIPO_ESTRUTURADOS_STR
]
