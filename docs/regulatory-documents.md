# Reading regulatory documents

Filed PDFs — tariffs, dockets, rulings — are the case this library was written
against, and they break naive matching in ways ordinary prose does not.

## What is actually in the text

A real filed electricity tariff reads:

> *"the monthly demand charge of $8.540 per kW **R** will be reduced by $0.05266…"*

That stray `R` is a revision marker flagging a changed line. It sits mid-sentence.
**A quotation typed from memory omits it and is refused** — correctly, because
those are not the same characters.

```python
doc.find("$8.540 per kW will be reduced")     # None — the R is missing
doc.find("$8.540 per kW R will be reduced")   # Claim
```

Extraction also strews line numbers, running headers and page furniture through the
middle of sentences. **The library will not paper over any of it**, because the same
leniency that forgives a stray `R` would forgive a changed digit.

## So work the other way round

```python
for hit in doc.search("monthly on-peak hours of use less than 100"):
    print(hit.cite(), hit.text)
```

**Let the document tell you its own wording**, then quote that. This is not a
workaround; it is the correct use.

## A worked failure

An analysis published to eight people said an on-peak demand window ran
*"from 10 a.m. to 10 p.m."* The filed book says **10 a.m. to 8 p.m., weekdays
only**. The library refused the published wording and `search` returned the true
sentence from page 16.

**Eight corrections went out the same day.** That is what this is for.
