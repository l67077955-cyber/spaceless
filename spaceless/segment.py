"""Turn a run of letters typed without spaces into spaced words."""

import math

import wordninja

# wordninja ships a frequency-ranked English word list; cost = log(rank * log N)
_COST = wordninja.DEFAULT_LANGUAGE_MODEL._wordcost
_LOG_N = math.log(len(_COST))

# Only fairly common words may appear in a split. The long tail of the list
# holds junk like "thankyou", "iam", "icl", which make bad splits, and typos
# then find no split at all, so the run is left as typed.
MAX_RANK = 30000
MAX_RANK_TWO_LETTERS = 10000
SINGLE_LETTER_WORDS = {"a", "i"}
# A run that is itself a word at least this common is never split.
KNOWN_WORD_RANK = 60000


def _rank(word):
    cost = _COST.get(word)
    return None if cost is None else math.exp(cost) / _LOG_N - 1


def _allowed(word):
    rank = _rank(word)
    if rank is None:
        return False
    if len(word) == 1:
        return word in SINGLE_LETTER_WORDS
    if len(word) == 2:
        return rank <= MAX_RANK_TWO_LETTERS
    return rank <= MAX_RANK


_VOCAB = {w: c for w, c in _COST.items() if _allowed(w)}
_MAX_LEN = max(map(len, _VOCAB))
# cost of a user-supplied word: as cheap as a fairly common word
_EXTRA_WORD_COST = math.log(1000 * _LOG_N)

# Long runs may keep a few unknown chunks (typos, names) as they are, as long
# as most of the letters belong to real words.
UNKNOWN_MIN_RUN = 12
UNKNOWN_MIN_CHUNK = 3
UNKNOWN_BASE_COST = 5.0
UNKNOWN_LETTER_COST = 6.0
MIN_KNOWN_SHARE = 0.7


def _segment(s, extra, allow_unknown):
    """Cheapest split of `s` into words as [(piece, known)], or None if there is none."""
    best = [(0.0, 0, True)] + [(math.inf, 0, True)] * len(s)
    for end in range(1, len(s) + 1):
        for start in range(max(0, end - _MAX_LEN) if not allow_unknown else 0, end):
            piece = s[start:end]
            cost = _EXTRA_WORD_COST if piece in extra else _VOCAB.get(piece)
            known = cost is not None
            if not known:
                if not allow_unknown or len(piece) < UNKNOWN_MIN_CHUNK:
                    continue
                cost = UNKNOWN_BASE_COST + UNKNOWN_LETTER_COST * len(piece)
            if best[start][0] + cost < best[end][0]:
                best[end] = (best[start][0] + cost, start, known)
    if best[-1][0] == math.inf:
        return None
    pieces, end = [], len(s)
    while end:
        _, start, known = best[end]
        pieces.append((s[start:end], known))
        end = start
    return pieces[::-1]


def split_run(run, extra_words=frozenset()):
    """Return `run` with spaces between its words, or None to leave it as typed.

    `extra_words` (lower case) are never split themselves and count as known
    words inside a longer run.
    """
    lower = run.lower()
    if lower in extra_words:
        return None
    # camelCase is probably an identifier, not a sentence
    if any(c.isupper() for c in run[1:]) and not run.isupper():
        return None
    rank = _rank(lower)
    if rank is not None and rank <= KNOWN_WORD_RANK:
        return None
    pieces = _segment(lower, extra_words, allow_unknown=False)
    if pieces is None and len(run) >= UNKNOWN_MIN_RUN:
        pieces = _segment(lower, extra_words, allow_unknown=True)
        if pieces:
            known = sum(len(p) for p, k in pieces if k)
            if known / len(run) < MIN_KNOWN_SHARE:
                pieces = None
    if not pieces or len(pieces) < 2:
        return None
    # slice the original so the typed letter case survives
    words, i = [], 0
    for p, _ in pieces:
        words.append(run[i : i + len(p)])
        i += len(p)
    return " ".join(words)
