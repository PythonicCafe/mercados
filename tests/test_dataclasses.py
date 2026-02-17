import datetime
import random
import string
import types
from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import Union, get_args, get_origin

import pytest

from mercados import b3, bcb, cvm, fundosnet, ibge


def rand_str(n):
    return "".join(random.choice(string.ascii_letters + string.digits + " ") for _ in range(random.randint(0, n)))


def rand_int(minimo=0, maximo=1000):
    return random.randint(minimo, maximo)


def rand_float(maximo):
    return random.random() * maximo


def rand_decimal(maximo):
    return Decimal(str(rand_float(maximo)))


def rand_date(ano_minimo=1990, ano_maximo=2025):
    return datetime.date(random.randint(ano_minimo, ano_maximo), random.randint(1, 12), random.randint(1, 28))


def rand_datetime(ano_minimo=1990, ano_maximo=2025):
    return datetime.datetime(
        random.randint(ano_minimo, ano_maximo),
        random.randint(1, 12),
        random.randint(1, 28),
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
        random.randint(0, 1000000) if random.random() > 0.9 else 0,
    )


def _unwrap_optional(field_type: type) -> tuple[type, bool]:
    origin = get_origin(field_type)
    if origin is Union or isinstance(field_type, types.UnionType):
        args = get_args(field_type)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return non_none[0], True

    return field_type, False


def _cria_valor_falso(field_type: type):
    if field_type is bool:
        return random.random() > 0.5
    elif field_type is str:
        return rand_str(100)
    elif field_type is int:
        return rand_int(minimo=0, maximo=1000)
    elif field_type is float:
        return rand_float(maximo=10000)
    elif field_type is Decimal:
        return rand_decimal(maximo=100000)
    elif field_type is datetime.date:
        return rand_date()
    elif field_type is datetime.datetime:
        return rand_datetime()
    elif get_origin(field_type) is list:
        arg = get_args(field_type)[0]
        return [_cria_valor_falso(arg) for _ in range(random.randint(1, 3))]
    elif is_dataclass(field_type):
        return cria_objeto_com_dados_falsos(field_type)
    else:
        raise TypeError(f"Tipo não suportado: {field_type!r}")


def cria_objeto_com_dados_falsos(DataClass):
    row = {}
    for field in fields(DataClass):
        field_type, is_optional = _unwrap_optional(field.type)
        row[field.name] = _cria_valor_falso(field_type)
        if is_optional and random.random() > 0.5:
            row[field.name] = None
    return DataClass(**row)


def lista_dataclasses(modulo):
    resultado = []
    for atributo in dir(modulo):
        obj = getattr(modulo, atributo)
        if is_dataclass(obj):
            resultado.append(obj)
    return resultado


@pytest.mark.parametrize(
    "modulo, DataClass",
    [(modulo, DataClass) for modulo in (b3, bcb, cvm, fundosnet, ibge) for DataClass in lista_dataclasses(modulo)],
)
def test_dataclasses_serialize(modulo, DataClass):
    obj = cria_objeto_com_dados_falsos(DataClass)
    row = obj.serialize()
    dataclass_field_names = [field.name for field in fields(DataClass)]
    if modulo is cvm and DataClass.__name__ == "DocumentoEmpresa":
        dataclass_field_names = ["uuid"] + dataclass_field_names
    assert list(row.keys()) == dataclass_field_names, f"{modulo.__name__}.{DataClass.__name__}"
