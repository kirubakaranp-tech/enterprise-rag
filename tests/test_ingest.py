from chunking import split_into_chunks
from csv_loader import employee_sentence, leave_sentence, load_csv
from ingest import format_time, ingest_all
from pdf_loader import load_pdf
from vector_store import get_collection


def test_pdf_pages_keep_their_section():
    pages = load_pdf("data/pdfs/employee_handbook.pdf")
    assert len(pages) == 12
    assert pages[2]["section"] == "Leave Policy"
    assert pages[3]["section"] == "Leave Policy"


def test_csv_rows_become_sentences():
    rows = load_csv("data/csv/employees.csv")
    assert len(rows) == 120
    assert rows[0] == {"text": "Employee Arun (E001) works in Sales, earns 30000 a month and joined on 2023-01-27.", "row": 2}
    assert len(load_csv("data/csv/leave_records.csv")) == 300


def test_empty_cells_are_handled():
    row = {"employee_id": "E050", "name": "Ravi", "department": None, "salary": None, "joining_date": None}
    assert employee_sentence(row) == "Employee Ravi (E050) works in an unknown department."
    leave = {"employee_id": "E007", "leave_type": "Sick", "start_date": "2026-02-03", "days": None}
    assert leave_sentence(leave) == "Employee E007 took Sick leave from 2026-02-03 (days not recorded)."


def test_chunks_are_not_too_long():
    chunks = split_into_chunks("word " * 400, size=300, overlap=50)
    assert all(len(chunk) <= 300 for chunk in chunks)


def test_format_time():
    assert format_time(80) == "1m 20s"
    assert format_time(7.4) == "7s"


def test_first_run_indexes_every_source(data, capsys):
    summary, skipped = ingest_all()

    assert summary["PDF"]["files"] == 3
    assert summary["CSV"] == {"files": 2, "chunks": 420}
    assert skipped == 0
    output = capsys.readouterr().out
    assert "CSV: 2 files, 420 chunks" in output
    assert "Skipped (unchanged): 0 | Time:" in output

    collection = get_collection()
    assert collection.count() == summary["PDF"]["chunks"] + 420


def test_every_chunk_has_metadata(data):
    ingest_all()
    metadatas = get_collection().get(include=["metadatas"])["metadatas"]
    for metadata in metadatas:
        assert {"source", "source_type", "created"} <= set(metadata)
        if metadata["source_type"] == "pdf":
            assert {"page", "section"} <= set(metadata)
        else:
            assert "row" in metadata


def test_second_run_skips_unchanged_files(data, capsys):
    ingest_all()
    count = get_collection().count()

    summary, skipped = ingest_all()

    assert skipped == 5
    assert summary["PDF"] == {"files": 0, "chunks": 0}
    assert get_collection().count() == count


def test_changed_csv_is_reindexed_without_duplicates(data):
    ingest_all()
    leave_file = data / "csv" / "leave_records.csv"
    leave_file.write_text(leave_file.read_text(encoding="utf-8") + "E001,Casual,2026-11-20,1\n", encoding="utf-8")

    summary, skipped = ingest_all()

    assert skipped == 4
    assert summary["CSV"] == {"files": 1, "chunks": 301}
    assert len(get_collection().get(where={"source": "leave_records.csv"})["ids"]) == 301
