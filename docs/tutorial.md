# Tutorial

## Códigos e Licença

Todo o código mostrado nesse tutorial também está disponível na pasta
[`exemplos`](https://github.com/PythonicCafe/mercados/blob/develop/exemplos), para facilitar a execução.

O [código da biblitoeca em si está sob a licença
LGPLv3](https://github.com/PythonicCafe/mercados/tree/develop?tab=readme-ov-file#licen%C3%A7a), mas todos os códigos
disponíveis nesse tutorial e na pasta `exemplos` estão disponíveis sob a [licença
CC0](https://creativecommons.org/public-domain/cc0/) (equivalente ao domínio público).

## Introdução

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


## IBGE

Dados que podem ser baixados do [IBGE](https://ibge.gov.br/):

- [Séries históricas de
  Índices](https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html?=&t=series-historicas)
  (IPCA, IPCA-15 e INPC)


### Exemplo: IPCA dos últimos 12 meses

O módulo `ibge` consegue baixar as séries históricas do IPCA, IPCA-15 e INPC. Os valores estão disponíveis desde
dezembro de 1993, quando o "número série" tinha o valor `100.00`. O valor é corrigido pelos índices mensalmente.

```python
import datetime

from mercados.ibge import IBGE


ibge = IBGE()
indice = "IPCA"  # Teste com "IPCA-15" e "INPC"
hoje = datetime.datetime.now().date()
ultimo = None
for taxa in ibge.historico(indice):
    if (hoje - taxa.data).days > 365:
        continue
    atual = taxa.valor
    if ultimo is None:
        variacao_str = "N/A"
    else:
        variacao = 100 * (atual / ultimo - 1)
        variacao_str = f"{variacao:.2f}%"
    print(f"{indice} em {taxa.data}: {atual:.2f} (variação: {variacao_str})")
    ultimo = taxa.valor
```

O retorno será algo como:

```
IPCA em 2024-10-15: 7036.33 (variação: N/A)
IPCA em 2024-11-15: 7063.77 (variação: 0.39%)
IPCA em 2024-12-15: 7100.50 (variação: 0.52%)
IPCA em 2025-01-15: 7111.86 (variação: 0.16%)
IPCA em 2025-02-15: 7205.03 (variação: 1.31%)
IPCA em 2025-03-15: 7245.38 (variação: 0.56%)
IPCA em 2025-04-15: 7276.54 (variação: 0.43%)
IPCA em 2025-05-15: 7295.46 (variação: 0.26%)
IPCA em 2025-06-15: 7312.97 (variação: 0.24%)
IPCA em 2025-07-15: 7331.98 (variação: 0.26%)
IPCA em 2025-08-15: 7323.91 (variação: -0.11%)
```

## Banco Central

Dados que podem ser baixados do Banco Central do Brasil:
- Sistema NovoSelic: Ajuste de valor pela Selic por dia ou mês
- [Sistema Gerenciador de Séries
  Temporais](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries), que
  possui milhares de séries disponíveis, incluindo Selic e CDI. O sistema também consolida séries de outros órgãos,
  como IPCA (do IBGE), IGP-M (da FGV), dentre outros.

### Exemplo: CDI dos Últimos 7 Dias

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
- [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): lista de companhias abertas
- [RAD](https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx): busca por documentos publicados
- [Portal de Dados Abertos](https://dados.cvm.gov.br/): informe diário de fundos de investimento


### Exemplo: Cota Histórica de Fundos de Investimento

Podemos usar os dados de informes diários de fundos de investimento e montar uma planilha com o histórico dos informes
diários de um fundo específico. No informe constam dados como o valor da cota, valores de captação e resgate,
quantidade de cotistas, patrimônio líquido e valor da carteira.


```python
cnpj_fundo = "18302338000163"  # Ártica Long Term FIA
csv_filename = Path("data") / "cota-artica-long-term.csv"
csv_filename.parent.mkdir(exist_ok=True, parents=True)
inicio = datetime.date(2019, 9, 1)  # Mês em que migrou de clube para fundo (dados de clube não ficam disponíveis)
fim = datetime.datetime.now().date()
atual = inicio
print(f"Salvando dados em {csv_filename}")
cvm = CVM()
with csv_filename.open(mode="w") as fobj:
    writer = None
    while atual <= fim:
        print(f"Coletando para o mês {atual.month:02d}/{atual.year}")
        for informe in cvm.informe_diario_fundo(atual):
            # O método `informe_diario_fundo` ignora o campo "dia" da data passada e retorna todos os informes diários
            # de todos os fundos para o ano/mês
            if informe.fundo_cnpj == cnpj_fundo:
                row = informe.serialize()  # Transforma em dicionário
                if writer is None:
                    writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
        atual = (atual.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)  # Próximo mês
```


## Secretaria do Tesouro Nacional

Dados que podem ser baixados da Secretaria do Tesouro Nacional (STN):

- Histórico de preços de títulos


### Exemplo: Preços de títulos na última semana

A partir da planilha que tem os preços históricos para todos os títulos do Tesouro, vamos pegar apenas os valores dos
últimos 7 dias:

```python
import datetime

from mercados.stn import Tesouro

tesouro = Tesouro()
hoje = datetime.datetime.now().date()
semana_passada = hoje - datetime.timedelta(days=7)
historico = []
for titulo in tesouro.historico_titulos():
    if semana_passada <= titulo.data <= hoje:
        print(f"{titulo.data}\t{titulo.nome} ({titulo.vencimento})\tR$ {titulo.preco:,}")
```

O retorno será algo como:

```
2025-10-23	Tesouro Renda+ Aposentadoria Extra (2084-12-15)	R$ 172.94
2025-10-23	Tesouro Renda+ Aposentadoria Extra (2079-12-15)	R$ 243.07
2025-10-23	Tesouro Renda+ Aposentadoria Extra (2074-12-15)	R$ 344.03
[..]
2025-10-17	Tesouro Prefixado (2026-01-01)	R$ 971.72
2025-10-17	Tesouro IPCA+ com Juros Semestrais (2026-08-15)	R$ 4,463.44
2025-10-17	Tesouro IPCA+ (2026-08-15)	R$ 4,208.51
```


## B3

Dados que podem ser baixados da B3:
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

### Exemplo: Preços da Negociação em Bolsa

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

### Exemplo: Últimas Cotações

No exemplo abaixo, pegamos as últimas cotações disponíveis para um determinado ativo. Os dados são sempre referentes ao
último pregão e com atraso de 15 minutos.

```python
from mercados.b3 import B3

b3 = B3()
for preco in b3.ultimas_cotacoes("POMO4"):
    print(f"Cotação de {preco.codigo_negociacao} em {preco.datahora}: {preco.valor}")
```

Deve retornar algo como:

```
Cotação de POMO4 em 2025-08-12 10:03:00-03:00: 8.95
Cotação de POMO4 em 2025-08-12 10:04:00-03:00: 8.93
[...]
Cotação de POMO4 em 2025-08-12 17:46:00-03:00: 8.97
Cotação de POMO4 em 2025-08-12 17:54:00-03:00: 8.93
```


### Exemplo: Valores dos Índices

No exemplo abaixo, pegamos os valores diários do Índice de Fundos de Investimentos Imobiliários (IFIX) de 2010 ao ano
atual e salvamos o resultado em um arquivo CSV.

```python
import csv
import datetime
from mercados.b3 import B3


indice_escolhido = "IFIX"
ano_inicial = 2010
ano_atual = datetime.datetime.now().year

b3 = B3()
print("Índices disponíveis:")
for indice in b3.indices:
    print(f"- {indice}")

with open(f"{indice_escolhido}.csv", mode="w") as fobj:
    writer = csv.DictWriter(fobj, fieldnames=["data", "valor"])
    writer.writeheader()
    for ano in range(ano_inicial, ano_atual + 1):
        print(f"Coletando dados do {indice_escolhido} para {ano}")
        for taxa in b3.valor_indice(indice_escolhido, ano):
            writer.writerow({"data": taxa.data, "valor": taxa.valor})
```

Deve retornar algo como:

```
Índices disponíveis:
- AGFS
- BDRX
- GPTW
[...]
Coletando dados do IFIX para 2023
Coletando dados do IFIX para 2024
Coletando dados do IFIX para 2025
```

O arquivo `IFIX.csv` será criado com todos os valores do IFIX desde 30/12/2010, quando seu valor inicial era `1000.00`.


### Exemplo: Aluguel de Ativos

No exemplo abaixo, pegamos os dados para aluguel do ativo XPML11 para os últimos 30 dias (os dados só ficam disponíveis
para esse período). Para termos um resultado com maior granularidade, coletamos os dados dia a dia, mas é possível
passar um período (data inicial e final diferentes) para evitar muitas requisições. Para cada dia e ativo é possível
que mais de um registro apareça, dado que podem existir valores distintos para o campo "mercado" ("Registro" ou "Neg.
Eletrônica D+1").

```python
import csv
import datetime

from mercados.b3 import B3

ativo = "XPML11"
csv_filename = f"b3-aluguel-{ativo}.csv"
b3 = B3()
data_final = datetime.datetime.now().date()  # Hoje
data_inicial = data_final - datetime.timedelta(days=30)  # 1 mês atrás
data = data_final
with open(csv_filename, mode="w") as fobj:
    writer = None
    print(f"Capturando dados de aluguel para {ativo}")
    while data >= data_inicial:
        dados = b3.clearing_emprestimos_registrados(data_inicial=data, data_final=data, codigo_negociacao=ativo)
        resultado = sorted(dados, key=lambda item: item.data, reverse=True)  # Ordena dados pela data (decrescente)
        if resultado:
            item = resultado[0]
            print(f"  {item}")
            row = item.serialize()  # Transforma `item` (que é uma dataclass) em um dicionário
            if writer is None:
                writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow(row)
        data -= datetime.timedelta(days=1)
```

O arquivo `b3-aluguel-XPML11.csv` deve ser criado e o programa mostrará na tela algo como:

```
Capturando dados de aluguel para XPML11
  EmprestimoAtivo(data=datetime.date(2025, 7, 25), codigo_negociacao='XPML11', codigo_isin='BRXPMLCTF000', nome='XP MALLS FDO INV IMOB FII RESP LIM', mercado='Registro', contratos=43, quantidade=9692, minima=0.0012, media_ponderada=0.0012, maxima=0.0012, valor=Decimal('978601.24'), taxa_doador=None, taxa_tomador=None)
  EmprestimoAtivo(data=datetime.date(2025, 7, 24), codigo_negociacao='XPML11', codigo_isin='BRXPMLCTF000', nome='XP MALLS FDO INV IMOB FII RESP LIM', mercado='Registro', contratos=147, quantidade=103759, minima=0.0012, media_ponderada=0.0012, maxima=0.0012, valor=Decimal('10454756.84'), taxa_doador=None, taxa_tomador=None)
  [...]
  EmprestimoAtivo(data=datetime.date(2025, 7, 1), codigo_negociacao='XPML11', codigo_isin='BRXPMLCTF000', nome='XP MALLS FDO INV IMOB FII RESP LIM', mercado='Registro', contratos=54, quantidade=34623, minima=0.0009, media_ponderada=0.0009, maxima=0.0015, valor=Decimal('3585211.65'), taxa_doador=None, taxa_tomador=None)
  EmprestimoAtivo(data=datetime.date(2025, 6, 30), codigo_negociacao='XPML11', codigo_isin='BRXPMLCTF000', nome='XP MALLS FDO INV IMOB FII RESP LIM', mercado='Registro', contratos=45, quantidade=125078, minima=0.0009, media_ponderada=0.0009, maxima=0.0009, valor=Decimal('12904297.26'), taxa_doador=None, taxa_tomador=None)
```


## FundosNET

No [FundosNET](https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM) são publicados documentos estruturados (em XML) e não estruturados sobre fundos.
A biblioteca `mercados` consegue extrair o XML de alguns desses documentos, retornando um objeto Python com os valores
já convertidos para tipos nativos (`str`, `int`, `datetime.date`, `decimal.Decimal` etc.).

### Exemplo: Baixar e Extrair Informes Diários de ETFs

```python
import datetime
from mercados.document import InformeDiarioFundo
from mercados.fundosnet import FundosNet
from mercados.utils import format_dataclass

data_inicial = datetime.date(2025, 7, 1)
data_final = datetime.date(2025, 7, 11)
fnet = FundosNet()

print("Buscando documentos no FundosNET e selecionando informes diários")
documentos = {}
for doc in fnet.search(start_date=data_inicial, end_date=data_final):
    if doc.tipo != "Informe Diário":
        continue
    documentos[doc.id] = doc
    if len(documentos) % 10 == 0:
        print(f"\r{len(documentos):5} encontrados", end="", flush=True)
print(f"\r{len(documentos):5} encontrados", flush=True)

print("Baixando XMLs dos informes selecionados")
xmls = {}
for doc_id, doc in documentos.items():
    xmls[doc_id] = fnet.baixa_xml(doc.url)
    if len(xmls) % 10 == 0:
        print(f"\r{len(xmls):5} baixados", end="", flush=True)
print(f"\r{len(xmls):5} baixados", flush=True)

for doc_id, xml in xmls.items():
    print(f"Extraindo informes do XML de {doc_id}:")
    informes = InformeDiarioFundo.from_xml(xml)
    for rank, informe in enumerate(informes, start=1):
        print(f"#{rank}: {format_dataclass(informe)}")
    print()
```


## B3 + FundosNET

Podemos combinar informações disponíveis na B3 para filtrar dados publicados no FundosNET.

### Exemplo: Cota de ETFs da B3

Vamos listar os ETFs da B3 e, a partir do CNPJ, coletaremos do FundosNET os informes diários publicados por esses ETFs
nos últimos 7 dias (que estejam ativos). A partir da URL de cada informe, baixaremos o XML, faremos a extração e
mostraremos o CNPJ, código de negociação, data e valor da cota:

```python
import datetime

from mercados.b3 import B3
from mercados.document import InformeDiarioFundo
from mercados.fundosnet import FundosNet

fim = datetime.datetime.now().date()
inicio = fim - datetime.timedelta(days=7)
b3 = B3()
fnet = FundosNet()
print("Baixando lista de ETFs da B3")
etfs = list(b3.etfs(detalhe=True))
print(f"Encontrados {len(etfs)} ETFs")
etfs.sort(key=lambda etf: etf.codigo_negociacao)
for etf in etfs:
    etf_cnpj = etf.cnpj
    for doc in fnet.search(cnpj=etf_cnpj, situacao="A", category="Informes Periódicos", type_="Informe Diário",
                           start_date=inicio, end_date=fim):
        xml = fnet.baixa_xml(doc.url)
        informes = InformeDiarioFundo.from_xml(xml)
        for informe in informes:
            if informe.fundo_cnpj != etf_cnpj:  # O XML pode conter informes de diversos fundos
                continue
            print(f"{etf_cnpj}\t{etf.codigo_negociacao}\t{informe.data_competencia}\t{informe.cota}")
```

O resultado será algo como:

```
Baixando lista de ETFs da B3
Encontrados 133 ETFs
38542889000101	ACWI11	2025-10-22	15.715211000000
38542889000101	ACWI11	2025-10-21	15.723275000000
38542889000101	ACWI11	2025-10-20	15.727208000000
[...]
42264597000121	YDRO11	2025-10-17	52.674210700000
42264597000121	YDRO11	2025-10-16	54.067090100000
42264597000121	YDRO11	2025-10-08	49.849949900000
```
