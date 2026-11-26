# Enterprise RAG

A RAG pipeline for company knowledge from three kinds of sources. Work happens on the
`feature/enterprise-rag` branch.

## Multi-source ingestion

| Source | Files | How it is read | One chunk per |
|---|---|---|---|
| PDF policies | `data/pdfs/employee_handbook.pdf` (12 pages), `hr_compensation_policy.pdf` (5 pages), `it_security_policy.pdf` (6 pages) | PyMuPDF, page by page, with the section heading found by font size (Day 1) | about 300 characters of a page |
| CSV exports | `data/csv/employees.csv` (120 rows), `data/csv/leave_records.csv` (300 rows) | pandas, every row becomes a sentence | row |

CSV rows are turned into text that reads well for RAG, for example:

```
Employee Arun (E001) works in Sales, earns 30000 a month and joined on 2023-01-27.
Employee E019 took 1 day of Sick leave from 2026-09-10.
```

Empty cells are left out of the sentence instead of showing `nan`.

Every chunk is stored in Chroma (`chroma_db/`) with metadata:

| Source type | Metadata |
|---|---|
| PDF | `source`, `source_type`, `page`, `section`, `created` |
| CSV | `source`, `source_type`, `row`, `created` |

### Incremental indexing

`index_registry.json` keeps the sha256 hash of every file (Day 2). A file is only indexed again when
its hash changes; its old chunks are deleted first, so there are no duplicates. Unchanged files are
skipped and only get a new `last_synced_at`.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

```
python ingest.py
```

The first run downloads the embedding model (about 80 MB) if it is not on your PC yet.

First run:

```
PDF: 3 files, 67 chunks
CSV: 2 files, 420 chunks
Skipped (unchanged): 0 | Time: ...
```

Second run, with no changes:

```
PDF: 0 files, 0 chunks
CSV: 0 files, 0 chunks
Skipped (unchanged): 5 | Time: 0s
```

## Project structure

```
data/pdfs/         the 3 policy PDFs
data/csv/          the 2 CSV exports
pdf_loader.py      reads a PDF page by page with its section heading
csv_loader.py      turns CSV rows into sentences
chunking.py        splits text into chunks
registry.py        sha256 hashes and index_registry.json
vector_store.py    saves chunks in Chroma
ingest.py          runs everything and prints the summary
tests/             tests with a fake embedding model
```

## Tests

```
python -m pytest
```
