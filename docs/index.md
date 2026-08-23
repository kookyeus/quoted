# Using `quoted`

Four pages, one problem each. Every example is runnable against the library or the
service, and **none of them claims an integration that does not exist** — there is
no framework plugin here, only plain Python and plain HTTP, which is all this needs.

| Page | The problem it solves |
|---|---|
| [Verifying what a model quotes](verifying-model-quotations.md) | A model cites a source it did not read |
| [Grounding a retrieval pipeline](grounding-retrieval.md) | Retrieval found the right document and the answer still drifted |
| [Reading regulatory documents](regulatory-documents.md) | Filed PDFs contain markers, headers and line numbers that break naive matching |
| [Refusals that are useful](useful-refusals.md) | "Not found" makes the caller guess again |

**The one idea underneath all four:** a claim is worth exactly what its source says,
and a system that cannot show the source should say so rather than produce
something shaped like an answer.
