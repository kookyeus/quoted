"""Tests for the HTTP door. Run: `python3 tests/test_serve.py`

**The refusal path is tested harder than the success path**, because anything can
return a passage and the product is declining to confirm one that is not there.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quoted.serve import Handler                                # noqa: E402

DOC = ("The on-peak demand charge applies from 10 a.m. to 8 p.m. on weekdays, "
       "excluding holidays. Off-peak demand is billed at $0.00 per kW.")

FAILED: list[str] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f" — {detail}" if not cond else ""))
    if not cond:
        FAILED.append(name)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"


def post(path: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


code, body = post("/verify", {"document": DOC, "quote": "from 10 a.m. to 8 p.m. on weekdays"})
ok("a true quotation is verified", code == 200 and body["verified"] is True, str(body))

code, body = post("/verify", {"document": DOC, "quote": "from 10 a.m. to 10 p.m. every day"})
ok("a false quotation is refused", body.get("verified") is False)
ok("a refusal is 200, not an error", code == 200,
   "a 4xx would let retry logic treat an honest no as a transient failure")
ok("the refusal says where it diverges",
   body.get("diverges_at", "").startswith("10 p.m."), str(body.get("diverges_at")))
ok("the refusal names the true prefix",
   body.get("verified_prefix") == "from 10 a.m. to", str(body.get("verified_prefix")))
ok("the refusal offers the real passage",
   any("8 p.m." in n["text"] for n in body.get("nearest", [])))

code, body = post("/verify", {"document": DOC, "quote": "the Federal Reserve raised rates"})
ok("an unrelated quotation gets an empty prefix", body.get("verified_prefix") == "")

code, body = post("/verify", {"document": DOC})
ok("a missing quote is a 400 with a reason", code == 400 and "quote" in body["error"])

code, body = post("/verify", {"quote": "anything"})
ok("a missing document is a 400 with a reason", code == 400 and "document" in body["error"])

code, body = post("/search", {"document": DOC, "term": "off-peak"})
ok("search finds a real term", code == 200 and len(body["passages"]) >= 1)

code, body = post("/nonsense", {"a": 1})
ok("an unknown endpoint is a 404 that lists the real ones",
   code == 404 and "/verify" in body["endpoints"])

with urllib.request.urlopen(f"{BASE}/health", timeout=10) as r:
    ok("health answers", r.status == 200 and json.loads(r.read())["ok"] is True)

srv.shutdown()
print()
if FAILED:
    print(f"  {len(FAILED)} failing: " + "; ".join(FAILED))
    sys.exit(1)
print("  ALL PASS")
