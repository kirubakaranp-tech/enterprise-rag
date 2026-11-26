import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

load_dotenv()

DATABASE_NAME = "hr_db"
READONLY_USER = "hr_readonly"
LEAVE_DAYS = {"Earned": 18, "Sick": 10, "Casual": 6}
MONTHS = ["2026-01", "2026-02", "2026-03"]


def load_data(conn):
    employees = pd.read_csv("data/csv/employees.csv")
    leave_records = pd.read_csv("data/csv/leave_records.csv")
    used = leave_records.groupby(["employee_id", "leave_type"])["days"].sum()

    for _, row in employees.iterrows():
        joining_date = None if pd.isna(row["joining_date"]) else row["joining_date"]
        conn.execute("INSERT INTO employees VALUES (%s, %s, %s, %s)",
                     (row["employee_id"], row["name"], row["department"], joining_date))

        for leave_type, total in LEAVE_DAYS.items():
            used_days = int(used.get((row["employee_id"], leave_type), 0))
            conn.execute("INSERT INTO leaves VALUES (%s, %s, %s, %s)",
                         (row["employee_id"], leave_type, total, min(used_days, total)))

        if pd.isna(row["salary"]):
            continue
        gross = int(row["salary"])
        deductions = round(gross * 0.12) + 200
        for month in MONTHS:
            conn.execute("INSERT INTO payslips VALUES (%s, %s, %s, %s, %s)",
                         (row["employee_id"], month, gross, deductions, gross - deductions))
    return len(employees)


def main():
    admin_url = os.getenv("DATABASE_ADMIN_URL")
    readonly_url = os.getenv("READONLY_DATABASE_URL")
    if not admin_url or not readonly_url:
        print("Please set DATABASE_ADMIN_URL and READONLY_DATABASE_URL in your .env file first.")
        return
    password = conninfo_to_dict(readonly_url).get("password")
    if not password or password == "CHOOSE_A_PASSWORD":
        print("Please choose a password for the read-only user in READONLY_DATABASE_URL.")
        return

    with psycopg.connect(admin_url, autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE_NAME,)).fetchone():
            conn.execute(f"CREATE DATABASE {DATABASE_NAME}")
            print(f"Created database {DATABASE_NAME}")

    with psycopg.connect(make_conninfo(admin_url, dbname=DATABASE_NAME), autocommit=True) as conn:
        conn.execute(Path("sql/hr_db.sql").read_text(encoding="utf-8"))
        count = load_data(conn)
        print(f"Loaded {count} employees with leave balances and payslips for {', '.join(MONTHS)}")

        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (READONLY_USER,)).fetchone()
        command = "ALTER ROLE {} LOGIN PASSWORD {}" if exists else "CREATE ROLE {} LOGIN PASSWORD {}"
        conn.execute(sql.SQL(command).format(sql.Identifier(READONLY_USER), sql.Literal(password)))
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(DATABASE_NAME), sql.Identifier(READONLY_USER)))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(READONLY_USER)))
        conn.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(READONLY_USER)))
        conn.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(sql.Identifier(READONLY_USER)))
        print(f"User {READONLY_USER} can only read")


if __name__ == "__main__":
    main()
