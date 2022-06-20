import datetime

from rows.utils import CsvLazyDictWriter
from tqdm import tqdm

from mercado.fundosnet import FundosNet


fnet = FundosNet()

start_date = datetime.date(2016, 1, 1)
end_date = datetime.date.today()
writer = CsvLazyDictWriter("data/rendimentos.csv")
result = fnet.search(
    category="Aviso aos Cotistas - Estruturado",
    type_="Rendimentos e Amortizações",
    start_date=start_date,
    end_date=end_date,
)
for row in tqdm(result):
    writer.writerow(row)
writer.close()

writer = CsvLazyDictWriter("data/informe_mensal.csv")
result = fnet.search(
    category="Informes Periódicos",
    type_="Informe Mensal Estruturado",
    start_date=start_date,
    end_date=end_date,
)
for row in tqdm(result):
    writer.writerow(row)
writer.close()
