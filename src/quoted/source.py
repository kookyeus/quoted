"""A document you can quote from, and cannot quote beyond."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .claim import Claim, NotFound, Unreadable
from .normalise import normalise

_PAGE = re.compile(r"\f|<<<\s*PAGE\s+(\d+)\s*>>>", re.I)


@dataclass
class Source:
    """Text with a name, searchable, and honest about what it does not contain.

    **Construct it from text you already have.** This library deliberately does
    not bundle PDF extraction — extraction is somebody else's problem and a
    dependency you should choose yourself. `from_file` handles plain text;
    anything else, extract it your own way and pass the string.
    """

    name: str
    text: str
    _pages: list[tuple[int, int, str]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise Unreadable(f"{self.name} is empty — nothing can be quoted from it")
        self._index_pages()

    # --- construction ---------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path, encoding: str = "utf-8") -> "Source":
        p = Path(path)
        try:
            return cls(name=p.name, text=p.read_text(encoding, errors="replace"))
        except OSError as e:
            raise Unreadable(f"{p.name} could not be read: {e}") from e

    @classmethod
    def from_pages(cls, name: str, pages: list[str]) -> "Source":
        """Build from a list of page strings, so locators are exact."""
        joined = "".join(f"<<<PAGE {i+1}>>>\n{p}\n" for i, p in enumerate(pages))
        return cls(name=name, text=joined)

    # --- the whole point ------------------------------------------------------

    def find(self, quote: str) -> Claim | None:
        """Return a Claim **only if** the words are genuinely in this document.

        Typography is ignored; wording is not. If the passage is absent this
        returns `None` and the caller has nothing to assert.
        """
        if not quote or not quote.strip():
            return None
        at = normalise(self.text).find(normalise(quote))
        if at < 0:
            return None
        raw_at = self._raw_offset(quote)
        return Claim(text=self._verbatim(quote, raw_at) or quote.strip(),
                     document=self.name,
                     locator=self.locator_at(raw_at),
                     query=quote.strip())

    def must_find(self, quote: str) -> Claim:
        """As `find`, but raises rather than returning nothing.

        **Use this where absence must not be mistaken for silence.** The
        difference matters: a caller that receives `None` may quietly move on,
        and that is how a system reports "nothing found" when it never looked.
        """
        c = self.find(quote)
        if c is None:
            raise NotFound(f"{self.name} does not contain: {quote.strip()[:80]!r}")
        return c

    def search(self, term: str, window: int = 400) -> list[Claim]:
        """Every passage around `term`, each one a verified Claim."""
        out, low, t = [], normalise(self.text), normalise(term)
        if not t:
            return out
        start = 0
        while True:
            i = low.find(t, start)
            if i < 0:
                break
            raw = self._raw_offset_at(i)
            a, b = max(0, raw - window // 3), min(len(self.text), raw + window)
            passage = re.sub(r"\s+", " ", self.text[a:b]).strip()
            out.append(Claim(text=passage, document=self.name,
                             locator=self.locator_at(raw), query=term))
            start = i + max(1, len(t))
        return out

    # --- locating -------------------------------------------------------------

    def _index_pages(self) -> None:
        marks = [(m.start(), m.group(1)) for m in _PAGE.finditer(self.text)]
        if not marks:
            self._pages = [(0, len(self.text), "whole document")]
            return
        for n, (pos, num) in enumerate(marks):
            end = marks[n + 1][0] if n + 1 < len(marks) else len(self.text)
            label = f"page {num}" if num else f"page {n + 1}"
            self._pages.append((pos, end, label))

    def locator_at(self, offset: int) -> str:
        for a, b, label in self._pages:
            if a <= offset < b:
                return label
        return "location not identified"

    def _raw_offset(self, quote: str) -> int:
        return self._raw_offset_at(normalise(self.text).find(normalise(quote)))

    def _raw_offset_at(self, norm_index: int) -> int:
        """Map a normalised index back to roughly where it sits in the original.

        Approximate by design — it drives a page label, never a claim's truth.
        """
        if norm_index < 0:
            return 0
        ratio = norm_index / max(1, len(normalise(self.text)))
        return min(len(self.text) - 1, int(ratio * len(self.text)))

    def _verbatim(self, quote: str, near: int) -> str | None:
        """Recover the original spelling of a passage found by normalised match."""
        span = len(quote) * 2 + 40
        a, b = max(0, near - span), min(len(self.text), near + span)
        window = self.text[a:b]
        n_q = normalise(quote)
        for size in (len(quote), len(quote) + 10, len(quote) + 30):
            for i in range(max(0, len(window) - size)):
                if normalise(window[i:i + size]) == n_q:
                    return re.sub(r"\s+", " ", window[i:i + size]).strip()
        return None

    def __repr__(self) -> str:
        return f"<Source {self.name!r} {len(self.text):,} chars, {len(self._pages)} page(s)>"
