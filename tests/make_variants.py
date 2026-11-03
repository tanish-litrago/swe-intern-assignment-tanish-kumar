"""Generates our OWN synthetic Kessler-style PDFs (not part of the assignment pack) together with the
expected extraction result, to prove the extractor survives layout drift. Run: python tests/make_variants.py"""
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal as D
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kessler.helpers import build_document  # noqa: E402

H = A4[1]
BUYER = {"name": "Rheinwerk Anlagenbau AG", "street": "Hafenstraße 88", "postal_code": "47119",
         "city": "Duisburg", "customer_number": "40217"}
SUPPLIER = {"name": "Kessler Industrietechnik GmbH", "vat_id": "DE287364519"}
RETURN = "Kessler Industrietechnik GmbH · Gewerbestraße 14 · 73760 Ostfildern"
FOOT = "USt-IdNr. DE287364519 · Steuer-Nr. 59/012/34567 · HRB 731184 Amtsgericht Stuttgart"
cent = lambda x: x.quantize(D("0.01"), ROUND_HALF_UP)


def de(x):
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if x < 0 else "") + s


def price_de(x):
    """Unit price with 2-3 decimals (0,152 must stay 0,152)."""
    s = f"{abs(x):,.3f}"
    s = s[:-1] if s.endswith("0") else s
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct_de(x):
    """Decimal('10') -> '10' (Decimal.normalize() would give '1E+1')."""
    return f"{x.normalize():f}".replace(".", ",")


def item(pos, art, desc, qty, unit, price, pe=1, disc=None, vat=19, notes=(), discount_row=False):
    base = D(str(qty)) * D(str(price)) / D(pe)
    amount = cent(base * D(str(disc or 0)) / 100)
    return {"position": pos, "article_number": art, "description": " ".join([desc, *notes]), "quantity": D(str(qty)),
            "unit": unit, "unit_price": D(str(price)), "price_unit": D(pe),
            "discount_percent": None if disc is None else D(str(disc)),
            "line_total": cent(base) - amount, "vat_rate": vat, "_desc": desc, "_notes": notes,
            "_base": cent(base), "_discount_amount": amount, "_row": discount_row}


def totals(items):
    net = {}
    for it in items:
        net[it["vat_rate"]] = net.get(it["vat_rate"], D(0)) + it["line_total"]
    vat = {r: cent(n * r / 100) for r, n in net.items()}
    return net, vat


def expected(layout_items, meta, cash=None):
    net, vat = totals(layout_items)
    clean = [{k: v for k, v in it.items() if not k.startswith("_")} for it in layout_items]
    return build_document(
        doc_type="invoice", number=meta["number"], doc_date=meta["date"], service_date=meta.get("service"),
        due_date=meta.get("due"), supplier=SUPPLIER, buyer=BUYER, order_reference=meta.get("order"),
        delivery_note=meta.get("delivery"), referenced_invoice=None, items=clean, net_by_rate=net, vat_by_rate=vat,
        net_total=sum(net.values()), vat_total=sum(vat.values()),
        gross_total=sum(net.values()) + sum(vat.values()), cash_discount=cash)


class Page:
    def __init__(self, c):
        self.c = c

    def t(self, x, top, s, right=False, size=8.5):
        self.c.setFont("Helvetica", size)
        (self.c.drawRightString if right else self.c.drawString)(x, H - top - 7, s)


def render_v1(path, layout_items, meta, shift=0, split_after=None, header_word="Art.-Nr.", cash=None):
    c = canvas.Canvas(str(path), pagesize=A4)
    p = Page(c)
    dd = lambda d: d.strftime("%d.%m.%Y")
    pages = [layout_items[:split_after], layout_items[split_after:]] if split_after else [layout_items]

    def header(top, first):
        if first:
            p.t(51, 120, RETURN)
            for i, line in enumerate([BUYER["name"], "Abt. Kreditorenbuchhaltung", BUYER["street"],
                                      f"{BUYER['postal_code']} {BUYER['city']}"]):
                p.t(51, 134 + 13 * i, line)
            p.t(51, 229, "RECHNUNG", size=14)
        rows = [("Rechnungs-Nr.", meta["number"]), ("Datum", dd(meta["date"])), ("Kunden-Nr.", "40217")]
        if first:
            if meta.get("order"):
                rows.append(("Ihre Bestellung", f"{meta['order']} vom 22.09.2026"))
            rows.append(("Lieferschein-Nr.", meta["delivery"]))
            if meta.get("service"):
                rows.append(("Leistungsdatum", dd(meta["service"])))
        for i, (lab, val) in enumerate(rows):
            p.t(346, 118 + 12.5 * i, lab)
            p.t(544, 118 + 12.5 * i, val, right=True)
        p.t(51, top, "Pos.")
        p.t(85, top, header_word)
        p.t(159, top, "Bezeichnung")
        p.t(363 + shift, top, "Menge", right=True)
        p.t(371 + shift, top, "ME")
        p.t(447 + shift, top, "Einzelpreis", right=True)
        p.t(449 + shift, top, "€")
        p.t(471 + shift, top, "PE", right=True)
        p.t(478 + shift, top, "Rab.")
        p.t(505 + shift, top, "%", right=True)
        p.t(546 + shift, top, "Gesamt", right=True)
        p.t(548 + shift, top, "€")
        p.t(564 + shift, top, "USt")
        p.t(587 + shift, top, "%", right=True)

    def footer(n, total):
        p.t(51, 800, f"{RETURN} · Tel. +49 711 448210-0          Seite {n} von {total}", size=7)
        p.t(51, 818, FOOT, size=7)

    carried = D(0)
    for n, chunk in enumerate(pages, 1):
        top = 316 if n == 1 else 230
        header(top - 20, n == 1)
        if n > 1:
            p.t(159, top, "Übertrag von Seite 1")
            p.t(553 + shift, top, de(carried), right=True)
            top += 18
        for it in chunk:
            p.t(51, top, str(it["position"]))
            p.t(85, top, it["article_number"])
            p.t(159, top, it["_desc"])
            p.t(363 + shift, top, de(it["quantity"]).replace(",00", ""), right=True)
            p.t(371 + shift, top, it["unit"])
            p.t(454 + shift, top, price_de(it["unit_price"]), right=True)
            p.t(471 + shift, top, str(int(it["price_unit"])), right=True)
            if it["discount_percent"] is not None:
                p.t(505 + shift, top, pct_de(it["discount_percent"]), right=True)
            p.t(553 + shift, top, de(it["line_total"]), right=True)
            p.t(587 + shift, top, str(it["vat_rate"]), right=True)
            top += 14.5
            for note in it["_notes"]:
                p.t(159, top - 3, note)
                top += 11
            carried += it["line_total"]
        if n < len(pages):
            p.t(159, top + 4, "Übertrag")
            p.t(553 + shift, top + 4, de(carried), right=True)
            footer(n, len(pages))
            c.showPage()
    net, vat = totals(layout_items)
    top += 14
    for r in sorted(net, reverse=True):
        p.t(346, top, f"Nettobetrag {r} % USt")
        p.t(553, top, de(net[r]), right=True)
        top += 12
    for r in sorted(net, reverse=True):
        p.t(346, top, f"zzgl. {r} % USt auf {de(net[r])}")
        p.t(553, top, de(vat[r]), right=True)
        top += 12
    gross = sum(net.values()) + sum(vat.values())
    p.t(346, top, "Rechnungsbetrag")
    p.t(520, top, f"{de(gross)} EUR", right=True)
    top += 20
    if meta.get("due"):
        p.t(51, top, f"Zahlbar bis {dd(meta['due'])} ohne Abzug.")
        top += 11
    if cash:
        p.t(51, top, f"Bei Zahlung bis {dd(cash['until'])} abzüglich {pct_de(cash['percent'])} % "
                     f"Skonto (= {de(cash['amount'])} EUR).")
    footer(len(pages), len(pages))
    c.save()


def render_v2(path, layout_items, meta):
    c = canvas.Canvas(str(path), pagesize=A4)
    p = Page(c)
    long = lambda d: f"{d.day}. {['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'][d.month-1]} {d.year}"
    for i, (lab, val) in enumerate([("Rechnung Nr.", meta["number"]), ("Rechnungsdatum", long(meta["date"])),
                                    ("Lieferdatum", long(meta["service"])), ("Kundennummer", "40217"),
                                    ("Bestellnummer", meta["order"]), ("Lieferschein", meta["delivery"])]):
        p.t(51, 55 + 12.5 * i, lab)
        p.t(147, 55 + 12.5 * i, val)
    p.t(431, 69, "Industrietechnik GmbH · seit 1987")
    p.t(334, 120, RETURN)
    for i, line in enumerate([BUYER["name"], "z. Hd. Kreditorenbuchhaltung", BUYER["street"],
                              f"{BUYER['postal_code']} {BUYER['city']}", "DEUTSCHLAND"]):
        p.t(334, 134 + 13 * i, line)
    p.t(51, 229, "Rechnung", size=14)
    top = 260
    for x, s, right in [(51, "Pos", False), (102, "Menge", True), (108, "Einh.", False), (142, "Artikel", False),
                        (210, "Beschreibung", False), (468, "Preis/Einh.", True), (499, "MwSt", True),
                        (567, "Betrag", True)]:
        p.t(x, top, s, right=right)
    top += 17
    for it in layout_items:
        p.t(51, top, f"{it['position']:03d}")
        p.t(102, top, de(it["quantity"]).replace(",00", ""), right=True)
        p.t(108, top, it["unit"])
        p.t(142, top, it["article_number"])
        p.t(210, top, it["_desc"])
        p.t(461, top, price_de(it["unit_price"]), right=True)
        p.t(463, top, "€")
        p.t(499, top, f"{it['vat_rate']}%", right=True)
        p.t(560, top, de(it["_base"]), right=True)
        p.t(562, top, "€")
        top += 14
        if it["_row"]:
            pct = pct_de(it["discount_percent"])
            p.t(210, top - 2, f"abzgl. Sonderrabatt {pct} % auf {de(it['_base'])} €")
            p.t(560, top - 2, de(-it["_discount_amount"]), right=True)
            p.t(562, top - 2, "€")
            top += 12
        for note in it["_notes"]:
            p.t(210, top - 2, note)
            top += 12
    net, vat = totals(layout_items)
    top += 8
    p.t(334, top, "Summe netto")
    p.t(560, top, de(sum(net.values())), right=True)
    p.t(562, top, "€")
    for r in sorted(vat, reverse=True):
        top += 13
        p.t(334, top, f"MwSt {r}%")
        p.t(560, top, de(vat[r]), right=True)
        p.t(562, top, "€")
    top += 13
    p.t(334, top, "Gesamtbetrag")
    p.t(560, top, de(sum(net.values()) + sum(vat.values())), right=True)
    p.t(562, top, "€")
    p.t(51, top + 24, f"Zahlungsziel: 30 Tage netto (bis {long(meta['due'])}). Kein Skontoabzug.")
    p.t(51, 800, f"{RETURN} · Tel. +49 711 448210-0          Seite 1 von 1", size=7)
    p.t(51, 818, FOOT, size=7)
    c.save()


def make_all(folder):
    """Returns {name: (pdf_path, expected_dict_or_None)}; None means 'must raise UnknownLayout'."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    base = [item(1, "KI-40112", "Rillenkugellager 6205-2RS", 24, "Stk", "8.45"),
            item(2, "KI-55219", "Spannelement Typ RFN 7012 40x65", 4, "Stk", "38.15", disc=5),
            item(3, "KI-20811", "Sechskantschraube DIN 933 M10x40 8.8 verz.", 1000, "Stk", "14.60", pe=100,
                 notes=("Charge 2026-114",)),
            item(4, "BU-90011", "Fachbuch: Tabellenbuch Metall", 2, "Stk", "34.90", vat=7)]
    meta = {"number": "RE-2026-90001", "date": date(2026, 10, 20), "service": date(2026, 10, 19),
            "due": date(2026, 11, 19), "order": "4500099001", "delivery": "LS-99001"}
    cash = {"percent": D("2"), "until": date(2026, 10, 30), "amount": D("11.11")}
    # A: table columns drift 8 pt to the right
    render_v1(folder / "A_shifted_columns.pdf", base, meta, shift=8, cash=cash)
    out["A_shifted_columns"] = (folder / "A_shifted_columns.pdf", expected(base, meta, cash))
    # B: two pages with carry-over rows and a note line right before the page break
    many = [item(i, "KI-40112", "Rillenkugellager 6205-2RS", 10 + i, "Stk", "8.45",
                 notes=("lt. Ihrer Anfrage",) if i in (3, 7) else ()) for i in range(1, 15)]
    render_v1(folder / "B_two_pages.pdf", many, meta, split_after=7, cash=cash)
    out["B_two_pages"] = (folder / "B_two_pages.pdf", expected(many, meta, cash))
    # C: optional fields missing (no order, no service date, no due date, no Skonto)
    meta_c = {k: v for k, v in meta.items() if k not in ("order", "service", "due")}
    render_v1(folder / "C_minimal.pdf", base[:2], meta_c)
    out["C_minimal"] = (folder / "C_minimal.pdf", expected(base[:2], meta_c))
    # D: new layout with discount rows on two items
    new = [item(1, "KI-40112", "Rillenkugellager 6205-2RS", 30, "Stk", "8.69"),
           item(2, "KI-31009", "Linearführungswagen HGH25CA", 4, "Stk", "116.40", disc=3, discount_row=True),
           item(3, "KI-20811", "Sechskantschraube DIN 933", 600, "Stk", "0.152", notes=("Preis je Stück",)),
           item(4, "KI-77002", "Schmierfett Lithium EP2", 12, "Stk", "10.15", disc=10, discount_row=True),
           item(5, "BU-90034", "Fachbuch: Hydraulik", 1, "Stk", "49.80", vat=7)]
    render_v2(folder / "D_new_layout_two_discount_rows.pdf", new, meta)
    out["D_new_layout_two_discount_rows"] = (folder / "D_new_layout_two_discount_rows.pdf", expected(new, meta))
    # E: header column renamed -> no known layout, must fail loudly
    render_v1(folder / "E_unknown_layout.pdf", base[:2], meta, header_word="Artikel-Nr.")
    out["E_unknown_layout"] = (folder / "E_unknown_layout.pdf", None)
    return out


if __name__ == "__main__":
    make_all(Path(__file__).parent / "variants")
    print("variants written to tests/variants/")
