"""Compare on the words, not the typography.

**A verifier that fails on a dash is worse than none**, because it teaches you
to distrust the one signal that matters.

This exists because of a real failure. A model was handed the phrase
"15-minute demand", quoted it back correctly, and used a non-breaking hyphen.
A naive substring check called a correctly quoted, properly sourced answer
unverified. The verifier was checking the font.

PDF extraction, word processors and language models disagree constantly about
hyphens, quotation marks, ligatures and whitespace. None of those disagreements
change what was said.
"""

from __future__ import annotations

import re
import unicodedata

_DASHES = "‐‑‒–—―−－"
_SINGLES = "‘’‚‛′´`"
_DOUBLES = "“”„‟″"
_SPACES = "        　"

_MAP = {
    **{ord(c): "-" for c in _DASHES},
    **{ord(c): "'" for c in _SINGLES},
    **{ord(c): '"' for c in _DOUBLES},
    **{ord(c): " " for c in _SPACES},
    0x00AD: "",          # soft hyphen — invisible, and fatal to matching
    0x200B: "",          # zero-width space
    0xFEFF: "",          # byte-order mark
}

_LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
              "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st"}


def normalise(text: str) -> str:
    """Reduce text to the form in which two quotations can be compared.

    Case-folded, ligatures expanded, punctuation regularised, whitespace
    collapsed. **Nothing here changes which words were said** — that is the
    line, and anything that would cross it does not belong in this function.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    for lig, plain in _LIGATURES.items():
        t = t.replace(lig, plain)
    t = t.translate(_MAP)
    t = re.sub(r"\s+", " ", t)
    return t.strip().casefold()


def contains(haystack: str, needle: str) -> bool:
    """Is `needle` genuinely present in `haystack`, ignoring typography?"""
    n = normalise(needle)
    return bool(n) and n in normalise(haystack)


def locate(haystack: str, needle: str) -> int:
    """Where `needle` starts in the *normalised* haystack, or -1."""
    n = normalise(needle)
    return normalise(haystack).find(n) if n else -1
