# mercados

`mercados` é uma biblioteca em Python e uma interface de linha de comando (CLI) para baixar, extrair e limpar dados do
mercado financeiro brasileiro de diversas organizações, como:
- Comissão de Valores Mobiliários (CVM)
- Banco Central do Brasil (BCB)
- Secretaria do Tesouro Nacional (STN)
- Bolsa, Brasil e Balcão (B3)
- Instituto Brasileiro de Geografia e Estatística (IBGE)

A biblioteca foi desenvolvida ao longo dos últimos anos, já é utilizada em sistemas que estão em produção e tem como
objetivo ser a melhor, mais robusta e fácil opção para acessar dados do mercado financeiro e macroeconômicos de maneira
programática. O foco da biblioteca é coletar e tratar as informações nas fontes originais/oficiais e apenas de dados
que sejam abertos/gratuitos. Por isso, não possui dados que são vendidos (como os que são em tempo real). Ela é
implementada de maneira a usar o mínimo de dependências possível (sem `pandas`, por exemplo) e da maneira mais
Pythônica (idiomática) possível, em Português.

A biblioteca é desenvolvida e testada em sistema Debian GNU/Linux com Python 3.11. É possível que funcione em versões
mais recentes e em algumas anteriores sem problemas; como ela é feita totalmente em Python, também deve funcionar sem
problemas em outros sistemas, como Windows e Mac OS X. Instale-a executando:

```shell
pip install mercados
```

Para acessar dados do IBGE, é necessário instalar mais dependências. Instale-as com:
```shell
pip install mercados[ibge]
```

O código da `mercados` está licenciado sob [LGPL versão 3](https://www.gnu.org/licenses/lgpl-3.0.pt-br.html). Você só
deve utilizá-la se aceitar os termos da licença (veja mais detalhes na seção abaixo).

A documentação ainda está em desenvolvimento (veja o material em construção em [docs/tutorial.md](docs/tutorial.md)).

> **Atenção**: apesar de todo o código funcionar e de ter sido testado em diversos sistemas em produção que o utilizam,
> algumas mudanças poderão acontecer na interface da biblioteca até que ela atinja a versão `1.0.0`, ou seja, atente-se
> a atualizações. Veja mais detalhes sobre o versionamento adotado em [*semantic versioning*](https://semver.org/).

Caso queira contribuir com o projeto, veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

`mercados` tem como licença a [Licença Pública Geral Menor GNU versão 3 (LGPL
v3)](https://www.gnu.org/licenses/lgpl-3.0.pt-br.html). Em resumo:

**✅ O que você pode fazer:**
- Usar a biblioteca em projetos proprietários ou livres
- Modificar o código-fonte da biblioteca
- Distribuir a biblioteca original ou modificada em conjunto com um outro programa, desde que:
  - Notifique seu usuário de que a biblioteca é usada no seu programa e está licenciada sob LGPL v3
  - Forneça uma cópia da LGPL v3 junto com a distribuição do seu programa

**🚫 O que você não pode fazer:**
- Restringir a liberdade do usuário do seu programa de modificar a biblioteca
- Distribuir a biblioteca (original ou modificada) sem fornecer o código-fonte
- Incorporar partes significativas da biblioteca no seu código sem informar e fornecer a licença

## Dados disponíveis

- [IBGE](https://ibge.gov.br/):
  - [Séries históricas de
    Índices](https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html?=&t=series-historicas)
    (IPCA, IPCA-15 e INPC)
- [CVM](https://www.gov.br/cvm/pt-br):
  - [Notícias](https://www.gov.br/cvm/pt-br/assuntos/noticias)
  - [FundosNET](https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM): documentos publicados,
    incluindo a extração de alguns tipos de XML
  - [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): lista de companhias abertas
  - [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): busca por documentos publicados
  - [Portal de Dados Abertos](https://dados.cvm.gov.br/): informe diário de fundos de investimento
  - Balancete de fundos [de investimento](https://dados.cvm.gov.br/dataset/fi-doc-balancete) e
    [estruturados](https://dados.cvm.gov.br/dataset/fie-doc-balancete)
- [BCB](https://www.bcb.gov.br/):
  - Sistema NovoSelic: Ajuste de valor pela Selic por dia ou mês
  - [Sistema Gerenciador de Séries
    Temporais](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries):
    milhares de séries temporais, incluindo Selic, CDI e também publicadas por outros órgãos, como IPCA e IGP-M
- [Secretaria do Tesouro Nacional](https://www.gov.br/tesouronacional/pt-br):
  - Histórico de preços de títulos
- [B3](https://www.b3.com.br/pt_br/para-voce):
  - Valor histórico de diversos índices
  - Cotação diária da negociação em bolsa (um registro por ativo)
  - Preços a cada 5 minutos do último pregão por ativo (com atraso de 15min)
  - Negociações intradiárias em bolsa (um registro por negociação)
  - Cotação diária da negociação em balcão
  - Cadastro de fundos listados (FII, FI-Infra, FI-Agro, FIP, FIDC e ETF)
  - Cadastro de debêntures ativas
  - Cadastro de BDRs listados
  - Cadastro de empresas listadas
  - Informações cadastrais sobre CRAs e CRIs
  - Documentos de CRAs, CRIs, FIIs, FI-Infras, FI-Agros e FIPs listados
  - Dividendos de FI-Infras e FI-Agros
  - Clearing (diversas informações)


## Links úteis

### FundosNet

- [Fundos (FIP, FIDC, FII etc.)](https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM)
- [CRA/CRI](https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosCertificadosCVM)
- [Manual do sistema](https://www.b3.com.br/data/files/CD/E1/F3/6B/D0CA2810F9BC5928AC094EA8/Manual%20do%20Sistema%20FundosNet%20-%2008.2022-a.pdf)

### B3

- [CRAs listados](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-fixa/cra/cras-listados/)
- [CRIs listados](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-fixa/cri/cris-listados/)
- [Cotações (2)](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/cotacoes/)
- [Cotações renda fixa](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/renda-fixa/)
- [Cotações](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/)
- [Código ISIN](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/codigo-isin/pesquisa/)
- [Dados públicos de produtos listados (bolsa e balcão)](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/)
- [ETFs listados](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/etf/renda-fixa/etfs-listados/)
- [FIDC histórico fatos relevantes balcão](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/fundos-de-investimentos/fidc/historico-fatos-relevantes-balcao/)
- [FIIs listados](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/fundos-de-investimentos/fii/fiis-listados/)
- [Formador de mercado renda variável](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/formador-de-mercado/renda-variavel/)
- [Histórico por pregão](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/pesquisa-por-pregao/)
- [Ofertas públicas em andamento](https://www.b3.com.br/pt_br/produtos-e-servicos/solucoes-para-emissores/ofertas-publicas/ofertas-em-andamento/empresas/publicacao-de-ofertas-publicas/)
- [Ofertas públicas encerradas](https://www.b3.com.br/pt_br/produtos-e-servicos/solucoes-para-emissores/ofertas-publicas/ofertas-encerradas/)
- [Plantão de notícias](https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Index?agencia=18&SociedadeEmissora=LAVF)
- [Debêntures](https://www.debenture.com.br/exploreosnd/consultaadados/emissoesdedebentures/puhistorico_r.asp)
- [Instrumentos listados](https://arquivos.b3.com.br/tabelas/InstrumentsConsolidated/2024-06-24?lang=pt)

### CETIP

- [Dados](http://estatisticas.cetip.com.br/astec/series_v05/paginas/lum_web_v04_10_03_consulta.asp)
- [Séries históricas](http://estatisticas.cetip.com.br/astec/series_v05/paginas/web_v05_series_introducao.asp?str_Modulo=Ativo&int_Idioma=1&int_Titulo=6&int_NivelBD=2%3E)

### Anbima

- [Debêntures](http://www.debentures.com.br/)


### Outras bibliotecas e projetos

Aqui listamos outras bibliotecas concorrentes e/ou que complementam os dados e funcionalidades disponíveis na
`mercados` e que podem ser úteis em análises.

#### Captura de dados

Existem diversas bibliotecas Python que capturam dados do mercado financeiro brasileiro. Alguns projetos estão
abandonados, já outros não são aderentes ao objetivo da `mercados`, mas talvez possam ser úteis em casos específicos:

- [`brFinance`](https://github.com/eudesrodrigo/brFinance)
- [`pycvm`](https://github.com/glourencoffee/pycvm/), [`pybov`](https://github.com/glourencoffee/pybov/) e
  [`pyibr`](https://github.com/glourencoffee/pyibr/)
- [`FinLogic`](https://github.com/crdcj/FinLogic) e [`PYield`](https://github.com/crdcj/PYield)
- [`stpstone`](https://github.com/guilhermegor/stpstone)
- [`cvmpy`](https://github.com/drsansao/cvmpy)
- [`py_financas`](https://github.com/jfrfonseca/py_financas)
- [`cvm-sqlite`](https://github.com/eduresser/cvm-sqlite)
- [`getDataCVM`](https://github.com/mandicneves/getDataCVM)
- [`pydemonstrativos`](https://github.com/andremsilveira/pydemonstrativos)
- [`fundosbr`](https://github.com/thobiast/fundosbr)
- [`fundspy`](https://github.com/joaopm33/fundspy)
- [`anbima_calendar`](https://github.com/izidorome/anbima_calendar)
- [`pyettj`](https://github.com/rafa-rod/pyettj), [`tesouro_direto_br`](https://github.com/rafa-rod/tesouro_direto_br)
  e [`comparar_fundos_br`](https://github.com/rafa-rod/comparar_fundos_br)
- [`tradingcomdados`](https://pypi.org/project/tradingcomdados/) (sem repositório Git?)

#### Análise de dados

- [`magicformulabr`](https://github.com/thobiast/magicformulabr)
- [`stocks-52week-rank`](https://github.com/thobiast/stocks-52week-rank)
- [`pytrendseries`](https://github.com/rafa-rod/pytrendseries)
- [`ta-lib`](https://ta-lib.org/)
- [`quantstats`](https://github.com/ranaroussi/quantstats)
- [`backtesting.py`](https://kernc.github.io/backtesting.py/)
- [`VectorBT`](https://vectorbt.dev/)

#### APIs

- [Dados de Mercado](https://www.dadosdemercado.com.br/api/docs)
- [MFinance](https://mfinance.com.br/swagger/index.html) ([repositórios no Github](https://github.com/mfinancecombr/))
- [brapi.dev](https://brapi.dev/)
