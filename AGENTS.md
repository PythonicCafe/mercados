# AGENTS.md

> Biblioteca e CLI em Python para coletar, extrair e normalizar dados abertos do mercado financeiro brasileiro a partir das fontes oficiais (B3, BCB, CVM, IBGE e STN).

## Comandos

- Construir ambiente: `make build`
- Testes com cobertura: `make test`; teste selecionado: `TEST_ARGS="-k nome_do_teste" make test`
- Lint e formatação: `make lint` (altera arquivos: _autoflake_ -> _isort_ -> _black_ -> _flake8_)
- Verificação de tipos obrigatória: `mypy --strict mercados tests scripts`
- _Smoke tests_ com rede: `make smoke-test`; exemplos: `make smoke-test-examples`
- Ajuda da CLI: `python -m mercados --help`; regenerar o manual após mudar a CLI: `make man`

Com `ENV_TYPE=development`, os alvos que executam a aplicação rodam diretamente no ambiente atual; nos demais ambientes, usam o serviço `main` do _Docker Compose_. Não considere a alteração pronta sem rodar os testes, o lint e `mypy --strict` aplicáveis; informe explicitamente o que não foi executado.

## Código e dados

- Siga primeiro os padrões já presentes no módulo que está sendo alterado e faça somente a mudança solicitada.
- Todo código novo ou alterado deve ser completamente tipado e passar em `mypy --strict`. Use anotações modernas (`str | None`, `list[T]`); não contorne erros com `Any`, `# type: ignore` ou tipos imprecisos sem uma justificativa técnica explícita.
- Nomes de domínio, documentação, comentários e mensagens da CLI são em PT-BR, sem acentos em identificadores. Código genérico pode usar Inglês. Preserve o idioma de comentários e _docstrings_ existentes.
- Prefira a _stdlib_ e as dependências já adotadas. Não introduza `pandas`; processe CSV com `csv` e valores monetários com `Decimal`.
- Use `pathlib.Path` para caminhos, `dataclass` para dados estruturados e funções de conversão/normalização pequenas e determinísticas. Cada _dataclass_ pública deve manter `serialize()` com chaves na mesma ordem dos campos, pois isso é testado.
- Clientes HTTP devem reutilizar `create_session`, enviar `USER_AGENT`, ter _timeout_ explícito e preservar o tratamento de erros da fonte. Não faça chamadas HTTP reais em testes.
- Trate formatos, _encoding_, colunas e valores das fontes como contratos externos voláteis: inspecione arquivos reais, valide hipóteses sobre o conjunto completo e cubra casos históricos e de borda em testes. Não invente mapeamentos, códigos ou normalizações sem evidência.
- Para valores categóricos recebidos de uma fonte, trate explicitamente todos os valores conhecidos e levante erro com contexto para valores novos ou desconhecidos. Não use um padrão silencioso.

## CLI e módulos de fonte

- A CLI registra módulos de fonte em `mercados.__main__`. Cada módulo participante expõe `_DESCRICAO_CLI`, `_configura_parser_cli(parser)` e `main(args) -> int`; mantenha esse contrato ao adicionar uma fonte ou subcomando.
- Use `argparse`, `Path` para argumentos de caminho e opções longas em _kebab-case_. Dados exportados vão para _stdout_; status e erros vão para _stderr_. A lógica de coleta e transformação não deve imprimir diretamente.
- Preserve os formatos de exportação e use `dicts_to_file` para a saída tabular. Crie diretórios pais antes de gravar um arquivo.
- Para módulos de coleta que possam ser usados isoladamente, mantenha o ponto de entrada `if __name__ == "__main__":` compatível com a CLI principal.

## Testes e documentação

- Use `pytest` com `assert` direto. Teste comportamento e conversões com amostras reais anonimizadas ou dados mínimos representativos em `tests/data/`; não teste detalhes internos.
- Acrescente testes de regressão para correções em _parsers_, _dataclasses_, formatos de fonte ou normalizações. O `pytest` também executa _doctests_; mantenha exemplos corretos.
- Atualize `README.md` quando mudar fontes suportadas, uso público ou formatos de saída. Atualize `docs/mercados.1` via `make man` quando alterar argumentos ou subcomandos.

## Git e manutenção destas instruções

- Commits são atômicos e em PT-BR; não use `git add .`. Antes de preparar uma contribuição, leia `CONTRIBUTING.md`, que é a fonte de requisitos de contribuição e dos prefixos de _commit_.
- Se uma mudança criar, alterar ou remover uma convenção recorrente, comando, contrato de dados/CLI, requisito de teste, ferramenta ou processo que estas instruções devem orientar, atualize este `AGENTS.md` no mesmo trabalho. Remova instruções obsoletas e mantenha-o conciso.
- Se encontrar uma suposição incorreta neste arquivo, corrija-a ou proponha a correção antes de concluir a tarefa.
