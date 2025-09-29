from datetime import date
from decimal import Decimal
from io import StringIO
from textwrap import dedent

from mercados.utils import dicts_to_file

data = [
    {"data": date(2024, 11, 2)},
    {"valor": 0.123},
    {"data": date(2024, 11, 4), "valor": 0.040168},
    {"data": "2024-11-05", "valor": Decimal("0.040168")},
]


def assert_dicts_to_file(data, fmt, esperado):
    with StringIO() as fobj:
        dicts_to_file(data, fmt, fobj)
        fobj.seek(0)
        resultado = fobj.read()

    # Chamar .splitlines evita \r\n vs \n
    assert resultado.strip().splitlines() == esperado.strip().splitlines()


def test_dicts_to_file_csv():
    esperado = dedent(
        """
        data,valor
        2024-11-02,
        ,0.123
        2024-11-04,0.040168
        2024-11-05,0.040168
    """
    )
    assert_dicts_to_file(data, "csv", esperado)


def test_dicts_to_file_tsv():
    esperado = dedent(
        """
        data\tvalor
        2024-11-02\t
        \t0.123
        2024-11-04\t0.040168
        2024-11-05\t0.040168
    """
    )
    assert_dicts_to_file(data, "tsv", esperado)


def test_dicts_to_file_txt():
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
    assert_dicts_to_file(data, "txt", esperado)


def test_dicts_to_file_md():
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
    assert_dicts_to_file(data, "md", esperado)
    assert_dicts_to_file(data, "markdown", esperado)
