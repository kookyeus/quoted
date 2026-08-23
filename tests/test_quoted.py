"""The tests are the specification. Each one is a real failure that happened."""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from quoted import Source, NotFound, Unreadable

TARIFF = [
 "WISCONSIN ELECTRIC POWER COMPANY\nRate Schedule Cg 2",
 "For monthly on-peak hours of use less than 100, the monthly demand charge "
 "of $8.540 per kW will be reduced by $0.05266 times the difference between "
 "the 100 and the monthly on-peak hours of use.",
 "The customer maximum 15-minute demand will be the greatest rate at which "
 "electrical energy has been used during any period of 15 consecutive minutes "
 "in the current or preceding 11 billing months.",
]

def check(name, cond):
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    return 0 if cond else 1

bad = 0
doc = Source.from_pages("wepco-cg2.pdf", TARIFF)

# 1 — a real quote returns a claim, with its page
c = doc.find("the monthly demand charge of $8.540 per kW will be reduced")
bad += check("finds a genuine passage", c is not None)
bad += check("names the document", c and c.document == "wepco-cg2.pdf")
bad += check("gives a page locator", c and "page" in c.locator)

# 2 — the failure that started this: typography must not defeat a true quote
c2 = doc.find("customer maximum 15‑minute demand")      # non-breaking hyphen
bad += check("survives a non-breaking hyphen", c2 is not None)

# 3 — THE CENTRAL PROPERTY: a false quote yields nothing
bad += check("refuses a passage that is not there",
             doc.find("the demand charge is waived entirely") is None)

# 4 — a plausible near-miss must also fail. This is the one that matters.
bad += check("refuses a plausible-but-wrong figure",
             doc.find("demand charge of $9.540 per kW") is None)

# 5 — absence can be made loud
try:
    doc.must_find("no such text anywhere")
    bad += check("must_find raises on absence", False)
except NotFound:
    bad += check("must_find raises on absence", True)

# 6 — unreadable is NOT the same as not-found
try:
    Source(name="empty.pdf", text="   ")
    bad += check("empty source raises Unreadable", False)
except Unreadable:
    bad += check("empty source raises Unreadable", True)

# 7 — search returns verified passages, each locatable
hits = doc.search("hours of use")
bad += check("search finds the clause", len(hits) >= 1)
bad += check("every search hit is located", all("page" in h.locator for h in hits))

# 10 — a real filed-document artifact: a revision marker mid-sentence.
#      The library must refuse the tidy version, because it is not what is written.
artifact = Source.from_pages("filed.pdf", [
    "the monthly demand charge of $8.540 per kW R will be reduced by $0.05266"])
bad += check("refuses a quote missing a mid-sentence artifact",
             artifact.find("$8.540 per kW will be reduced") is None)
bad += check("accepts the wording actually printed",
             artifact.find("$8.540 per kW R will be reduced") is not None)
bad += check("search recovers the true wording regardless",
             len(artifact.search("demand charge")) >= 1)

print(f"\n  {'ALL PASS' if not bad else str(bad) + ' FAILED'}")
sys.exit(1 if bad else 0)
