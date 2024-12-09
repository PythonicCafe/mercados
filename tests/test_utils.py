from datetime import date
from decimal import Decimal
from textwrap import dedent

from mercados.utils import dicts_to_str

data = [
    {"data": date(2024, 11, 2)},
    {"valor": 0.123},
    {"data": date(2024, 11, 4), "valor": 0.040168},
    {"data": "2024-11-05", "valor": Decimal("0.040168")},
]


def test_dicts_to_str_csv():
    esperado = dedent(
        """
        data,valor
        2024-11-02,
        ,0.123
        2024-11-04,0.040168
        2024-11-05,0.040168
    """
    )
    resultado = dicts_to_str(data, "csv")
    # Chamar .splitlines evita \r\n vs \n
    assert resultado.strip().splitlines() == esperado.strip().splitlines()


def test_dicts_to_str_tsv():
    esperado = dedent(
        """
        data\tvalor
        2024-11-02\t
        \t0.123
        2024-11-04\t0.040168
        2024-11-05\t0.040168
    """
    )
    resultado = dicts_to_str(data, "tsv")
    # Chamar .splitlines evita \r\n vs \n
    assert resultado.strip().splitlines() == esperado.strip().splitlines()


def test_dicts_to_str_txt():
    esperado = dedent(
        """
        +------------+----------+
        |       data |    valor |
        +------------+----------+
        | 2024-11-02 |          |
        |            |    0.123 |
        | 2024-11-04 | 0.040168 |
        | 2024-11-05 | 0.040168 |
        +------------+----------+
    """
    )
    resultado = dicts_to_str(data, "txt")
    assert resultado.strip() == esperado.strip()


def test_dicts_to_str_md():
    esperado = dedent(
        """
        |       data |    valor |
        | ---------- | -------- |
        | 2024-11-02 |          |
        |            |    0.123 |
        | 2024-11-04 | 0.040168 |
        | 2024-11-05 | 0.040168 |
    """
    )
    resultado = dicts_to_str(data, "md")
    assert resultado.strip() == esperado.strip()
