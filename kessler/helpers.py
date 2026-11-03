"""Generic helpers: German numbers/dates, line grouping, column assignment, JSON output.
No supplier-specific logic lives here."""
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

MONTHS = {"januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7,
          "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}


class UnknownLayout(Exception):
    """Raised when no known layout parser matches the document."""


def parse_de_number(text):
    """'1.234,56' -> Decimal('1234.56'); trailing minus ('225,80-') means negative."""
    s = text.replace("€", "").replace("EUR", "").strip()
    neg = s.startswith("-") or s.endswith("-")
    s = s.strip("-").replace(".", "").replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"not a German number: {text!r}") from None
    return -d if neg else d


def parse_date(text):
    """'06.10.2026' or '19. Oktober 2026' -> date. Raises ValueError for impossible dates."""
    t = text.strip()
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
    if m:
        d, mo, y = map(int, m.groups())
        return date(y, mo, d)
    m = re.fullmatch(r"(\d{1,2})\.\s*([A-Za-zÄäÖöÜü]+)\s+(\d{4})", t)
    if not m or m.group(2).lower() not in MONTHS:
        raise ValueError(f"not a date: {text!r}")
    return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))


@dataclass
class Line:
    words: list

    @property
    def top(self):
        return self.words[0]["top"]

    @property
    def text(self):
        return " ".join(w["text"] for w in self.words)

    def text_in(self, xmin, xmax):
        """Text of the words whose left edge lies in [xmin, xmax) - one column of the page."""
        return " ".join(w["text"] for w in self.words if xmin <= w["x0"] < xmax)


def page_lines(page):
    # x_tolerance=1: the default (3) glues '14,60' and the PE column '100' into '14,60100'
    words = sorted(page.extract_words(x_tolerance=1), key=lambda w: (w["top"], w["x0"]))
    groups = []
    for w in words:
        if groups and w["top"] - groups[-1][-1]["top"] <= 2.5:
            groups[-1].append(w)
        else:
            groups.append([w])
    return [Line(sorted(g, key=lambda w: w["x0"])) for g in groups]


def assign_column(word, cols, tol=10):
    """cols: [(name, 'R'|'L', x)]. Right-aligned columns match on the word's right edge (x1),
    left-aligned ones on its left edge (x0): the last left column that starts at or before the word."""
    best = None
    for name, kind, x in cols:
        if kind == "R" and abs(word["x1"] - x) <= tol and (best is None or abs(word["x1"] - x) < best[0]):
            best = (abs(word["x1"] - x), name)
    if best:
        return best[1]
    left = [c for c in cols if c[1] == "L" and word["x0"] >= c[2] - 5]
    return max(left, key=lambda c: c[2])[0] if left else None


def table_rows(pdf, header_words, columns_from_header, stop_re):
    """Yield (cells, line_text) for every table line on every page. Cells: column name -> text.
    A page's table starts under the header line and ends at the first line matching stop_re."""
    for page in pdf.pages:
        lines = page_lines(page)
        hi = next((i for i, ln in enumerate(lines) if header_words <= {w["text"] for w in ln.words}), None)
        if hi is None:
            continue
        cols = columns_from_header(lines[hi])
        for ln in lines[hi + 1:]:
            if stop_re.match(ln.text):
                break
            cells = {}
            for w in ln.words:
                if w["text"] == "€":  # zero-width currency glyphs in the new layout
                    continue
                name = assign_column(w, cols)
                cells[name] = (cells.get(name, "") + " " + w["text"]).strip()
            yield cells, ln.text


def parse_address_block(lines):
    """['Rheinwerk Anlagenbau AG', 'Abt. X', 'Hafenstraße 88', '47119 Duisburg', ...] -> dict."""
    lines = [ln for ln in lines if not re.match(r"(Abt\.|z\. ?Hd\.|Attn|c/o)", ln)]
    pi = next(i for i, ln in enumerate(lines) if re.fullmatch(r"\d{5}\s+.+", ln))
    postal, city = lines[pi].split(None, 1)
    return {"name": lines[0], "street": lines[pi - 1], "postal_code": postal, "city": city}


def block_lines(lines, top_from, xmin, xmax, span=80):
    """Non-empty text of one page column for the lines within `span` points under top_from."""
    out = []
    for ln in lines:
        if top_from < ln.top <= top_from + span:
            t = ln.text_in(xmin, xmax)
            if t:
                out.append(t)
    return out


def _f(d):
    return None if d is None else float(d)


def build_document(*, doc_type, number, doc_date, service_date, due_date, supplier, buyer, order_reference,
                   delivery_note, referenced_invoice, items, net_by_rate, vat_by_rate, net_total, vat_total,
                   gross_total, cash_discount):
    """Assemble the output dict (Decimal/date -> JSON types) in schema order."""
    iso = lambda d: None if d is None else d.isoformat()
    return {
        "document_type": doc_type,
        "document_number": number,
        "document_date": iso(doc_date),
        "service_date": iso(service_date),
        "due_date": iso(due_date),
        "currency": "EUR",
        "supplier": supplier,
        "buyer": buyer,
        "order_reference": order_reference,
        "delivery_note_number": delivery_note,
        "referenced_invoice": referenced_invoice,
        "line_items": [{
            "position": it["position"], "article_number": it["article_number"],
            "description": it["description"], "quantity": _f(it["quantity"]), "unit": it["unit"],
            "unit_price": _f(it["unit_price"]), "price_unit": _f(it["price_unit"]),
            "discount_percent": _f(it["discount_percent"]), "line_total": _f(it["line_total"]),
            "vat_rate": it["vat_rate"],
        } for it in items],
        "totals": {
            "net_by_vat_rate": {str(r): _f(v) for r, v in net_by_rate.items()},
            "vat_by_vat_rate": {str(r): _f(v) for r, v in vat_by_rate.items()},
            "net_total": _f(net_total), "vat_total": _f(vat_total), "gross_total": _f(gross_total),
        },
        "cash_discount": None if cash_discount is None else
        {"percent": _f(cash_discount["percent"]), "until": iso(cash_discount["until"]),
         "amount": _f(cash_discount["amount"])},
    }


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
