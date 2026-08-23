"""quoted — an assertion you cannot make without the words to back it.

    >>> from quoted import Source
    >>> doc = Source.from_pages("tariff.pdf", ["...on-peak demand is measured..."])
    >>> claim = doc.find("on-peak demand is measured")
    >>> print(claim)
    "on-peak demand is measured" — tariff.pdf · page 1

    >>> doc.find("on-peak demand is free") is None
    True

**If the words are not in the document, you get nothing to say.**
"""

from .claim import Claim, NotFound, Unreadable
from .normalise import contains, normalise
from .source import Source

__all__ = ["Source", "Claim", "NotFound", "Unreadable", "normalise", "contains"]
__version__ = "0.1.0"
