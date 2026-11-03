"""python validate.py outputs/  ->  outputs/validation_report.md (checks V1-V7 per document).
A FAIL caused by the document itself is a result, not a bug: we report it, we never correct it."""
import json
import re
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

TOL = D("0.01")
CHECKS = ["V1", "V2", "V3", "V4", "V5", "V6", "V7"]
TITLES = {"V1": "line total = qty x price / PE x (1 - discount)", "V2": "sum of lines = net per VAT rate",
          "V3": "net x rate = VAT per rate", "V4": "net + VAT = gross", "V5": "supplier VAT ID is DE + 9 digits",
          "V6": "dates valid, due date not before document date", "V7": "sign matches document type"}


def d(x):
    return D(str(x))


def fmt(x, sign=False):
    return format(x, "+.2f" if sign else ".2f")


def cause_line(expected, printed):
    """Hypothesis only, never a fact."""
    e, p = fmt(abs(expected)).replace(".", ""), fmt(abs(printed)).replace(".", "")
    if abs(printed - expected) <= D("0.02"):
        return "within 0.02: probably rounding"
    if sorted(e) == sorted(p) and e != p:
        return "printed digits are a permutation of the expected digits: possible digit-transposition typo"
    return "no simple explanation found"


def v1(doc):
    sign = -1 if doc["document_type"] == "credit_note" else 1  # credit notes: qty/price positive, totals negative
    bad, worst = [], D(0)
    for it in doc["line_items"]:
        disc = d(it["discount_percent"] or 0)
        exp = sign * d(it["quantity"]) * d(it["unit_price"]) / d(it["price_unit"]) * (1 - disc / 100)
        diff = d(it["line_total"]) - exp
        worst = max(worst, abs(diff))
        if abs(diff) > TOL:
            bad.append((it, exp, diff))
    info = [f"{len(doc['line_items'])} lines checked, largest difference {fmt(worst)}"]
    for it, exp, diff in bad:
        info.append(f"line pos {it['position']} ({it['article_number']}): expected {fmt(exp)}, printed "
                    f"{fmt(d(it['line_total']))}, difference {fmt(diff, True)}; likely cause: "
                    f"{cause_line(exp, d(it['line_total']))}")
    return not bad, info, bad


def v2(doc, v1_bad):
    info, ok = [], True
    sums = {}
    for it in doc["line_items"]:
        sums[str(it["vat_rate"])] = sums.get(str(it["vat_rate"]), D(0)) + d(it["line_total"])
    printed = doc["totals"]["net_by_vat_rate"]
    for rate in sorted(set(sums) | set(printed), key=int):
        s, p = sums.get(rate, D(0)), d(printed.get(rate, 0))
        diff = s - p
        good = abs(diff) <= TOL
        ok &= good
        line = f"{rate}% : sum of lines {fmt(s)}, printed net {fmt(p)}, difference {fmt(diff, True)}"
        if not good:
            v1_delta = sum((dd for it, _, dd in v1_bad if str(it["vat_rate"]) == rate), D(0))
            if v1_delta and abs(diff - v1_delta) <= TOL:
                line += ("; this equals the V1 error: the printed net matches the recomputed line, so the "
                         "printed line total (not the totals) is the likely mistake")
        info.append(line)
    # Layout 2 prints no net per rate (it is derived from the lines), so the per-rate lines above compare a
    # value with itself there. The comparison with the PRINTED total net is the real test.
    total_lines, printed_total = sum(sums.values(), D(0)), d(doc["totals"]["net_total"])
    diff = total_lines - printed_total
    ok &= abs(diff) <= TOL
    info.append(f"all rates: sum of lines {fmt(total_lines)}, printed total net {fmt(printed_total)}, "
                f"difference {fmt(diff, True)}")
    return ok, info


def v3(doc):
    info, ok = [], True
    for rate, net in doc["totals"]["net_by_vat_rate"].items():
        exp, p = d(net) * D(rate) / 100, d(doc["totals"]["vat_by_vat_rate"].get(rate, 0))
        good = abs(p - exp) <= TOL
        ok &= good
        info.append(f"{rate}% : net {fmt(d(net))} x {rate}% = {fmt(exp)}, printed VAT {fmt(p)}, "
                    f"difference {fmt(p - exp, True)}")
    return ok, info


def v4(doc):
    t = doc["totals"]
    exp = d(t["net_total"]) + d(t["vat_total"])
    diff = d(t["gross_total"]) - exp
    return abs(diff) <= TOL, [f"net {fmt(d(t['net_total']))} + VAT {fmt(d(t['vat_total']))} = {fmt(exp)}, "
                              f"printed gross {fmt(d(t['gross_total']))}, difference {fmt(diff, True)}"]


def v5(doc):
    vid = doc["supplier"]["vat_id"]
    return bool(re.fullmatch(r"DE\d{9}", vid)), [f"supplier VAT ID {vid}"]


def v6(doc):
    info, ok, parsed = [], True, {}
    names = [("document_date", doc["document_date"]), ("service_date", doc.get("service_date")),
             ("due_date", doc.get("due_date")), ("cash discount until", (doc.get("cash_discount") or {}).get("until"))]
    for name, val in names:
        if val is None:
            continue
        try:
            parsed[name] = date.fromisoformat(val)
            info.append(f"{name} {val} valid")
        except ValueError:
            ok = False
            info.append(f"{name} {val} is NOT a valid date")
    if "due_date" in parsed and "document_date" in parsed:
        good = parsed["due_date"] >= parsed["document_date"]
        ok &= good
        info.append(f"due date {'not before' if good else 'BEFORE'} document date")
    return ok, info


def v7(doc):
    t = doc["totals"]
    amounts = ([it["line_total"] for it in doc["line_items"]] + list(t["net_by_vat_rate"].values())
               + list(t["vat_by_vat_rate"].values()) + [t["net_total"], t["vat_total"], t["gross_total"]])
    credit = doc["document_type"] == "credit_note"
    wrong = [a for a in amounts if (a >= 0 if credit else a <= 0)]
    return not wrong, [f"{doc['document_type']}: {len(amounts) - len(wrong)} of {len(amounts)} amounts have the "
                       f"expected sign ({'negative' if credit else 'positive'}); quantity and unit price excluded"]


def validate(doc):
    r1, i1, bad = v1(doc)
    r2, i2 = v2(doc, bad)
    return {"V1": (r1, i1), "V2": (r2, i2), "V3": v3(doc), "V4": v4(doc), "V5": v5(doc), "V6": v6(doc),
            "V7": v7(doc)}


def report(results):
    mark = lambda ok: "PASS" if ok else "FAIL"
    out = ["# Validation report", "",
           "Checks V1-V7 on the extracted JSON files. A FAIL means the *document* is inconsistent as printed "
           "(values are extracted as printed, never corrected). Likely causes are hypotheses, not facts.", "",
           "| Document | " + " | ".join(CHECKS) + " |", "|---|" + "---|" * len(CHECKS)]
    for name, _, res in results:
        out.append(f"| {name} | " + " | ".join(mark(res[c][0]) for c in CHECKS) + " |")
    out += ["", "Check definitions: " + "; ".join(f"{c} = {TITLES[c]}" for c in CHECKS), ""]
    for name, doc, res in results:
        out += [f"## {name} ({doc['document_type']} {doc['document_number']})", ""]
        for c in CHECKS:
            ok, info = res[c]
            out.append(f"- **{c} {mark(ok)}** - {TITLES[c]}")
            out += [f"  - {line}" for line in info]
        out.append("")
    fails = [(n, c) for n, _, res in results for c in CHECKS if not res[c][0]]
    out += ["## Summary", "", "All checks passed." if not fails else
            "Failed checks: " + ", ".join(f"{n}: {c}" for n, c in fails)]
    return "\n".join(out) + "\n"


def main(argv):
    folder = Path(argv[0] if argv else "outputs")
    results = []
    for f in sorted(folder.glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        results.append((f.stem, doc, validate(doc)))
    (folder / "validation_report.md").write_text(report(results), encoding="utf-8")
    print(f"{len(results)} documents -> {folder / 'validation_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
