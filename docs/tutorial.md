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


## FundosNET

No [FundosNET](https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM) são publicados documentos estruturados (em XML) e não estruturados sobre fundos.
A biblioteca `mercados` consegue extrair o XML de alguns desses documentos, retornando um objeto Python com os valores
já convertidos para tipos nativos (`str`, `int`, `datetime.date`, `decimal.Decimal` etc.).

### Exemplo: Baixar e Extrair Informes Diários de ETFs

```python
import base64
import datetime
import requests
from mercados.document import InformeDiarioFundo
from mercados.fundosnet import FundosNet
from mercados.utils import format_dataclass

data_inicial = datetime.date(2025, 7, 1)
data_final = datetime.date(2025, 7, 11)
fnet = FundosNet()
session = requests.Session()

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
    response = session.get(doc.url)
    xmls[doc_id] = base64.b64decode(response.content)  # Sim, o contéudo é retornado em base64 :|
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
