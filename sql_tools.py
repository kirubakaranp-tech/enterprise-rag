import json
import os
import re

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

READONLY_DATABASE_URL = os.getenv("READONLY_DATABASE_URL", "")
DEPARTMENTS = ["Engineering", "Finance", "HR", "Marketing", "Sales", "Support"]


def connect_readonly():
    conn = psycopg.connect(READONLY_DATABASE_URL, connect_timeout=5, row_factory=dict_row)
    conn.read_only = True
    return conn


def get_leave_balance(emp_id):
    if not isinstance(emp_id, str) or not re.fullmatch(r"E\d{3}", emp_id):
        return {"error": "emp_id must look like E001"}
    with connect_readonly() as conn:
        rows = conn.execute(
            "SELECT leave_type, total_days, used_days, total_days - used_days AS days_left "
            "FROM leaves WHERE emp_id = %s ORDER BY leave_type",
            (emp_id,),
        ).fetchall()
    if not rows:
        return {"error": f"There is no employee {emp_id}"}
    return {"emp_id": emp_id, "balances": rows}


def get_payslip(emp_id, month):
    if not isinstance(emp_id, str) or not re.fullmatch(r"E\d{3}", emp_id):
        return {"error": "emp_id must look like E001"}
    if not isinstance(month, str) or not re.fullmatch(r"\d{4}-\d{2}", month):
        return {"error": "month must look like 2026-02"}
    with connect_readonly() as conn:
        row = conn.execute(
            "SELECT emp_id, month, gross_pay, deductions, net_pay FROM payslips WHERE emp_id = %s AND month = %s",
            (emp_id, month),
        ).fetchone()
    if row is None:
        return {"error": f"There is no payslip for {emp_id} in {month}"}
    return row


def count_employees(department):
    if department not in DEPARTMENTS:
        return {"error": f"department must be one of {DEPARTMENTS}"}
    with connect_readonly() as conn:
        row = conn.execute("SELECT count(*) AS employees FROM employees WHERE department = %s", (department,)).fetchone()
    return {"department": department, "employees": row["employees"]}


TOOL_FUNCTIONS = {
    "get_leave_balance": get_leave_balance,
    "get_payslip": get_payslip,
    "count_employees": count_employees,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_leave_balance",
            "description": "Get how many days of each leave type one employee has left.",
            "parameters": {
                "type": "object",
                "properties": {"emp_id": {"type": "string", "description": "Employee id like E001"}},
                "required": ["emp_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_payslip",
            "description": "Get one employee's payslip for one month: gross pay, deductions and net pay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_id": {"type": "string", "description": "Employee id like E001"},
                    "month": {"type": "string", "description": "Month like 2026-02"},
                },
                "required": ["emp_id", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_employees",
            "description": "Count the employees in one department.",
            "parameters": {
                "type": "object",
                "properties": {"department": {"type": "string", "enum": DEPARTMENTS}},
                "required": ["department"],
            },
        },
    },
]


def run_tool(name, arguments_text):
    if name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {name}"}
    try:
        arguments = json.loads(arguments_text or "{}")
        return TOOL_FUNCTIONS[name](**arguments)
    except (json.JSONDecodeError, TypeError):
        return {"error": f"Wrong arguments for {name}"}
