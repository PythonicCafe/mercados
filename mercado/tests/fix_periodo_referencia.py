import csv

from rows.utils import open_compressed
from tqdm import tqdm

from mercado.utils import fix_periodo_referencia, parse_date


def not_yet_a_test():
    fobj = open_compressed("rendimentos.csv.gz")
    data = set()
    for row in tqdm(csv.DictReader(fobj)):
        data.add(
            (
                row["periodo_referencia"],
                int(row["ano"]) if row["ano"] else parse_date("iso-date", row["data_base"]).year,
            )
        )

    c1, c2 = 0, 0
    for value, year in data:
        r = fix_periodo_referencia(value, year)
        if r is None:
            c1 += 1
            print(value, r)
        else:
            c2 += 1
    print(c1, c2, c2 / (c1 + c2))
