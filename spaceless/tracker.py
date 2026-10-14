"""Remember the letters typed since the last break and decide when to rewrite them."""

import string

LETTERS = set(string.ascii_letters + "'")
TRIGGERS = set(" .,!?;:")


class Tracker:
    def __init__(self, splitter, min_length=4):
        self.splitter = splitter
        self.min_length = min_length
        self.run = ""

    def reset(self):
        self.run = ""

    def backspace(self):
        self.run = self.run[:-1]

    def char(self, ch):
        """Feed one typed character.

        Returns (backspaces, text) when the run just ended by `ch` should be
        erased and retyped as `text`, otherwise None.
        """
        if ch in LETTERS:
            self.run += ch
            return None
        run, self.run = self.run, ""
        if ch not in TRIGGERS or len(run) < self.min_length:
            return None
        fixed = self.splitter(run)
        if fixed is None:
            return None
        return len(run) + 1, fixed + ch
