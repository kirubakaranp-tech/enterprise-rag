from pathlib import Path

from search_baselines import QUESTIONS, TOP_K, bm25_search, is_hit, vector_search

RRF_K = 60
CANDIDATES = 20
WEIGHTS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]
RESULTS_FILE = Path("results") / "hybrid_comparison.md"


def fuse(bm25_results, vector_results, k=TOP_K, weight=0.5):
    scores = {}
    chunks = {}

    for rank, chunk in enumerate(bm25_results, start=1):
        scores[chunk["id"]] = scores.get(chunk["id"], 0) + weight / (RRF_K + rank)
        chunks[chunk["id"]] = chunk

    for rank, chunk in enumerate(vector_results, start=1):
        scores[chunk["id"]] = scores.get(chunk["id"], 0) + (1 - weight) / (RRF_K + rank)
        chunks[chunk["id"]] = chunk

    best_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)[:k]
    return [chunks[chunk_id] for chunk_id in best_ids]


def hybrid_search(query, k=TOP_K, weight=0.5):
    return fuse(bm25_search(query, CANDIDATES), vector_search(query, CANDIDATES), k, weight)


def pick_best_weight(hits_by_weight):
    best_score = max(hits_by_weight.values())
    best_weights = [weight for weight, hits in hits_by_weight.items() if hits == best_score]
    return min(best_weights, key=lambda weight: (round(abs(weight - 0.5), 6), weight))


def main():
    total = len(QUESTIONS)
    candidates = {}
    for _, question, _, _ in QUESTIONS:
        candidates[question] = (bm25_search(question, CANDIDATES), vector_search(question, CANDIDATES))

    hits_by_weight = {}
    for weight in WEIGHTS:
        hits = 0
        for _, question, source, must_contain in QUESTIONS:
            bm25_results, vector_results = candidates[question]
            if is_hit(fuse(bm25_results, vector_results, TOP_K, weight), source, must_contain):
                hits += 1
        hits_by_weight[weight] = hits
        print(f"weight {weight:.1f} (BM25 share) -> hybrid hit rate @3: {hits}/{total}")

    best_weight = pick_best_weight(hits_by_weight)

    rows = []
    for kind, question, source, must_contain in QUESTIONS:
        bm25_results, vector_results = candidates[question]
        rows.append((
            question,
            kind,
            is_hit(bm25_results[:TOP_K], source, must_contain),
            is_hit(vector_results[:TOP_K], source, must_contain),
            is_hit(fuse(bm25_results, vector_results, TOP_K, best_weight), source, must_contain),
        ))

    bm25_total = sum(row[2] for row in rows)
    vector_total = sum(row[3] for row in rows)
    hybrid_total = sum(row[4] for row in rows)
    summary = f"Hit rate @3 -> BM25: {bm25_total}/{total} | Vector: {vector_total}/{total} | Hybrid: {hybrid_total}/{total}"
    print(f"\nBest weight: {best_weight} (BM25 share)")
    print(summary)

    lines = ["# Hybrid search with reciprocal rank fusion", "", summary, "",
             f"Best weight: {best_weight} (share of BM25, the rest is vector).", "",
             "| Question | Type | BM25 | Vector | Hybrid |", "|---|---|---|---|---|"]
    for question, kind, bm25_hit, vector_hit, hybrid_hit in rows:
        marks = ["Y" if hit else "N" for hit in (bm25_hit, vector_hit, hybrid_hit)]
        lines.append(f"| {question} | {kind} | " + " | ".join(marks) + " |")
    lines += ["", "## Weight sweep", "", "| BM25 weight | Hybrid hits @3 |", "|---|---|"]
    for weight, hits in hits_by_weight.items():
        lines.append(f"| {weight:.1f} | {hits}/{total} |")
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved the tables in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
