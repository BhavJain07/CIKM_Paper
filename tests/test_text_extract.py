from provbench_rag.evaluation.text_extract import first_sentence


def test_first_sentence():
    s = first_sentence("Hello world. Second here.")
    assert "Hello world." in s or s.startswith("Hello")
