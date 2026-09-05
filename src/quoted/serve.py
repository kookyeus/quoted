"""An HTTP door onto `quoted`. One endpoint, and it refuses.

**The product is the refusal.** Anything can return a passage that looks right;
the commercially valuable behaviour is declining to confirm a quotation that is
not in the document, which is the failure keeping language models out of law,
medicine, finance and compliance.

**Zero dependencies, exactly like the library.** `http.server` is unfashionable and
entirely adequate for a service whose work is string matching. A dependency here
would be a claim to maintain something, and this project's whole argument is that
claims should be checkable.

## The endpoints

    POST /verify   {"document": "<text>", "quote": "<claimed wording>"}
                   → 200 {"verified": true,  "text": ..., "locator": ...}
                   → 200 {"verified": false, "reason": ..., "nearest": [...]}

    POST /search   {"document": "<text>", "term": "<what to look for>"}
                   → 200 {"passages": [...]}

    GET  /health   → 200 {"ok": true, ...}

**A refused verification is a 200, not a 4xx.** The question was answered
correctly; the answer is no. Returning an error would tempt a caller's retry logic
into treating an honest refusal as a transient failure, which is precisely how
these systems end up citing sources nobody read.

Run: `python3 -m quoted.serve` · `PORT` and `MAX_BYTES` from the environment.
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .source import Source

PORT = int(os.environ.get("PORT", "8080"))

# A document larger than this is refused rather than silently truncated —
# truncation would let a quotation "not be found" because we stopped reading.
from . import page                                  # noqa: E402

MAX_BYTES = int(os.environ.get("MAX_BYTES", str(4 * 1024 * 1024)))

# A verified prefix shorter than this is noise — see `_divergence`.
MIN_PREFIX_WORDS = 3
MIN_PREFIX_CHARS = 8

STARTED = time.time()


class Refused(ValueError):
    """The request cannot be answered as asked. Said plainly, never guessed around."""


def _verify(payload: dict) -> dict:
    doc = payload.get("document")
    quote = payload.get("quote")
    if not isinstance(doc, str) or not doc.strip():
        raise Refused("no document supplied — send the text to check against")
    if not isinstance(quote, str) or not quote.strip():
        raise Refused("no quote supplied — send the wording you want verified")

    src = Source(name=payload.get("name") or "document", text=doc)
    found = src.find(quote)
    if found:
        return {"verified": True, "text": found.text, "locator": found.locator,
                "document": found.document}

    # **A bare "no" makes the caller guess again.** The commercially useful
    # answer says where the claim stops being true — which is what let a filed
    # tariff correct a wording that had already reached eight people.
    longest, tail = _divergence(src, quote)
    nearest = []
    if longest:
        for c in src.search(longest, window=240)[:3]:
            if c.text not in nearest:
                nearest.append({"text": c.text, "locator": c.locator})
    return {
        "verified": False,
        "reason": "that wording does not appear in the document",
        "quote": quote,
        "verified_prefix": longest,
        "diverges_at": tail,
        "nearest": nearest,
        "note": ("`verified_prefix` is the longest run of the quote that IS in the "
                 "document; `diverges_at` is where it stops being true. An empty "
                 "prefix means the subject is not discussed at all."),
    }


def _divergence(src: Source, quote: str) -> tuple[str, str]:
    """The longest opening run of the quote that is genuinely in the document.

    **This is the feature, not a nicety.** Told only "not found", a caller retries
    with another guess. Told "the first nine words are real and it goes wrong at
    'to 10 p.m.'", a caller — human or model — corrects itself. The published
    error this library was built from was exactly of that shape: a true clause
    with a false ending welded on.

    Quotes are short, so the quadratic scan is irrelevant and the clarity is not.
    """
    words = quote.split()
    if not words:
        return "", ""
    lo, hi, best = 1, len(words), 0
    while lo <= hi:                     # longest true prefix, by bisection
        mid = (lo + hi) // 2
        if src.find(" ".join(words[:mid])):
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    # **A one-word match is not verification.** "the Federal Reserve raised rates"
    # against a tariff sheet found "the", and reporting that as a verified prefix
    # would flatter a claim that is entirely false. A prefix must be substantial
    # enough to mean something before it is offered as evidence of anything.
    prefix = " ".join(words[:best])
    if best < MIN_PREFIX_WORDS or len(prefix) < MIN_PREFIX_CHARS:
        return "", quote
    return prefix, " ".join(words[best:])


def _search(payload: dict) -> dict:
    doc = payload.get("document")
    term = payload.get("term")
    if not isinstance(doc, str) or not doc.strip():
        raise Refused("no document supplied")
    if not isinstance(term, str) or not term.strip():
        raise Refused("no term supplied")
    src = Source(name=payload.get("name") or "document", text=doc)
    window = min(int(payload.get("window") or 400), 2000)
    return {"passages": [{"text": c.text, "locator": c.locator}
                         for c in src.search(term, window=window)[:20]]}


ROUTES = {"/verify": _verify, "/search": _search}


class Handler(BaseHTTPRequestHandler):
    server_version = "quoted"
    sys_version = ""                       # do not advertise the interpreter

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body, indent=1).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, body: str) -> None:
        raw = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:                                   # noqa: N802
        path = self.path.rstrip("/")
        # **A person following the link gets a page.** For eight days this
        # returned the health blob to everyone, so the service was live and the
        # product did not exist. `/health` keeps the JSON, because that is what
        # the platform reads.
        if path == "":
            self._send_html(page.html())
        elif path == "/health":
            self._send(200, {"ok": True, "service": "quoted",
                             "uptime_seconds": round(time.time() - STARTED, 1),
                             "endpoints": sorted(ROUTES)})
        else:
            self._send(404, {"error": f"no such endpoint: {self.path}",
                             "endpoints": sorted(ROUTES)})

    def do_POST(self) -> None:                                  # noqa: N802
        route = ROUTES.get(self.path.rstrip("/"))
        if not route:
            self._send(404, {"error": f"no such endpoint: {self.path}",
                             "endpoints": sorted(ROUTES)})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send(400, {"error": "unreadable Content-Length"})
            return
        if length <= 0:
            self._send(400, {"error": "empty request body"})
            return
        if length > MAX_BYTES:
            # **Refused rather than truncated.** A quotation that "cannot be found"
            # because we stopped reading is the exact lie this service exists to
            # prevent, and it would be indistinguishable from an honest refusal.
            self._send(413, {"error": f"document exceeds {MAX_BYTES} bytes",
                             "why": "truncating it would produce a false refusal"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise Refused("body must be a JSON object")
            self._send(200, route(payload))
        except Refused as e:
            self._send(400, {"error": str(e)})
        except json.JSONDecodeError as e:
            self._send(400, {"error": f"body is not valid JSON: {e}"})
        except Exception as e:                                  # noqa: BLE001
            # Named, never smoothed into a generic 500 with a cheerful body.
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"{self.log_date_time_string()} {fmt % args}\n")


def main() -> None:
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    sys.stderr.write(f"quoted listening on 0.0.0.0:{PORT}\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()


if __name__ == "__main__":
    main()
