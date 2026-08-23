# Verifying what a model quotes

A language model asked to quote a document will sometimes produce a quotation that
is *nearly* right — the correct subject, the correct register, one changed figure.
**That is the dangerous failure, because it survives review by a person who already
believes it.**

## The pattern

```python
from quoted import Source

doc = Source(name="tariff.pdf", text=extracted_text)

claim = doc.find(model_output_quote)
if claim is None:
    raise ValueError(f"unsourced: {model_output_quote!r}")
print(claim.cite(), claim.text)
```

`find` returns `None` when the wording is not present. `must_find` raises instead.
**Use `must_find` wherever an absence must not be quietly swallowed** — an empty
return value becomes an empty list becomes a sentence saying nothing was found.

## What it will not do

It does not match on meaning, similarity, or embedding distance. `$8.540` and
`$9.540` are different claims and always will be. **Nearly the same wording is a
different fact**, which is the entire reason to run this check rather than a
semantic one.

## What it does relax

Typography, and only typography. Dashes, quotation marks, ligatures, soft hyphens
and zero-width spaces are normalised before comparison.

**This matters more than it sounds.** A model handed `15-minute demand` returned it
with a non-breaking hyphen, and a naive substring check called a correctly quoted,
properly sourced answer unverified. **It was checking the font.**
