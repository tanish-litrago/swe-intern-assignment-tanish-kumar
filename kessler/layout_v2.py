"""Kessler layout 2 (INV-05, 'new format since 01.10.2026'): label/value block top left, buyer address
top right, no PE / Rab. columns, discounts as their own row under the item, '€' in every cell."""
import re
from decimal import Decimal

from .helpers import (block_lines, build_document, page_lines, parse_address_block, parse_date,
                      parse_de_number, table_rows)

HEADER_WORDS = {"Beschreibung", "Preis/Einh.", "MwSt", "Betrag"}
STOP = re.compile(r"(Summe netto|Zahlungsziel|Kessler Industrietechnik GmbH\s*·)")
LABELS = [("Rechnung Nr.", "number"), ("Rechnungsdatum", "date"), ("Lieferdatum", "service"),
          ("Kundennummer", "customer"), ("Bestellnummer", "order"), ("Lieferschein", "delivery")]
ADDR_X = 330  # buyer address is right of this x; label/value block is left of 300


def _columns(header):
    w = header.words
    t = [x["text"] for x in w]
    return [("pos", "L", w[t.index("Pos")]["x0"]), ("unit", "L", w[t.index("Einh.")]["x0"]),
            ("art", "L", w[t.index("Artikel")]["x0"]), ("desc", "L", w[t.index("Beschreibung")]["x0"]),
            ("qty", "R", w[t.index("Menge")]["x1"]), ("price", "R", w[t.index("Preis/Einh.")]["x1"]),
            ("vat", "R", w[t.index("MwSt")]["x1"]), ("total", "R", w[t.index("Betrag")]["x1"])]


def parse(pdf):
    lines = page_lines(pdf.pages[0])
    hdr = next(ln for ln in lines if HEADER_WORDS <= {w["text"] for w in ln.words})
    meta = {}
    for ln in lines:
        left = ln.text_in(0, 300)
        for label, key in LABELS:
            if ln.top < hdr.top and left.startswith(label):
                meta[key] = left[len(label):].strip()
                break
    ret = next(ln for ln in lines if re.search(r"GmbH\s*·.*·\s*\d{5}", ln.text_in(ADDR_X, 10_000)))
    supplier_name = ret.text_in(ADDR_X, 10_000).split("·")[0].strip()
    buyer = parse_address_block(block_lines(lines, ret.top, ADDR_X, 10_000))
    buyer["customer_number"] = meta["customer"]

    items = []
    for c, text in table_rows(pdf, HEADER_WORDS, _columns, STOP):
        if re.fullmatch(r"\d+", c.get("pos", "")):
            items.append({
                "position": int(c["pos"]), "article_number": c["art"], "description": c.get("desc", ""),
                "quantity": parse_de_number(c["qty"]), "unit": c["unit"],
                "unit_price": parse_de_number(c["price"]), "price_unit": Decimal(1),  # no PE column
                "discount_percent": None, "line_total": parse_de_number(c["total"]),
                "vat_rate": int(c["vat"].rstrip("%"))})
        elif items:
            m = re.match(r"abzgl\.\s.*?(\d+(?:,\d+)?)\s*%", c.get("desc", ""))
            if m and c.get("total"):  # discount row: fold into the item above, never its own item
                items[-1]["discount_percent"] = parse_de_number(m[1])
                items[-1]["line_total"] += parse_de_number(c["total"])
            elif c.get("desc"):
                items[-1]["description"] += " " + c["desc"]

    all_text = [ln.text for p in pdf.pages for ln in page_lines(p)]
    vat, net_total, gross, due = {}, None, None, None
    for t in all_text:
        if m := re.match(r"Summe netto\s+(\S+)", t):
            net_total = parse_de_number(m[1])
        elif m := re.match(r"MwSt (\d+)%\s+(\S+)", t):
            vat[int(m[1])] = parse_de_number(m[2])
        elif m := re.match(r"Gesamtbetrag\s+(\S+)", t):
            gross = parse_de_number(m[1])
        elif m := re.search(r"Zahlungsziel:.*\(bis ([^)]+)\)", t):
            due = parse_date(m[1])
    # shortcut: this layout prints no net per VAT rate, so it is derived from the line totals
    net = {}
    for it in items:
        net[it["vat_rate"]] = net.get(it["vat_rate"], Decimal(0)) + it["line_total"]
    vat_id = re.search(r"USt-IdNr\.\s*(DE\s?\d{9})", " ".join(all_text))[1].replace(" ", "")
    return build_document(
        doc_type="invoice", number=meta["number"], doc_date=parse_date(meta["date"]),
        service_date=parse_date(meta["service"]) if "service" in meta else None, due_date=due,
        supplier={"name": supplier_name, "vat_id": vat_id}, buyer=buyer,
        order_reference=meta.get("order"), delivery_note=meta.get("delivery"), referenced_invoice=None,
        items=items, net_by_rate=net, vat_by_rate=vat, net_total=net_total, vat_total=sum(vat.values()),
        gross_total=gross, cash_discount=None)  # shortcut: 'Kein Skontoabzug' is the only terms line seen
