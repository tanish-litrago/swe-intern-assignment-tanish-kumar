"""python extract.py <pdf> [<pdf> ...]  ->  outputs/<pdf name>.json (schema-checked)."""
import json
import sys
from pathlib import Path

import pdfplumber
from jsonschema import validate

from kessler.detect import detect
from kessler.helpers import UnknownLayout, write_json

SCHEMA = json.loads((Path(__file__).parent / "data" / "output_schema.json").read_text(encoding="utf-8"))


def extract(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        data = detect(pdf).parse(pdf)
    validate(data, SCHEMA)  # trust boundary: never write output that breaks the contract
    return data


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    status = 0
    for p in argv:
        try:
            out = Path("outputs") / (Path(p).stem + ".json")
            write_json(extract(p), out)
            print(f"{p} -> {out}")
        except UnknownLayout as e:
            print(f"{p}: UNKNOWN LAYOUT: {e}", file=sys.stderr)
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
