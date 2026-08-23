# Grounding a retrieval pipeline

Retrieval answers *"which document"*. It does not answer *"did the model actually
read it"*, and those are different questions with different failure modes.

## Where the drift happens

A typical pipeline retrieves a passage, puts it in the prompt, and generates an
answer. The answer is usually faithful. **When it is not, nothing downstream
notices**, because the retrieval step succeeded and the generation step returned
text.

**Check the output against the passage that was actually supplied**, not against
the corpus:

```python
supplied = Source(name=chunk_id, text=retrieved_chunk)

for quotation in extract_quotations(answer):
    if supplied.find(quotation) is None:
        # The model quoted something that is not in what it was given.
        flag(quotation)
```

## Why check against the chunk rather than the corpus

Because a quotation found *somewhere else in the corpus* is still wrong. The model
was given one passage; if its quotation comes from a different one, the citation is
misattributed even though the words exist. **Verifying against the corpus would
pass it.**

## Order of operations

**Search, then quote — never guess, then confirm.** Ask the document for its own
wording and let the model use that:

```python
for hit in supplied.search("monthly demand charge"):
    print(hit.cite(), hit.text)      # verbatim, with its locator
```

A guessed quotation gets refused for reasons that have nothing to do with truth.
