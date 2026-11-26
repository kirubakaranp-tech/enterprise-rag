import search_baselines
from ingest import ingest_all
from search_baselines import BM25Index, bm25_search, is_hit, tokenize, vector_search


def test_tokenize_keeps_codes_and_ids_together():
    assert tokenize("Policy HR-204 for employee E047 (2026-07-26).") == ["policy", "hr-204", "for", "employee", "e047", "2026-07-26"]


def test_bm25_finds_an_exact_code():
    chunks = [
        {"id": "a", "text": "HR-204 Leave Policy owned by the People team", "source": "register"},
        {"id": "b", "text": "Annual leave can be carried forward up to 30 days", "source": "handbook"},
        {"id": "c", "text": "IT-117 Password Policy owned by IT Security", "source": "register"},
    ]
    results = BM25Index(chunks).search("What is HR-204?", k=1)
    assert results[0]["id"] == "a"


def test_is_hit_needs_the_right_source_and_text():
    results = [{"source": "employees.csv", "text": "Employee Karthik (E047) works in Engineering."}]
    assert is_hit(results, "employees.csv", "(E047)")
    assert not is_hit(results, "leave_records.csv", "(E047)")
    assert not is_hit(results, "employees.csv", "(E048)")


def test_both_searches_return_top_3_from_the_index(data, monkeypatch):
    ingest_all()
    monkeypatch.setattr(search_baselines, "_index", None)

    bm25 = bm25_search("What is policy HR-204 about?")
    vector = vector_search("What is policy HR-204 about?")

    assert len(bm25) == len(vector) == 3
    assert bm25[0]["source"] == "policy_register.pdf"
    assert "HR-204" in bm25[0]["text"]
    assert {"id", "text", "source"} <= set(vector[0])


def test_every_expected_answer_is_inside_one_chunk(data, monkeypatch):
    ingest_all()
    chunks = search_baselines.load_chunks()
    for _, _, source, must_contain in search_baselines.QUESTIONS:
        assert any(chunk["source"] == source and must_contain in chunk["text"] for chunk in chunks), must_contain
