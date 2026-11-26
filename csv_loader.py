from pathlib import Path

import pandas as pd


def clean_row(row):
    clean = {}
    for column, value in row.items():
        if pd.isna(value):
            clean[column] = None
        elif isinstance(value, float) and value.is_integer():
            clean[column] = int(value)
        else:
            clean[column] = value
    return clean


def employee_sentence(row):
    name = row["name"] or "An employee"
    department = row["department"] or "an unknown department"
    sentence = f"Employee {name} ({row['employee_id']}) works in {department}"
    if row["salary"] is not None:
        sentence += f", earns {row['salary']} a month"
    if row["joining_date"] is not None:
        sentence += f" and joined on {row['joining_date']}"
    return sentence + "."


def leave_sentence(row):
    if row["days"] is None:
        return f"Employee {row['employee_id']} took {row['leave_type']} leave from {row['start_date']} (days not recorded)."
    day_word = "day" if row["days"] == 1 else "days"
    return f"Employee {row['employee_id']} took {row['days']} {day_word} of {row['leave_type']} leave from {row['start_date']}."


def generic_sentence(file_name, row):
    parts = [f"{column} is {value}" for column, value in row.items() if value is not None]
    return f"{file_name}: " + ", ".join(parts) + "."


SENTENCE_BUILDERS = {
    "employees.csv": employee_sentence,
    "leave_records.csv": leave_sentence,
}


def load_csv(path):
    path = Path(path)
    table = pd.read_csv(path)
    builder = SENTENCE_BUILDERS.get(path.name)

    rows = []
    for index, row in table.iterrows():
        row = clean_row(row)
        text = builder(row) if builder else generic_sentence(path.stem, row)
        rows.append({"text": text, "row": index + 2})
    return rows
