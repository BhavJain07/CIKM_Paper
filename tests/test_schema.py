from provbench_rag.schema import DocumentRecord


def test_document_roundtrip():
    raw = (
        '{"doc_id":"d","cluster_id":"c","source_url":"u","source_type":"t",'
        '"authority_level":3,"publication_date":null,"validity_start":null,"validity_end":null,'
        '"jurisdiction":null,"original_or_copy_label":"unknown","text":"hi",'
        '"paragraph_spans":[{"start":0,"end":2}]}'
    )
    d = DocumentRecord.model_validate_json(raw)
    assert d.doc_id == "d"
    assert d.paragraph_spans[0].end == 2
