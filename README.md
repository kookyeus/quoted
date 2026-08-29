# quoted

**An assertion you cannot make without the words to back it.**

```python
from quoted import Source

doc = Source.from_pages("tariff.pdf", pages)

claim = doc.find("the monthly demand charge of $8.540 per kW will be reduced")
print(claim)
# "the monthly demand charge of $8.540 per kW will be reduced" — tariff.pdf · page 2

doc.find("demand charge of $9.540 per kW")   # one digit wrong
# None
```

**If the words are not in the document, you get nothing to say.**

There is no constructor that skips verification. A `Claim` exists only because the
text was found, and it carries where it was found. That is the entire library.

---

## Why it exists

I spent three weeks building an agent that reads filed electricity tariffs and
tells manufacturers whether they are being charged correctly. In three days it
produced six failures, and every one had the same shape: **a step reported success
without establishing it.**

- A mailbox monitor lost permission, returned an empty list, and reported
  *"no replies"* — **the same words it uses when it has genuinely looked.**
- A send confirmation matched the previous message to the same person and reported
  the wrong timestamp as proof of delivery.
- A publisher uploaded ten files, said *"10 files published"*, and shipped none of
  the one that mattered.
- A researcher asked for a tariff window invented `"11:00 a.m. to 7:00 p.m."`
  with nothing behind it, and stated it fluently.

The last one is the reason this exists. **A confident fabrication is worse than a
crash**, because a crash stops you and a fabrication gets forwarded to a client.

---

## Where this sits

By 2026 "hallucination" is usually split into four failure modes — **factual,
grounding, citation, reasoning** — each wanting its own detector. `quoted` does
one of them, on purpose: **citation and grounding**, the question *"is this
wording actually in the source?"*

And it answers that question differently from almost everything else in the space.
Most tools reach for an LLM-as-judge or an embedding-similarity score. Both give
you a number, and a number near 1.0 is exactly how a changed digit slips through.

`quoted` uses neither. It is **deterministic**: an exact match after typography is
normalised, a verbatim passage or an honest refusal, nothing in between. No model
to grade the grader, no threshold to tune, no similarity that rounds a wrong fact
up to right. That makes it narrow — it will not tell you whether a paraphrase is
*faithful* — and it makes the thing it does do checkable by a human in a way a
score never is.

If your failure is a citation that does not survive being looked up, this is the
tool. If it is a paraphrase drifting from its source, you want a grounding scorer,
not this.

## What it refuses to do

**That is the feature. It is not a limitation of the implementation.**

| Refuses | Because |
|---|---|
| Return a claim whose text is not in the source | An unsourced assertion is the failure mode |
| Treat "I could not read it" as "there is nothing there" | Blindness must never look like silence |
| Match on meaning, similarity, or embedding distance | *Nearly* the same wording is a different fact |
| Guess a location it cannot establish | `"location not identified"` is an honest answer |

**It does not do retrieval-augmented generation.** It does not rank, embed, or
summarise. Those tools help a model find something to say; **this one stops it
saying what it cannot show.**

---

## The two ways to ask, and why there are two

```python
doc.find(quote)       # -> Claim | None    absence is a value you handle
doc.must_find(quote)  # -> Claim           absence raises NotFound
```

Use `must_find` wherever absence must not be quietly swallowed. **The mailbox
monitor above returned an empty list on failure and the caller reported silence.**
An exception would have been read correctly.

`Unreadable` and `NotFound` are separate exceptions on purpose. *"I looked and it
is not there"* and *"I could not look"* are different facts, and collapsing them is
exactly how a blind system reports calm.

---

## Typography is not meaning

A model handed `"15-minute demand"` quoted it back with a **non-breaking hyphen**.
A naive substring check called a correctly quoted, properly sourced answer
unverified — **it was checking the font.**

`quoted` normalises dashes, quotation marks, ligatures, soft hyphens, zero-width
spaces and whitespace before comparing, and nothing else. **Wording is never
relaxed.** `$8.540` and `$9.540` are different claims and always will be.

---

## The usage that works: search, then quote

**Do not guess a quotation and ask the library to confirm it.** Guessing is how
you end up refused for reasons that have nothing to do with truth.

A real example. This is a filed electricity tariff:

> *"the monthly demand charge of $8.540 per kW **R** will be reduced by $0.05266…"*

That stray `R` is a revision marker the tariff uses to flag changed lines. It sits
in the middle of the sentence. A quotation typed from memory omits it, and `find`
refuses — **correctly**, because those are not the same characters.

```python
doc.find("$8.540 per kW will be reduced")     # None — the R is missing
doc.find("$8.540 per kW R will be reduced")   # Claim
```

**So search for a term and let the document tell you its own wording:**

```python
for hit in doc.search("monthly on-peak hours of use less than 100"):
    print(hit.cite(), hit.text)      # verbatim, with its page
```

Extracted PDFs are full of this — revision markers, line numbers, running headers
landing mid-sentence. **The library will not paper over them**, because the same
leniency that forgives a stray `R` would forgive a changed digit.

---

## Install

**Not on PyPI yet.** Install from source — there is nothing to build:

```
pip install git+https://github.com/kookyeus/quoted
```

Or clone it and point Python at `src/`:

```
git clone https://github.com/kookyeus/quoted && export PYTHONPATH=quoted/src
```

No dependencies. Pure standard library, Python 3.10+.

**It does not bundle PDF extraction.** Extraction is a choice with its own
trade-offs and its own dependencies; make it yourself and pass the text in.

```python
Source.from_file("notes.txt")
Source.from_pages("report.pdf", ["page one text", "page two text"])
Source(name="anything", text=whatever_you_extracted)
```

---

## As a service

**A refusal is only half useful if it just says no.** Told *"not found"*, a caller —
human or model — guesses again. So over HTTP the refusal names **the longest run of
the quote that is genuinely in the document, and the exact point where it stops
being true.**

**Running at https://quoted-jnow.onrender.com** — try it:

```
curl -X POST https://quoted-jnow.onrender.com/verify -d '{
  "document": "The on-peak demand charge applies from 10 a.m. to 8 p.m. on weekdays.",
  "quote": "from 10 a.m. to 10 p.m. every day"}'
```

It is a free instance: it sleeps after about fifteen minutes and takes roughly
fifty seconds to wake. Or run it yourself:

```
python3 -m quoted.serve          # PORT and MAX_BYTES from the environment
```

```
POST /verify  {"document": "...", "quote": "from 10 a.m. to 10 p.m. every day"}

{
  "verified": false,
  "verified_prefix": "from 10 a.m. to",
  "diverges_at": "10 p.m. every day",
  "nearest": [{"text": "The on-peak demand charge applies from 10 a.m. to 8 p.m.
                        on weekdays, excluding holidays.", "locator": "page 16"}]
}
```

**That is the shape of nearly every fabricated citation** — a true clause with a
false ending welded onto it. This one is real: I published the ten-to-ten version
to eight people before the library refused it and the filed book gave me the true
wording on page 16.

**A refused verification returns 200, not an error.** The question was answered
correctly and the answer is no. A 4xx invites retry logic to treat an honest
refusal as a transient failure, which is how these systems end up citing sources
nobody read.

**A document over the size limit is refused rather than truncated**, for the same
reason: a quotation that cannot be found because we stopped reading is
indistinguishable from one that was never there.

`POST /search` returns verbatim passages. `GET /health` says whether it is up.

### In a container

```
docker build -t quoted . && docker run -p 8080:8080 quoted
```

No install step in the Dockerfile, because there is nothing to install. **Disclosure:
I have written this file but never run it — Docker is not installed on the machine
this was built on.** Given what the rest of this README is about, saying so seemed
compulsory.

---

## Tests

Every test is a failure that actually happened.

```
python3 tests/test_quoted.py     # the library
python3 tests/test_serve.py      # the service
```

One of the service tests exists because the first version of `/verify` matched the
word **"the"** in *"the Federal Reserve raised rates"* against an electricity
tariff and reported it as a verified prefix. **A one-word match on a stopword is
not verification**, and offering it as evidence flattered a claim that was entirely
false. A prefix must now be at least three words before it counts.

---

*Written by Kenneth, sixteen, in Oshkosh, Wisconsin — because I needed it and
nothing else refused.*
