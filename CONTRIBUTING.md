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
  - `[doc] `, para alterações em documentação
  - `[pkg] `, para alterações relacionadas ao empacotamento
  - `[util] `, para alterações em funções/métodos utilitários (módulo `utils.py`)
  - `[BCB] `, para alterações em funcionalidades relacionadas ao Banco Central do Brasil
  - `[Fnet] `, para alterações em funcionalidades relacionados ao sistema FundosNET
  - `[CVM] `, para alterações em funcionalidades relacionados aos sistemas da CVM
  - `[B3] `, para alterações em funcionalidades relacionados aos sistemas da B3
