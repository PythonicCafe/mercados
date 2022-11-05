def reverse_choices(data):
    return {value: key for key, value in data}


# TODO: usar mesmos códigos internos da API do sistema fnet (baixar todas
# categorias, espécies etc.)
DOCUMENTO_CATEGORIA = (
    (0, "Todos"),
    (1, "Fato Relevante"),
    (2, "Assembleia"),
    (3, "Comunicado ao Mercado"),
    (4, "Aviso aos Cotistas"),
    (5, "Regulamento"),
    (6, "Informes Periódicos"),
    (7, "Relatórios"),
    (8, "Oferta Pública de Distribuição de Cotas"),
    (9, "Políticas de Governança Corporativa"),
    (10, "Outras Informações"),
    (11, "Atos de Deliberação do Administrador"),
    (12, "Oferta Pública de Aquisição de Cotas"),
    (13, "Laudo de Avaliação (Conclusão de Negócio)"),
    (14, "Aviso aos Cotistas - Estruturado"),
    (15, "Regulamento de Emissores B3"),
    (16, "Documentos de Oferta de Distribuição Pública"),
    (17, "Termo de Securitização"),
    (18, "Averbação ou Registro do Termo de Securitização"),
    (19, "Aditamento de Termo de Securitização"),
    (20, "Aviso aos Investidores"),
    (21, "Informações para Registro de Oferta de CRA"),
    (22, "Informações para Registro de Oferta de CRI"),
    (23, "Informações para Registro Provisório de Oferta de CRI"),
    (24, "Listagem e Admissão à Negociação de Cotas"),
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
    (0, "Todos"),
    (1, "AGO"),
    (2, "AGO/E"),
    (3, "AGE"),
    (4, "Informe Mensal"),
    (5, "Informe Trimestral"),
    (6, "Informe Anual"),
    (7, "Relatório do Representante de Cotistas"),
    (8, "Informe Semestral - DFC e Relatório do Administrador"),
    (9, "Relatório Gerencial"),
    (10, "Press - Release"),
    (11, "Relatório Anual"),
    (12, "Outros Relatórios"),
    (13, "Prospecto"),
    (14, "Anúncio de Início"),
    (15, "Aviso ao Mercado"),
    (16, "Anúncio de Encerramento"),
    (17, "Restritos - ICVM 476"),
    (18, "Aviso de Modificação de Oferta"),
    (19, "Outros Documentos"),
    (20, "Divulgação de Fato Relevante"),
    (21, "Negociação de Cotas"),
    (22, "Participação em Assembleia"),
    (23, "Investimento"),
    (25, "Outras Políticas"),
    (26, "Perfil do Fundo"),
    (27, "Rentabilidade"),
    (29, "Outros Documentos"),
    (30, "Demonstrações Financeiras"),
    (31, "Instrumento Particular de Constituição/Encerramento do Fundo"),
    (32, "Instrumento Particular de Alteração do Regulamento"),
    (33, "Relação das demandas judiciais ou extrajudiciais"),
    (34, "Edital de Oferta Pública de Aquisição de Cotas"),
    (35, "Laudo de Avaliação"),
    (37, "Manifestação do Administrador / Gestor"),
    (38, "Edital de Oferta Pública de Aquisição de Cotas - Concorrente"),
    (40, "Informe Mensal Estruturado"),
    (41, "Rendimentos e Amortizações"),
    (45, "Informe Trimestral Estruturado"),
    (46, "Instrumento Particular de Emissão de Cotas"),
    (47, "Informe Anual Estruturado"),
    (49, "Outros Comunicados Não Considerados Fatos Relevantes"),
    (50, "Esclarecimentos de consulta B3 / CVM"),
    (51, "Demonstração Financeira de Encerramento"),
    (52, "Relatório Anual"),
    (53, "Material de Divulgação"),
    (63, "Composição da Carteira (CDA)"),
    (64, "Informe Diário"),
    (65, "Balancete"),
    (66, "Processo de enforcement"),
    (68, "Relatório de Agência de Rating"),
    (71, "Relatório de Agente Fiduciário"),
    (72, "Anúncio de Encerramento de Distribuição Pública"),
    (74, "Anúncio de Início de Distribuição Pública"),
    (75, "Aviso ao Mercado"),
    (76, "Comunicação de Modificação de Oferta"),
    (78, "Comunicado de Encerramento de Oferta com Esforços Restritos"),
    (80, "Comunicado de Início de Oferta com Esforços Restritos"),
    (81, 'Informe Mensal de CRA (Anexo "37" ICVM 600/18)'),
    (82, "Prospecto de Distribuição Pública"),
    (83, 'ANEXO "11 - I" CVM 600/18'),
    (84, "Anexo I - ICVM 414/04"),
    (85, "Anexo II - ICVM 414/04"),
    (86, "Informe Mensal de CRI (Anexo 32, II ICVM 480)"),
    (90, "Anexo 39-V (art. 10 §1º, inciso I da ICVM 472)"),
    (91, "Demonstrações Financeiras do Devedor ou Coobrigado"),
    (91, "Demonstrações Financeiras de Devedores ou Coobrigados"),
    (92, "Protocolo Inicial"),
    (93, "Protocolo para Cumprimento de Exigências"),
    (94, "Protocolo para Pedido de Prorrogação/Interrupção"),
    (98, "Formulário de Subscrição de Cotas (Estruturado)"),
    (100, "Formulário de Liberação para Negociação das Cotas"),
    (101, "Perfil do Fundo (Estruturado)"),
    (103, "Formulário de Liberação para Negociação das Cotas"),
)

FUNDO_TIPO = (
    (0, "Todos"),
    (1, "Fundo Imobiliário"),
    (2, "FIDC"),
    (3, "ETF"),
    (4, "ETF RF"),
    (7, "Fundo Setorial"),
)

RENDIMENTO_TIPO = (
    (1, "Rendimento"),
    (2, "Amortização"),
)

DOCUMENTO_CATEGORIA_DICT = reverse_choices(DOCUMENTO_CATEGORIA)
DOCUMENTO_ESPECIE_DICT = reverse_choices(DOCUMENTO_ESPECIE)
DOCUMENTO_MODALIDADE_DICT = reverse_choices(DOCUMENTO_MODALIDADE)
DOCUMENTO_SITUACAO_DICT = reverse_choices(DOCUMENTO_SITUACAO)
DOCUMENTO_STATUS_DICT = reverse_choices(DOCUMENTO_STATUS)
DOCUMENTO_TIPO_DICT = reverse_choices(DOCUMENTO_TIPO)
FUNDO_TIPO_DICT = reverse_choices(FUNDO_TIPO)
RENDIMENTO_TIPO_DICT = reverse_choices(RENDIMENTO_TIPO)
