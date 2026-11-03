"""Kessler layout 1 (INV-01..04): label/value block top right, 'PE' and 'Rab. %' columns,
carry-over rows ('Übertrag') between pages, totals split per VAT rate."""
import re
from datetime import timedelta
from decimal import Decimal

from .helpers import (block_lines, build_document, page_lines, parse_address_block, parse_date,
                      parse_de_number, table_rows)

HEADER_WORDS = {"Art.-Nr.", "Menge", "PE", "Rab."}
# Table ends at the totals block, a page-end carry-over, a payment line or the page footer.
STOP = re.compile(r"(Nettobetrag|Zahlbar|Übertrag\s+[\d.,]+$|Kessler Industrietechnik GmbH\s*·)")
LABELS = [("Rechnungs-Nr.", "number"), ("Gutschrift-Nr.", "number"), ("Datum", "date"),
          ("Kunden-Nr.", "customer"), ("Ihre Bestellung", "order"), ("Lieferschein-Nr.", "delivery"),
          ("Leistungsdatum", "service"), ("Bezug Rechnung", "ref")]
RIGHT_X = 340  # label/value block starts right of this x; buyer address is left of it


def _columns(header):
    w = header.words
    t = [x["text"] for x in w]
    pct = lambda after: w[t.index(after) + 1]  # the '%' that follows 'Rab.' / 'USt'
    return [("pos", "L", w[t.index("Pos.")]["x0"]), ("art", "L", w[t.index("Art.-Nr.")]["x0"]),
            ("desc", "L", w[t.index("Bezeichnung")]["x0"]), ("unit", "L", w[t.index("ME")]["x0"]),
            ("qty", "R", w[t.index("Menge")]["x1"]), ("price", "R", w[t.index("Einzelpreis")]["x1"]),
            ("pe", "R", w[t.index("PE")]["x1"]), ("rab", "R", pct("Rab.")["x1"]),
            ("total", "R", w[t.index("Gesamt")]["x1"]), ("vat", "R", pct("USt")["x1"])]


def parse(pdf):
    lines = page_lines(pdf.pages[0])
    hdr = next(ln for ln in lines if HEADER_WORDS <= {w["text"] for w in ln.words})
    meta, doc_type = {}, "invoice"
    for ln in lines:
        right = ln.text_in(RIGHT_X, 10_000)
        for label, key in LABELS:
            if ln.top < hdr.top and right.startswith(label):
                meta[key] = right[len(label):].strip()
                if label == "Gutschrift-Nr.":
                    doc_type = "credit_note"
                break
    ret = next(ln for ln in lines if re.search(r"GmbH\s*·.*·\s*\d{5}", ln.text_in(0, RIGHT_X)))
    supplier_name = ret.text_in(0, RIGHT_X).split("·")[0].strip()
    buyer = parse_address_block(block_lines(lines, ret.top, 0, RIGHT_X))
    buyer["customer_number"] = meta["customer"]

    items = []
    for c, text in table_rows(pdf, HEADER_WORDS, _columns, STOP):
        if text.startswith("Übertrag"):  # carry-over rows are not items
            continue
        if re.fullmatch(r"\d+", c.get("pos", "")):
            items.append({
                "position": int(c["pos"]), "article_number": c["art"], "description": c.get("desc", ""),
                "quantity": parse_de_number(c["qty"]), "unit": c["unit"],
                "unit_price": parse_de_number(c["price"]),
                "price_unit": parse_de_number(c["pe"]) if c.get("pe") else Decimal(1),
                "discount_percent": parse_de_number(c["rab"]) if c.get("rab") else None,
                "line_total": parse_de_number(c["total"]), "vat_rate": int(c["vat"])})
        elif items and c.get("desc"):  # extra line under an item (batch no., note, reference)
            items[-1]["description"] += " " + c["desc"]

    all_text = [ln.text for p in pdf.pages for ln in page_lines(p)]
    net, vat, gross, due, cash = {}, {}, None, None, None
    doc_date = parse_date(meta["date"])
    for t in all_text:
        if m := re.match(r"Nettobetrag (\d+) % USt\s+(\S+)$", t):
            net[int(m[1])] = parse_de_number(m[2])
        elif m := re.match(r"zzgl\. (\d+) % USt auf \S+\s+(\S+)$", t):
            vat[int(m[1])] = parse_de_number(m[2])
        elif m := re.match(r"(?:Rechnungsbetrag|Gutschriftsbetrag)\s+(\S+) EUR", t):
            gross = parse_de_number(m[1])
        elif m := re.match(r"Zahlbar bis (\S+)", t):
            due = parse_date(m[1])
        elif m := re.search(r"Bei Zahlung bis (\S+) abzüglich ([\d,]+) % Skonto \(= ([\d.,]+) EUR\)", t):
            cash = {"percent": parse_de_number(m[2]), "until": parse_date(m[1]), "amount": parse_de_number(m[3])}
        elif m := re.search(r"innerhalb von (\d+) Tagen ab Rechnungsdatum ([\d,]+) % Skonto \(= ([\d.,]+) EUR\)", t):
            # shortcut: deadline is printed as a day count, so it is computed from the document date
            cash = {"percent": parse_de_number(m[2]), "until": doc_date + timedelta(days=int(m[1])),
                    "amount": parse_de_number(m[3])}
    vat_id = re.search(r"USt-IdNr\.\s*(DE\s?\d{9})", " ".join(all_text))[1].replace(" ", "")
    first = lambda key: meta[key].split()[0] if key in meta else None  # drops 'vom <date>' / 'v. <date>'
    return build_document(
        doc_type=doc_type, number=meta["number"], doc_date=doc_date,
        service_date=parse_date(meta["service"]) if "service" in meta else None, due_date=due,
        supplier={"name": supplier_name, "vat_id": vat_id}, buyer=buyer, order_reference=first("order"),
        delivery_note=meta.get("delivery"), referenced_invoice=first("ref"), items=items,
        net_by_rate=net, vat_by_rate=vat, net_total=sum(net.values()), vat_total=sum(vat.values()),
        gross_total=gross, cash_discount=cash)
