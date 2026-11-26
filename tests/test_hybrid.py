import pytest

import search_baselines
from hybrid_search import RRF_K, fuse, hybrid_search, pick_best_weight
from ingest import ingest_all


def chunk(chunk_id):
    return {"id": chunk_id, "text": chunk_id, "source": "test"}


BM25 = [chunk("a"), chunk("b"), chunk("c")]
VECTOR = [chunk("c"), chunk("d"), chunk("a")]


def ids(results):
    return [result["id"] for result in results]


def test_equal_weight_is_plain_reciprocal_rank_fusion():
    scores = {
        "a": 1 / (RRF_K + 1) + 1 / (RRF_K + 3),
        "b": 1 / (RRF_K + 2),
        "c": 1 / (RRF_K + 3) + 1 / (RRF_K + 1),
        "d": 1 / (RRF_K + 2),
    }
    expected = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)[:3]
    assert ids(fuse(BM25, VECTOR, k=3, weight=0.5)) == expected


def test_chunks_found_by_both_methods_come_first():
    assert set(ids(fuse(BM25, VECTOR, k=2, weight=0.5))) == {"a", "c"}


def test_weight_1_is_bm25_and_weight_0_is_vector():
    assert ids(fuse(BM25, VECTOR, k=3, weight=1.0)) == ["a", "b", "c"]
    assert ids(fuse(BM25, VECTOR, k=3, weight=0.0)) == ["c", "d", "a"]


def test_higher_weight_moves_bm25_results_up():
    assert ids(fuse(BM25, VECTOR, k=1, weight=0.9)) == ["a"]
    assert ids(fuse(BM25, VECTOR, k=1, weight=0.1)) == ["c"]


@pytest.mark.parametrize(
    "hits, best",
    [({0.0: 7, 0.5: 9, 1.0: 6}, 0.5), ({0.3: 9, 0.5: 8, 0.7: 9}, 0.3), ({0.2: 8, 0.6: 8}, 0.6)],
)
def test_pick_best_weight_prefers_the_most_balanced_of_the_best(hits, best):
    assert pick_best_weight(hits) == best


def test_hybrid_search_on_the_real_index(data, monkeypatch):
    ingest_all()
    monkeypatch.setattr(search_baselines, "_index", None)
    results = hybrid_search("What is policy HR-204 about?", k=3, weight=0.5)
    assert len(results) == 3
    assert any("HR-204" in result["text"] for result in results)
