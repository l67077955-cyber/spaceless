from spaceless.segment import split_run


def test_splits_plain_sentence():
    assert split_run("iwanttoknowaninputmethod") == "i want to know an input method"
    assert split_run("thequickbrownfox") == "the quick brown fox"
    assert split_run("thankyouverymuch") == "thank you very much"


def test_keeps_typed_case():
    assert split_run("Seeyoutomorrow") == "See you tomorrow"
    assert split_run("THANKSALOT") is not None


def test_single_words_untouched():
    for word in ["hello", "nowhere", "into", "cannot", "username"]:
        assert split_run(word) is None


def test_typos_untouched():
    assert split_run("atumaticlly") is None
    assert split_run("github") is None


def test_camel_case_untouched():
    assert split_run("getUserName") is None


def test_extra_words():
    assert split_run("localhost") == "local host"
    assert split_run("localhost", frozenset({"localhost"})) is None
    assert split_run("pushtogithubnow") == "push to git hub now"
    assert split_run("pushtogithubnow", frozenset({"github"})) == "push to github now"


def test_long_run_keeps_typos_in_place():
    assert (
        split_run("cnayouinventaappandpostonmygithb")
        == "cna you invent a app and post on my githb"
    )


def test_mostly_garbage_untouched():
    assert split_run("asdfghjklqwertyuiop") is None
