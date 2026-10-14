from spaceless.segment import split_run
from spaceless.tracker import Tracker


def feed(tracker, text):
    jobs = [tracker.char(ch) for ch in text]
    return [j for j in jobs if j]


def test_rewrites_on_space():
    t = Tracker(split_run)
    assert feed(t, "seeyoutomorrow ") == [(15, "see you tomorrow ")]


def test_rewrites_on_punctuation():
    t = Tracker(split_run)
    assert feed(t, "thankyouverymuch!") == [(17, "thank you very much!")]


def test_only_last_run_is_touched():
    t = Tracker(split_run)
    assert feed(t, "hello iamhere.") == [(8, "i am here.")]


def test_short_runs_ignored():
    t = Tracker(split_run, min_length=4)
    assert feed(t, "isa ") == []


def test_backspace_edits_run():
    t = Tracker(split_run)
    feed(t, "iamherex")
    t.backspace()
    assert t.char(" ") == (8, "i am here ")


def test_reset_drops_run():
    t = Tracker(split_run)
    feed(t, "iamhere")
    t.reset()
    assert t.char(" ") is None


def test_digits_break_run():
    t = Tracker(split_run)
    assert feed(t, "iamhere2 ") == []
