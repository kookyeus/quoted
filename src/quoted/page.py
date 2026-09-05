"""The front door — the thing a person sees when they follow the link.

**Written 2026-09-05, after checking what a stranger actually got.** The service
had been live for eight days and answered `GET /` with a health blob:

    {"ok": true, "service": "quoted", "uptime_seconds": 4.7, ...}

Anything else was `404 no such endpoint`. Every route was POST-only and
JSON-only. So the API worked perfectly and **the product did not exist** — a
person clicking the link waited thirteen seconds for a free instance to wake and
was then shown a JSON object with no way in.

A Show HN post had been drafted and held against that URL. It would have
launched onto a health check.

The page is deliberately one file with no build step, no framework and no CDN:
it must survive a cold start on a free instance where every extra request is
another second of a stranger's patience.

Last updated: 2026-09-05 by JARVIS
"""

from __future__ import annotations

# A near-miss, prefilled, so the first click demonstrates the whole point
# without anybody typing. The quotation is plausible, the document is real in
# shape, and the divergence lands on the number — which is the failure the
# service was built for.
DEMO_DOC = (
    "Rate Cp-1 applies to non-residential customers whose maximum measured "
    "demand equals or exceeds 500 kilowatts.\n\n"
    "The customer charge is $8.540 per day.\n\n"
    "On-peak hours are 8 a.m. to 8 p.m., Monday through Friday, excluding "
    "holidays. All other hours are off-peak.\n\n"
    "Demand is measured as the greatest fifteen-minute integrated demand "
    "occurring during on-peak hours in the billing month."
)
DEMO_QUOTE = "On-peak hours are 8 a.m. to 10 p.m., Monday through Friday"

PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quoted — a citation verifier that refuses rather than guesses</title>
<meta name="description" content="Paste a document and a quotation. Quoted tells
you whether the wording is genuinely in the document, and where it stops being
true.">
<style>
*{box-sizing:border-box}
body{max-width:52rem;margin:0 auto;padding:2.5rem 1.25rem 5rem;
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif;
 color:#16181d;background:#fdfdfc}
h1{font-size:1.6rem;margin:0 0 .35rem;letter-spacing:-.01em}
.sub{color:#5b6068;margin:0 0 1.6rem}
label{display:block;font-weight:600;font-size:.88rem;margin:1.1rem 0 .35rem}
label span{font-weight:400;color:#6b7079}
textarea,input{width:100%;font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
 padding:.7rem .8rem;border:1px solid #d6d6d1;border-radius:6px;background:#fff;
 color:inherit;resize:vertical}
textarea:focus,input:focus{outline:2px solid #0b5;outline-offset:-1px;border-color:#0b5}
#doc{height:11rem}#quote{height:4.5rem}
button{margin-top:1.1rem;font:600 15px/1 inherit;padding:.8rem 1.4rem;border:0;
 border-radius:6px;background:#16181d;color:#fff;cursor:pointer}
button:hover{background:#000}button:disabled{background:#9a9ea5;cursor:default}
#out{margin-top:1.6rem}
.card{border:1px solid #d6d6d1;border-left-width:4px;border-radius:6px;
 padding:1rem 1.1rem;background:#fff}
.yes{border-left-color:#0b5}.no{border-left-color:#c2410c}.err{border-left-color:#b91c1c}
.verdict{font-weight:700;margin:0 0 .5rem}
.yes .verdict{color:#067a45}.no .verdict{color:#9a3412}.err .verdict{color:#991b1b}
.mono{font:13.5px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;
 background:#f6f6f4;padding:.55rem .7rem;border-radius:5px;
 white-space:pre-wrap;word-break:break-word;margin:.3rem 0 .8rem}
.ok{background:#dcfce7;padding:.05em .15em;border-radius:2px}
.bad{background:#fee2e2;padding:.05em .15em;border-radius:2px;
 text-decoration:line-through;text-decoration-color:#dc2626}
.k{font-size:.8rem;font-weight:600;color:#6b7079;letter-spacing:.04em;
 text-transform:uppercase;margin:.9rem 0 .2rem}
footer{margin-top:3rem;padding-top:1.2rem;border-top:1px solid #e6e6e2;
 color:#6b7079;font-size:.88rem}
a{color:#0b5}
.note{font-size:.88rem;color:#5b6068;margin:.6rem 0 0}
@media(prefers-color-scheme:dark){
 body{background:#131417;color:#e7e7e4}
 h1{color:#fff}.sub,.k,footer,.note{color:#9a9ea5}
 textarea,input,.card{background:#1b1d21;border-color:#32353c}
 .mono{background:#232629}button{background:#e7e7e4;color:#131417}
 button:hover{background:#fff}
 .ok{background:#14532d;color:#dcfce7}.bad{background:#5c1a1a;color:#fee2e2}
 footer{border-top-color:#2a2d33}
}
</style></head><body>

<h1>Quoted</h1>
<p class="sub">Paste a document and a quotation. It tells you whether that
wording is genuinely in the document &mdash; and if it is not,
<strong>where it stops being true</strong>.</p>

<label for="doc">The document <span>&mdash; the source of truth</span></label>
<textarea id="doc" spellcheck="false">__DOC__</textarea>

<label for="quote">The quotation <span>&mdash; the wording to check</span></label>
<textarea id="quote" spellcheck="false">__QUOTE__</textarea>

<button id="go">Check it</button>
<p class="note">Prefilled with a near-miss from a real electricity tariff. Press
the button before changing anything.</p>

<div id="out"></div>

<footer>
Built by <strong>Kenneth</strong>, sixteen, in Oshkosh, Wisconsin, after a
verifier told him a quotation was fine because two visually identical strings
had different bytes.
<br><br>
Nothing you paste is stored or logged.
&middot; <a href="https://github.com/kookyeus/quoted">Source</a>
&middot; <a href="https://kookyeus.github.io/pjm-queue-notes/">Notes</a>
&middot; <code>POST /verify</code> with <code>{document, quote}</code>
</footer>

<script>
const $ = id => document.getElementById(id);
const esc = s => s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

$('go').addEventListener('click', async () => {
  const btn = $('go'), out = $('out');
  const document_ = $('doc').value, quote = $('quote').value;
  btn.disabled = true; btn.textContent = 'Checking\\u2026';
  out.innerHTML = '';
  try {
    const r = await fetch('/verify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({document: document_, quote: quote})
    });
    const d = await r.json();
    out.innerHTML = d.error ? card('err', 'Refused', '<p>' + esc(d.error) + '</p>')
                            : render(d);
  } catch (e) {
    out.innerHTML = card('err', 'Could not reach the service',
      '<p>' + esc(String(e)) + '</p>');
  } finally { btn.disabled = false; btn.textContent = 'Check it'; }
});

function card(cls, verdict, body) {
  return '<div class="card ' + cls + '"><p class="verdict">' + verdict +
         '</p>' + body + '</div>';
}

function render(d) {
  if (d.verified) {
    return card('yes', 'Verified \\u2014 that wording is in the document',
      '<div class="k">As it appears</div><div class="mono">' +
      esc(d.text) + '</div>' +
      (d.locator ? '<div class="k">Where</div><div class="mono">' +
                   esc(d.locator) + '</div>' : ''));
  }
  let b = '<p>' + esc(d.reason || 'that wording does not appear') + '</p>';
  if (d.verified_prefix) {
    // The prefix ends on a word and the divergence begins on the next one, so
    // the space between them belongs to neither. Without this the marked claim
    // renders as "8 a.m. to10 p.m." and reads as a bug in the finding.
    const gap = /\s$/.test(d.verified_prefix) ||
                /^\s/.test(d.diverges_at || '') ? '' : ' ';
    b += '<div class="k">The claim, marked</div><div class="mono">' +
         '<span class="ok">' + esc(d.verified_prefix) + '</span>' + gap +
         '<span class="bad">' + esc(d.diverges_at || '') + '</span></div>' +
         '<p class="note">Green is genuinely in the document. Red is where it ' +
         'stops being true.</p>';
  } else {
    b += '<p class="note">No part of it is in the document. The subject is ' +
         'not discussed there at all.</p>';
  }
  if (d.nearest && d.nearest.length) {
    b += '<div class="k">What the document actually says</div>';
    for (const n of d.nearest) {
      b += '<div class="mono">' + esc(n.text) + '</div>';
    }
  }
  return card('no', 'Not verified', b);
}
</script>
</body></html>"""


def html() -> str:
    """The page, with the demo substituted in.

    Substituted rather than interpolated at import so the literal above stays
    readable and the braces in the stylesheet need no escaping.
    """
    return (PAGE.replace("__DOC__", DEMO_DOC)
                .replace("__QUOTE__", DEMO_QUOTE))
