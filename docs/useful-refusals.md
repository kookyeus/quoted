# Refusals that are useful

A refusal that only says *"not found"* makes the caller guess again — and a caller
that guesses is a caller that will eventually guess something plausible.

## What the service returns instead

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

**`verified_prefix` is the longest opening run of the quote that genuinely appears.
`diverges_at` is where it stops being true.**

That is the shape of nearly every fabricated citation: **a true clause with a false
ending welded onto it.** Told only "no", a model retries. Told exactly where its
claim left the document, it corrects itself.

## A prefix must be substantial

Three words and eight characters, minimum. An earlier version matched the word
`"the"` in *"the Federal Reserve raised rates"* against an electricity tariff and
reported it as a verified prefix — **flattering a claim that was entirely false.**

## Why a refusal is HTTP 200

The question was answered correctly and the answer is no. **A 4xx invites retry
logic to treat an honest refusal as a transient failure**, which is one of the ways
these systems end up citing sources nobody read.

For the same reason, a document over the size limit is **refused rather than
truncated**: a quotation that cannot be found because the service stopped reading is
indistinguishable from one that was never there.
