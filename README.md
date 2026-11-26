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

## SQL tools and question routing

### Mock HR database

`setup_db.py` creates the PostgreSQL database `hr_db` from the two CSV files, so the numbers match:

| Table | What is in it |
|---|---|
| `employees` | id, name, department and joining date of the 120 employees |
| `leaves` | for every employee: Earned 18, Sick 10 and Casual 6 days, minus the days used in `leave_records.csv` |
| `payslips` | gross pay, deductions and net pay for 2026-01, 2026-02 and 2026-03 |

It also creates the user `hr_readonly`, which can only read.

### Three safe tools (`sql_tools.py`)

| Tool | Checks before the query runs |
|---|---|
| `get_leave_balance(emp_id)` | `emp_id` must look like `E001` |
| `get_payslip(emp_id, month)` | `emp_id` like `E001`, `month` like `2026-02` |
| `count_employees(department)` | one of the 6 departments |

Every tool runs one fixed query with placeholders on a read-only connection. A bad value never
reaches the database, and an unknown tool name returns an error instead of running anything.

### The router (`router.py`)

1. The model first decides the route with one word:
   - **rag** for a question about policies, answered from the PDF chunks in Chroma
   - **sql** for a question about specific data, answered with the tools
   - **both** for a question that needs a rule and data
2. For `rag` and `both`, the 3 best PDF chunks are added to the prompt.
3. For `sql` and `both`, the model gets the 3 tools and calls the ones it needs.
4. The answer comes only from the chunks and the tool results, otherwise `I don't know.`
5. The sources are printed for every answer, for example
   `employee_handbook.pdf p.3, hr_db: get_leave_balance(E001)`.

### Evaluation

`eval_router.py` asks 8 questions (3 policy, 3 data, 2 mixed) and saves the table
`Question | Route chosen | Correct route (Y/N) | Answer correct (Y/N)` with the answers and sources in
`results/router_eval.md`. The expected numbers for the data questions are read from the
database, so the check always matches the data.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`: the Groq key, your PostgreSQL admin password, and a new password for `hr_readonly`.

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

Then the router:

```
python setup_db.py
python router.py "How many earned leave days does E001 have left?"
python eval_router.py
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
sql/hr_db.sql      the tables of the mock HR database
setup_db.py        creates hr_db from the CSV files and the read-only user
sql_tools.py       the 3 safe SQL tools
rag_search.py      finds the best policy chunks
router.py          chooses rag, sql or both and writes the answer with sources
eval_router.py     tests 8 questions and saves the results table
tests/             tests with a fake embedding model
```

## Tests

```
python -m pytest
```
