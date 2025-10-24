# Contribuindo

Caso queira contribuir com o projeto e rodar a versão em desenvolvimento em sua máquina, você pode utilizar os atalhos
disponíveis no `Makefile` para construir um container que possui todas as dependências instaladas. Necessita dos
programas `make`, `docker` (com o compose). Para listar os atalhos, execute:

```shell
make help
```

Algumas premissas para o desenvolvimento:

- Documentação, comentários, nomes de funções/métodos e estruturas de dados devem estar em Português do Brasil
  - Palavras em Inglês podem ser usadas no código, desde que sejam jargões da computação amplamente utilizados
    (exemplo: módulo `utils`)
- Partes mais críticas do código devem ter testes automatizados, como a extração de dados de um formato específico
  (*parsing*) para os modelos/dataclasses usados. Os testes devem conter dados reais, obfuscando dados pessoais
  sensíveis que possam existir, que devem ser salvos no próprio repositório
- Mensagens de commit devem ser claras e, caso aplicável, deve conter um dos seguintes prefixos:
  - `b3: `, para alterações em funcionalidades relacionadas aos dados coletados da B3
  - `bcb: `, para alterações em funcionalidades relacionadas aos dados coletados do Banco Central do Brasil
  - `cli: `, para alterações gerais na interface de linha de comando
  - `cvm: `, para alterações em funcionalidades relacionados aos dados coletados da CVM
  - `dev: `, para alterações referentes ao desenvolvimento (`Makefile`, linter etc.)
  - `doc: `, para alterações em documentação
  - `fnet: `, para alterações em funcionalidades relacionados aos dados coletados do sistema FundosNET
  - `ibge: `, para alterações em funcionalidades relacionados aos dados coletados do IBGE
  - `lib: `, para alterações gerais na biblioteca que não sejam utilitários nem empacotamento
  - `pkg: `, para alterações relacionadas ao empacotamento
  - `stn: `, para alterações em funcionalidades relacionadas aos dados coletados da Secretaria do Tesouro Nacional
  - `util: `, para alterações em funções/métodos utilitários (módulo `utils.py`)
