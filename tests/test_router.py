import json
from types import SimpleNamespace

import psycopg
import pytest

import router
import sql_tools
from sql_tools import count_employees, get_leave_balance, get_payslip, run_tool


def database_available():
    if not sql_tools.READONLY_DATABASE_URL:
        return False
    try:
        psycopg.connect(sql_tools.READONLY_DATABASE_URL, connect_timeout=2).close()
        return True
    except psycopg.Error:
        return False


needs_database = pytest.mark.skipif(not database_available(), reason="hr_db is not set up")


@pytest.mark.parametrize(
    "call, message",
    [
        (lambda: get_leave_balance("E001'; DROP TABLE leaves; --"), "emp_id must look like E001"),
        (lambda: get_leave_balance(1), "emp_id must look like E001"),
        (lambda: get_payslip("E001", "March"), "month must look like 2026-02"),
        (lambda: count_employees("Engineering; DELETE FROM employees"), "department must be one of"),
    ],
)
def test_bad_arguments_never_reach_the_database(call, message):
    assert message in call()["error"]


def test_run_tool_handles_unknown_tools_and_bad_arguments():
    assert run_tool("drop_tables", "{}") == {"error": "Unknown tool: drop_tables"}
    assert run_tool("get_payslip", '{"emp_id": "E001"}') == {"error": "Wrong arguments for get_payslip"}
    assert run_tool("get_payslip", "not json") == {"error": "Wrong arguments for get_payslip"}


@needs_database
def test_tools_read_the_database():
    balances = {row["leave_type"]: row["days_left"] for row in get_leave_balance("E001")["balances"]}
    assert balances == {"Casual": 6, "Earned": 13, "Sick": 10}
    assert get_payslip("E003", "2026-02")["net_pay"] == 46000
    assert count_employees("Engineering") == {"department": "Engineering", "employees": 12}
    assert "no employee" in get_leave_balance("E999")["error"]


def reply(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def tool_call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


@pytest.fixture
def fake_model(monkeypatch):
    calls = []

    def setup(route, *answers):
        replies = [reply(route), *answers]

        def chat(messages, tools=None):
            calls.append({"messages": messages, "tools": tools})
            return replies[len(calls) - 1]

        monkeypatch.setattr(router, "chat", chat)
        monkeypatch.setattr(router, "search_policies", lambda question: [
            {"text": "Employees get 18 days of earned leave.", "source": "employee_handbook.pdf", "page": 3}])
        monkeypatch.setattr(router, "run_tool", lambda name, arguments: {"emp_id": "E001", "days_left": 13})
        return calls

    return setup


@pytest.mark.parametrize("model_reply, route", [("rag", "rag"), ("SQL", "sql"), ("both.", "both"), ("not sure", "both")])
def test_decide_route(monkeypatch, model_reply, route):
    monkeypatch.setattr(router, "chat", lambda messages, tools=None: reply(model_reply))
    assert router.decide_route("question") == route


def test_policy_question_uses_only_rag(fake_model):
    calls = fake_model("rag", reply("Employees get 18 days of earned leave."))

    result = router.answer_question("How many earned leave days do employees get?")

    assert result == {"route": "rag", "answer": "Employees get 18 days of earned leave.",
                      "sources": ["employee_handbook.pdf p.3"]}
    assert calls[1]["tools"] is None
    assert "18 days of earned leave" in calls[1]["messages"][0]["content"]


def test_data_question_uses_only_sql(fake_model):
    calls = fake_model("sql", reply(tool_calls=[tool_call("get_leave_balance", {"emp_id": "E001"})]),
                       reply("E001 has 13 earned leave days left."))

    result = router.answer_question("How many earned leave days does E001 have left?")

    assert result["route"] == "sql"
    assert result["sources"] == ["hr_db: get_leave_balance(E001)"]
    assert calls[1]["tools"] is not None
    assert "(none)" in calls[1]["messages"][0]["content"]


def test_mixed_question_uses_both(fake_model):
    fake_model("both", reply(tool_calls=[tool_call("get_leave_balance", {"emp_id": "E001"})]),
               reply("E001 has 13 days left, and up to 30 days can be carried forward."))

    result = router.answer_question("How many days does E001 have left, and can they be carried forward?")

    assert result["route"] == "both"
    assert result["sources"] == ["employee_handbook.pdf p.3", "hr_db: get_leave_balance(E001)"]
