import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from vector_store import get_collection

RESULTS_FILE = Path("results") / "retrieval_comparison.md"
TOP_K = 3

QUESTIONS = [
    ("keyword", "What is policy HR-204 about?", "policy_register.pdf", "HR-204"),
    ("keyword", "Who owns IT-117?", "policy_register.pdf", "IT-117"),
    ("keyword", "Show the details of employee E047", "employees.csv", "(E047)"),
    ("keyword", "Which leave did E118 take on 2026-07-26?", "leave_records.csv", "E118 took 1 day of Earned leave from 2026-07-26"),
    ("keyword", "Do company laptops use BitLocker?", "it_security_policy.pdf", "BitLocker"),
    ("meaning", "Can I keep my unused vacation days for next year?", "employee_handbook.pdf", "up to 30 days"),
    ("meaning", "What should I do if I fell for a fake email?", "it_security_policy.pdf", "Report Phishing"),
    ("meaning", "How much more money do I get when I am promoted?", "hr_compensation_policy.pdf", "Promotions get an extra increase"),
    ("meaning", "Am I allowed to work from my hometown for a few weeks?", "employee_handbook.pdf", "another city in India"),
    ("meaning", "What happens if I keep coming to the office late?", "employee_handbook.pdf", "after 10:30 am three times"),
]


def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


def load_chunks():
    stored = get_collection().get(include=["documents", "metadatas"])
    chunks = []
    for chunk_id, text, metadata in zip(stored["ids"], stored["documents"], stored["metadatas"]):
        chunks.append({"id": chunk_id, "text": text, "source": metadata["source"]})
    return chunks


class BM25Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(chunk["text"]) for chunk in chunks])

    def search(self, query, k=TOP_K):
        scores = self.bm25.get_scores(tokenize(query))
        best = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:k]
        return [self.chunks[index] for index in best]


_index = None


def bm25_search(query, k=TOP_K):
    global _index
    if _index is None:
        _index = BM25Index(load_chunks())
    return _index.search(query, k)


def vector_search(query, k=TOP_K):
    results = get_collection().query(query_texts=[query], n_results=k)
    chunks = []
    for chunk_id, text, metadata in zip(results["ids"][0], results["documents"][0], results["metadatas"][0]):
        chunks.append({"id": chunk_id, "text": text, "source": metadata["source"]})
    return chunks


def is_hit(results, source, must_contain):
    return any(chunk["source"] == source and must_contain in chunk["text"] for chunk in results)


def main():
    rows = []
    for kind, question, source, must_contain in QUESTIONS:
        bm25_hit = is_hit(bm25_search(question), source, must_contain)
        vector_hit = is_hit(vector_search(question), source, must_contain)
        rows.append((kind, question, bm25_hit, vector_hit))
        print(f"{'Y' if bm25_hit else 'N'} | {'Y' if vector_hit else 'N'} | {kind:7} | {question}")

    bm25_total = sum(row[2] for row in rows)
    vector_total = sum(row[3] for row in rows)
    print(f"\nBM25: {bm25_total}/{len(rows)} | Vector: {vector_total}/{len(rows)}")

    lines = ["# BM25 vs vector search", "",
             f"A hit means the chunk with the answer is in the top {TOP_K}.", "",
             f"BM25: {bm25_total}/{len(rows)} | Vector: {vector_total}/{len(rows)}", "",
             "| Question | Type | BM25 hit (Y/N) | Vector hit (Y/N) |", "|---|---|---|---|"]
    for kind, question, bm25_hit, vector_hit in rows:
        lines.append(f"| {question} | {kind} | {'Y' if bm25_hit else 'N'} | {'Y' if vector_hit else 'N'} |")
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved the table in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
