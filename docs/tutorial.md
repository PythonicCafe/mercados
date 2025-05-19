# Tutorial

A biblioteca está dividida em módulos, onde cada módulo é responsável por coletar as informações de um órgão/sistema,
por exemplo: `mercados.cvm` coleta dados disponibilizados pela CVM.

## Instalação

A biblioteca `mercados` está disponível no [Python Package Index (PyPI)](https://pypi.org/). Instale-a executando:

```shell
pip install mercados
```

## Linha de comando

Além de ser usada como biblioteca Python, você também pode utilizar o projeto via linha de comando (quase todos os
módulos da biblioteca possuem uma interface de linha de comando). Execute `python -m mercados.X --help`, onde `X` é o
nome do módulo (`bcb`, `cvm`, `b3`, `fundosnet` etc.).

Para exemplos de uso da interface de linha de comando, veja o script
[`scripts/smoke-tests.sh`](https://github.com/PythonicCafe/mercados/blob/develop/scripts/smoke-test.sh).


## Banco Central

Dados que podem ser baixados do Banco Central do Brasil:
- Sistema NovoSelic: Ajuste de valor pela Selic por dia ou mês
- Séries temporais


### Séries temporais

A biblioteca `mercados` consegue coletar dados do [Sistema Gerenciador de Séries
Temporais](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries), que
possui milhares de séries disponíveis, incluindo Selic e CDI. O sistema também consolida séries de outros órgãos, como
IPCA (do IBGE), IGP-M (da FGV), dentre outros. Vamos a um exemplo para baixar os dados do CDI:

```python
import datetime
from mercados.bcb import BancoCentral

hoje = datetime.datetime.now().date()
semana_passada = hoje - datetime.timedelta(days=7)
bc = BancoCentral()
for taxa in bc.serie_temporal("CDI", inicio=semana_passada, fim=hoje):
    print(taxa)
```

O retorno será algo como:

```python
Taxa(data=datetime.date(2024, 12, 3), valor=Decimal('0.041957'))
Taxa(data=datetime.date(2024, 12, 4), valor=Decimal('0.041957'))
Taxa(data=datetime.date(2024, 12, 5), valor=Decimal('0.041957'))
Taxa(data=datetime.date(2024, 12, 6), valor=Decimal('0.041957'))
Taxa(data=datetime.date(2024, 12, 9), valor=Decimal('0.041957'))
```

Execute `print(bc.series.keys())` para ver a lista de todas as séries temporais disponíveis na biblioteca. Dica: caso
você encontre uma série no SGS e queria adicionar à biblioteca, você pode adicionar um par ao dicionário `bc.series`
com o comando `bc.series["nova série"] = 123456` (troque `nova série` pelo nome que gostaria de usar e `123456` pelo
código da mesma).


## CVM

Dados que podem ser baixados da CVM:

- [Notícias](https://www.gov.br/cvm/pt-br/assuntos/noticias)
- [FundosNET](https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM): documentos publicados,
  incluindo a extração de alguns tipos de XML
- [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): lista de companhias abertas
- [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): busca por documentos publicados
- [Portal de Dados Abertos](https://dados.cvm.gov.br/): informe diário de fundos de investimento


## B3

Dados que podem ser baixados da B3:
- Cotação diária da negociação em bolsa (um registro por ativo)
- Micro-dados de negociação em bolsa (*intraday*, um registro por negociação)
- Cotação diária da negociação em balcão
- Cadastro de fundos listados
- Cadastro de debêntures ativas
- Informações cadastrais sobre CRAs, CRIs, FIIs, FI-Infras, FI-Agros e FIPs listados
- Documentos de CRAs, CRIs, FIIs, FI-Infras, FI-Agros e FIPs listados
- Dividendos de FI-Infras e FI-Agros

### Negociação em bolsa

No exemplo abaixo, pegamos os dados para negociação de diversos tipos de ativos listados: fundo de investimento
imobiliário (FII), fundo de investimento em infraestrutura (FI-Infra), fundo de investimento em participações de
infraestrutura (FIP-IE) fundo de investimento no agroenegócio (FI-Agro), ações e opções. Para cada negociação, o
sistema possui dados como preços de abertura, médio, fechamento, mínimo e máximo, nome exibido no pregão, quantidade e
volume negociado.

```python
import datetime
from mercados.b3 import B3

b3 = B3()
negocios = b3.negociacao_bolsa("dia", datetime.date(2024, 12, 9))
for negocio in negocios:
    if negocio.codigo_negociacao in ("XPML11", "CPTI11", "ENDD11", "KNCA11", "ITSA4", "PETRX8"):
        print(negocio.codigo_negociacao, negocio.preco_abertura, negocio.preco_ultimo)
```

Deve retornar algo como:

```
ITSA4 9.28 9.30
XPML11 97.70 96.62
KNCA11 81.80 80.71
ENDD11 104.57 101.55
CPTI11 80.43 81.48
PETRX8 0.20 0.20
```
