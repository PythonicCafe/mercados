import csv
import datetime
import decimal
import io
import re
import socket
import subprocess
from functools import lru_cache
from pathlib import Path
from unicodedata import normalize

import requests
import requests.packages.urllib3.util.connection as urllib3_connection
from requests.adapters import HTTPAdapter, Retry

urllib3_connection.allowed_gai_family = lambda: socket.AF_INET  # Force requests to use IPv4
MONTHS = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()
MONTHS_3 = [item[:3] for item in MONTHS]
REGEXP_CAMELCASE_1 = re.compile("(.)([A-Z][a-z]+)")
REGEXP_CAMELCASE_2 = re.compile("([a-z0-9])([A-Z])")
REGEXP_SPACES = re.compile(r"\s{2,}", flags=re.MULTILINE)
REGEXP_CNPJ_SEPARATORS = re.compile("[./ -]+")
REGEXP_NUMERIC = re.compile(r"^[+-]? ?[0-9]+(\.[0-9]+)?$")
REGEXP_MONTH_YEAR = re.compile("^([0-9]{1,2})-([0-9]{2,4})$")
REGEXP_DATE_RANGE = re.compile("^(?:de )?([0-9]{2}/[0-9]{2}/[0-9]{4}) ?[aà–-] ?([0-9]{2}/[0-9]{2}/[0-9]{4})$")
REGEXP_ALPHA_MONTH_YEAR = re.compile("^([^0-9]+)[ /-]([0-9]{4})$")
REGEXP_YEAR_PART = re.compile(
    "^(1º|2º|3º|4º|1°|2°|3°|4°|1|2|3|4|primeiro|segundo|terceiro) (trimestre|semestre)( [0-9]{4})?$"
)
REGEXP_SEPARATOR = re.compile("(_+)")
REGEXP_WORD_BOUNDARY = re.compile(r"(\w\b)")
REGEXP_ATTACHMENT_FILENAME = re.compile("""^attachment; filename=['"]?(.*?)["']?$""")
BRT = datetime.timezone(-datetime.timedelta(hours=3))


@lru_cache(maxsize=1024)
def camel_to_snake(value):
    """
    >>> camel_to_snake("CamelToSnakeCase")
    'camel_to_snake_case'
    >>> camel_to_snake("HTTPRequest")
    'http_request'
    """
    value = str(value or "").strip()
    if not value:
        return ""
    # Adapted from <https://stackoverflow.com/a/1176023/1299446>
    return slug(REGEXP_CAMELCASE_2.sub(r"\1_\2", REGEXP_CAMELCASE_1.sub(r"\1_\2", value)))


def day_range(start, stop):
    """
    >>> list(day_range(datetime.date(2020, 1, 1), datetime.date(2020, 1, 3)))
    [datetime.date(2020, 1, 1), datetime.date(2020, 1, 2)]
    >>> len(list(day_range(datetime.date(2021, 1, 1), datetime.date(2021, 3, 30))))  # 31 + 28 + 29
    88
    """
    if start > stop:
        raise ValueError("`start` cannot be greater than `stop`")

    current = start
    one_day = datetime.timedelta(days=1)
    while current < stop:
        yield current
        current += one_day


def dicts_to_str(data: list[dict], fmt: str):
    """Convert a list of dictionaries to a string representation in a specific format.

    Values are not expected to have new-line (\n) and if the markdown format is used, it won't escape special chars,
    like `|`, `*` etc.

    :param data: list of dicionaries with the data. The dictionaries don't need to have the same keys (a set of all of
    them is used to create the table header)
    :param fmt: one of: markdown (or md), csv, tsv or txt
    """
    assert fmt in ("markdown", "md", "csv", "tsv", "txt")
    if not data:
        return ""
    header = []
    for row in data:
        for key in row.keys():
            if key not in header:
                header.append(key)
    if fmt in ("csv", "tsv"):
        delimiter = "\t" if fmt == "tsv" else ","
        with io.StringIO() as fobj:
            writer = csv.DictWriter(fobj, fieldnames=header, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
            fobj.seek(0)
            return fobj.read()
    elif fmt in ("markdown", "md", "txt"):
        # TODO: won't work if `\n` exists in a value
        # TODO: for markdown, needs to replace "|" with "&#124;" in values
        # TODO: escape markdown chars
        max_length = [len(value) for value in header]

        def values_as_str(values, separator="|", space=" "):
            return (
                f"{separator}{space}"
                + f"{space}{separator}{space}".join(
                    value.rjust(max_length[index]) for index, value in enumerate(values)
                )
                + f"{space}{separator}"
            )

        values = []
        for row in data:
            row_values = [str(row.get(key) or "") for key in header]
            for index, value in enumerate(row_values):
                if len(value) > max_length[index]:
                    max_length[index] = len(value)
            values.append(row_values)
        if fmt == "txt":
            separator_line = values_as_str(
                ["-" * max_length[index] for index in range(len(header))],
                separator="+",
                space="-",
            )
            header_line = values_as_str(header, separator="|", space=" ")
            values_lines = [values_as_str(row_values, separator="|", space=" ") for row_values in values]
            lines = [separator_line, header_line, separator_line] + values_lines + [separator_line]
        elif fmt in ("markdown", "md"):
            values = [header, ["-" * max_length[index] for index, _ in enumerate(header)]] + values
            lines = [values_as_str(row_values, separator="|", space=" ") for row_values in values]
        return "\n".join(lines)


def get_pdf_text(file_contents):
    command = ["pdftotext", "-layout", "-nopgbrk", "-enc", "UTF-8", "-", "-"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout_data, stderr_data = process.communicate(input=file_contents)
    text = stdout_data.decode("utf-8").replace("\x00", "").strip()
    return text


def slug(text, separator="_", permitted_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"):
    """Generate a slug for the `text`.

    >>> slug(' ÁLVARO  justen% ')
    'alvaro_justen'
    >>> slug(' ÁLVARO  justen% ', separator='-')
    'alvaro-justen'
    """

    text = str(text or "")

    # Strip non-ASCII characters
    # Example: u' ÁLVARO  justen% ' -> ' ALVARO  justen% '
    text = normalize("NFKD", text.strip()).encode("ascii", "ignore").decode("ascii")

    # Replace word boundaries with separator
    text = REGEXP_WORD_BOUNDARY.sub("\\1" + re.escape(separator), text)

    # Remove non-permitted characters and put everything to lowercase
    # Example: u'_ALVARO__justen%_' -> u'_alvaro__justen_'
    allowed_chars = set(list(permitted_chars) + [separator])
    text = "".join(char for char in text if char in allowed_chars).lower()

    # Remove double occurrencies of separator
    # Example: u'_alvaro__justen_' -> u'_alvaro_justen_'
    text = (REGEXP_SEPARATOR if separator == "_" else re.compile("(" + re.escape(separator) + "+)")).sub(
        separator, text
    )

    # Strip separators
    # Example: u'_alvaro_justen_' -> u'alvaro_justen'
    return text.strip(separator)


def create_session():
    import urllib3  # noqa

    urllib3.disable_warnings()
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=7, backoff_factor=0.1))
    session.headers["User-Agent"] = "Mozilla/5.0 mercados/python"
    session.headers["Accept"] = (
        "application/json,text/html,application/xhtml+xml,application/xml,application/pdf,text/csv,application/zip,application/x-zip-compressed"
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@lru_cache(maxsize=20)
def parse_bool(value):
    return {
        "t": True,
        "true": True,
        "s": True,
        "sim": True,
        "f": False,
        "false": False,
        "n": False,
        "nao": False,
        "não": False,
        "": None,
    }[str(value or "").lower().strip()]


def parse_br_decimal(value):
    value = str(value or "").strip()
    if not value:
        return None
    return decimal.Decimal(value.replace(",", "."))


def parse_date(fmt, value, full=False):
    value = str(value or "").strip()
    if not value or value == "0001-01-01":
        return None
    if fmt == "1":
        value = f"01/01/{value}"
        fmt = "%d/%m/%Y"
        obj_type = "date"
    elif fmt == "2":
        value = f"01/{value}"
        fmt = "%d/%m/%Y"
        obj_type = "date"
    elif fmt in ("3", "br-date"):
        fmt = "%d/%m/%Y"
        obj_type = "date"
    elif fmt == "4":
        fmt = "%d/%m/%Y %H:%M"
        obj_type = "datetime"
    elif fmt == "iso-datetime-tz":
        if "T" in value:
            fmt = "%Y-%m-%dT%H:%M:%S%z"
        else:
            fmt = "%Y-%m-%d %H:%M:%S%z"
        obj_type = "datetime"
    elif fmt == "iso-date":
        fmt = "%Y-%m-%d"
        obj_type = "date"
    obj = datetime.datetime.strptime(value, fmt).replace(tzinfo=BRT)
    if full or obj_type == "datetime":
        return obj
    elif obj_type == "date":
        return obj.date()


def parse_iso_date(value):
    return parse_date("iso-date", value)


def parse_datetime_force_timezone(value):
    return datetime.datetime.fromisoformat(value).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=-3)))


def clean_string(value):
    if value is None:
        return value
    return value.strip()


def parse_br_date(value):
    if not value or value == "0001-01-01":
        return None
    return parse_date("br-date", value)


@lru_cache(maxsize=120)
def get_month(value):
    value = {
        "janeeiro": "janeiro",
        "jneiro": "janeiro",
        "fevreiro": "fevereiro",
        "fvereiro": "fevereiro",
        "fevareiro": "fevereiro",
        "favereiro": "fevereiro",
        "feveiro": "fevereiro",
        "fevereriro": "fevereiro",
        "marco": "março",
        "abrik": "abril",
        "outbro": "outubro",
        "outubto": "outubro",
        "dezemrbo": "dezembro",
    }.get(value, value)
    if value in MONTHS:
        return MONTHS.index(value) + 1
    elif value in MONTHS_3:
        return MONTHS_3.index(value) + 1
    return value


@lru_cache(maxsize=120)
def last_day_of_month(year, month):
    dt = datetime.date(year, month, 20) + datetime.timedelta(days=15)
    return datetime.date(year, month, 20 + 15 - dt.day)


@lru_cache(maxsize=120)
def fix_periodo_referencia(value, original_year):
    # TODO: apply this function to raw values and save result
    value = (
        value.replace("antecip. da dist. de ", "")
        .replace(" à ", " a ")
        .replace(" - liq oferta", "")
        .replace(" - ganho de capital", "")
        .replace("extraordinario", "")
        .replace("extraordinário", "")
        .replace("extraordinaria", "")
        .replace("extraordinária", "")
        .replace(" - extra", "")
        .replace(" - complementar", "")
        .replace("complementar ", "")
        .replace(" - direito de preferencia", "")
        .replace(" até ", " a ")
    ).strip()

    if value.isdigit() and 1 <= int(value) <= 12:
        value = int(value)
        return (
            datetime.date(original_year, value, 1),
            last_day_of_month(original_year, value),
        )

    elif get_month(value) != value:
        value = get_month(value)
        return (
            datetime.date(original_year, value, 1),
            last_day_of_month(original_year, value),
        )

    elif REGEXP_MONTH_YEAR.match(value):
        month, year = [int(item) for item in REGEXP_MONTH_YEAR.findall(value)[0]]
        if year < 100:
            year = 2000 + year
        return (datetime.date(year, month, 1), last_day_of_month(year, month))

    elif REGEXP_DATE_RANGE.match(value):
        first, last = REGEXP_DATE_RANGE.findall(value)[0]
        return (
            parse_date("br-date", first),
            parse_date("br-date", last),
        )

    elif REGEXP_ALPHA_MONTH_YEAR.match(value):
        month, year = REGEXP_ALPHA_MONTH_YEAR.findall(value)[0]
        month = get_month(month)
        if isinstance(month, int):
            return (
                datetime.date(int(year), month, 1),
                last_day_of_month(int(year), month),
            )
    elif REGEXP_YEAR_PART.match(value):
        number, length, year = REGEXP_YEAR_PART.findall(value)[0]
        year = int(year) if year else original_year
        number = {
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "primeiro": 1,
            "segundo": 2,
            "terceiro": 3,
            "quarto": 4,
        }[number.replace("º", "").replace("°", "")]
        if (number, length) == (1, "semestre"):
            return (datetime.date(year, 1, 1), datetime.date(year, 6, 30))
        elif (number, length) == (2, "semestre"):
            return (datetime.date(year, 7, 1), datetime.date(year, 12, 31))
        elif (number, length) == (1, "trimestre"):
            return (datetime.date(year, 1, 1), datetime.date(year, 3, 31))
        elif (number, length) == (2, "trimestre"):
            return (datetime.date(year, 4, 1), datetime.date(year, 6, 30))
        elif (number, length) == (3, "trimestre"):
            return (datetime.date(year, 7, 1), datetime.date(year, 9, 30))
        elif (number, length) == (4, "trimestre"):
            return (datetime.date(year, 10, 1), datetime.date(year, 12, 31))

    elif (" a " in value or " e " in value) and "/" not in value:
        if " a " in value:
            first, last = value.split(" a ")
        elif " e " in value:
            first, last = value.split(" e ")
        first, last = get_month(first), get_month(last)
        if isinstance(first, int) and isinstance(last, int):
            return (
                datetime.date(original_year, first, 1),
                last_day_of_month(original_year, last),
            )

    elif "/" in value:
        parts = value.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            month, year = [item.strip().lower() for item in parts]
            if len(year) == 2:
                year = f"20{year}"
            elif year == "20225":
                year = "2022"
            year = int(year)
            months = []
            if " a " in month or " e " in month:
                if " a " in month:
                    min_max = [get_month(x) for x in month.split(" a ")]
                    months = list(range(min(min_max), max(min_max) + 1))
                elif " e " in month:
                    months = [get_month(x) for x in month.split(" e ")]
            elif not month.isdigit():
                months = [get_month(month), get_month(month)]
            else:
                months = [int(month), int(month)]
            start = datetime.date(year, months[0], 1)
            end = last_day_of_month(year, months[1])
            return start, end


def parse_int(value):
    return int(value) if value is not None else None


def clean_xml_dict(d):
    """
    >>> clean_xml_dict({"a": {"@xsi:nil": "true"}})
    {'a': None}

    >>> clean_xml_dict({"a": {"@xsi:nil": "true"}, "b": {"c": {"d": 1, "e": {"@xsi:nil": "true"}}}})
    {'a': None, 'b': {'c': {'d': 1, 'e': None}}}
    """
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            if value.get("@xsi:nil") == "true":
                value = None
            else:
                value = clean_xml_dict(value)
        result[key] = value
    return result


def download_files(urls: list[str], filenames: list[Path], quiet=False):
    session = create_session()
    for url, filename in zip(urls, filenames):
        filename = Path(filename)
        filename.mkdir(parents=True, exist_ok=True)
        response = session.get(url)
        with filename.open(mode="wb") as fobj:
            fobj.write(response.content)
