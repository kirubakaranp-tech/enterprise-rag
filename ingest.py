import time
from datetime import datetime
from pathlib import Path

import registry
import vector_store
from chunking import split_into_chunks
from csv_loader import load_csv
from pdf_loader import load_pdf

SOURCES = {
    "PDF": Path("data") / "pdfs",
    "CSV": Path("data") / "csv",
}


def pdf_chunks(path, created):
    chunks = []
    for page in load_pdf(path):
        for text in split_into_chunks(page["text"]):
            chunks.append({
                "id": f"{path.name}-{len(chunks)}",
                "text": text,
                "metadata": {
                    "source": path.name,
                    "source_type": "pdf",
                    "page": page["page"],
                    "section": page["section"] or "",
                    "created": created,
                },
            })
    return chunks


def csv_chunks(path, created):
    chunks = []
    for row in load_csv(path):
        chunks.append({
            "id": f"{path.name}-row{row['row']}",
            "text": row["text"],
            "metadata": {"source": path.name, "source_type": "csv", "row": row["row"], "created": created},
        })
    return chunks


def ingest_file(path, source_name):
    created = datetime.fromtimestamp(path.stat().st_ctime).strftime("%Y-%m-%d")
    if source_name == "PDF":
        return pdf_chunks(path, created)
    return csv_chunks(path, created)


def format_time(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


def ingest_all():
    start = time.perf_counter()
    entries = registry.load_registry()
    now = datetime.now().isoformat(timespec="seconds")
    summary = {}
    skipped = 0

    for source_name, folder in SOURCES.items():
        extension = f".{source_name.lower()}"
        files = sorted(path for path in folder.iterdir() if path.suffix.lower() == extension)
        summary[source_name] = {"files": 0, "chunks": 0}

        for path in files:
            if not registry.needs_reindex(path, entries):
                entries[path.name]["last_synced_at"] = now
                skipped += 1
                print(f"  {path.name}: unchanged -> skipped")
                continue

            chunks = ingest_file(path, source_name)
            vector_store.replace_chunks(path.name, chunks)
            entries[path.name] = {
                "hash": registry.file_hash(path),
                "file_name": path.name,
                "source_type": source_name.lower(),
                "chunks": len(chunks),
                "last_synced_at": now,
            }
            summary[source_name]["files"] += 1
            summary[source_name]["chunks"] += len(chunks)
            print(f"  {path.name}: indexed {len(chunks)} chunks")

    registry.save_registry(entries)
    seconds = time.perf_counter() - start

    print()
    for source_name, counts in summary.items():
        print(f"{source_name}: {counts['files']} files, {counts['chunks']} chunks")
    print(f"Skipped (unchanged): {skipped} | Time: {format_time(seconds)}")
    return summary, skipped


if __name__ == "__main__":
    ingest_all()
