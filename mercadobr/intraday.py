import argparse
import csv
import datetime
import io
import zipfile

import requests
from tqdm import tqdm


def intraday_zip_url(date: datetime.date):
    date_str = date.strftime("%Y-%m-%d")
    url = f"https://arquivos.b3.com.br/rapinegocios/tickercsv/{date_str}"
    return url


def read_zip_file(filename):
    zf = zipfile.ZipFile(filename)
    assert len(zf.filelist) == 1, f"Expected intraday file {repr(filename)} to have only one file inside zip"
    filename = zf.filelist[0].filename
    assert "_NEGOCIOSAVISTA.txt" in filename, f"Wrong filename inside ZIP file: {repr(filename)}"
    fobj = io.TextIOWrapper(zf.open(zf.filelist[0].filename), encoding="iso-8859-1")
    reader = csv.DictReader(fobj, delimiter=";")
    # TODO: criar dataclass e converter valores em objetos Python
    yield from reader


def download_file(url, output_filename, chunk_size=256 * 1024):
    """Download and save the zip file"""

    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))
    with open(output_filename, "wb") as fobj:
        with tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024, desc="Downloading file") as progress:
            for chunk in response.iter_content(chunk_size):
                fobj.write(chunk)
                progress.update(len(chunk))


def parse_date(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and/or convert B3 intraday ZIP files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: download
    download_parser = subparsers.add_parser("download", help="Download intraday ZIP file from B3.")
    download_parser.add_argument("date", type=parse_date, help="Date in YYYY-MM-DD format for the file to download.")
    download_parser.add_argument("zip_filename", help="Output filename for the downloaded ZIP file.")

    # Subcommand: convert
    convert_parser = subparsers.add_parser("convert", help="Convert intraday ZIP file to CSV.")
    convert_parser.add_argument("--codigo-ativo", "-c", action="append", help="Filter by stock code.")
    convert_parser.add_argument("zip_filename", help="Input ZIP filename.")
    convert_parser.add_argument("csv_filename", help="Output CSV filename.")

    args = parser.parse_args()

    if args.command == "download":
        url = intraday_zip_url(args.date)
        download_file(url, args.zip_filename)

    elif args.command == "convert":
        zip_filename = args.zip_filename
        csv_filename = args.csv_filename
        codigo_ativo = set(args.codigo_ativo) if args.codigo_ativo else None

        with open(csv_filename, mode="w") as fobj:
            writer = None
            for row in tqdm(read_zip_file(zip_filename), desc="Converting file"):
                if writer is None:
                    writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                if codigo_ativo is None or row["CodigoInstrumento"] in codigo_ativo:
                    writer.writerow(row)
