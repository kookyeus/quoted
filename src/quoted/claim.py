"""A claim that cannot exist unless its words are really in the source."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Claim:
    """Something asserted, with the evidence attached.

    **There is no public constructor that skips verification.** A `Claim` is
    returned by `Source.find()` only when the quoted text was located in the
    document, and it carries where it was found. If the passage is not there,
    `find()` returns `None` and the caller has nothing to assert.

    That is the whole library. Everything else is machinery in service of it.
    """

    text: str
    """The passage, verbatim from the document."""

    document: str
    """Which document it came from."""

    locator: str
    """Where inside it — page, sheet, section, or line."""

    query: str
    """What was asked for, kept so the claim can be audited later."""

    def cite(self) -> str:
        return f"{self.document} · {self.locator}"

    def __str__(self) -> str:
        return f'"{self.text}" — {self.cite()}'


class NotFound(Exception):
    """Raised by `must_find` when the passage is not in the document.

    **Two ways to ask, deliberately.** `find()` returns `None` so a caller can
    handle absence; `must_find()` raises so absence cannot be silently treated
    as an empty result.

    The second exists because of a real failure: a monitor that lost permission
    to read a mailbox returned an empty list, and the caller reported "no
    replies" — in the same words it used when it had genuinely looked and found
    none. **A failure that looks like a finding is worse than a crash.**
    """


class Unreadable(Exception):
    """The source could not be read at all.

    Distinct from `NotFound` on purpose. *"I looked and it is not there"* and
    *"I could not look"* are different facts, and collapsing them is how a
    blind system reports silence.
    """
