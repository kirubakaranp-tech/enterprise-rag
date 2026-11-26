import time
from pathlib import Path

from router import answer_question
from sql_tools import count_employees, get_leave_balance, get_payslip

RESULTS_FILE = Path("results") / "router_eval.md"
PAUSE_SECONDS = 5


def earned_left(emp_id):
    for balance in get_leave_balance(emp_id)["balances"]:
        if balance["leave_type"] == "Earned":
            return str(balance["days_left"])
    return "?"


def net_pay(emp_id, month):
    net = get_payslip(emp_id, month)["net_pay"]
    return f"{net:,}|{net}"


def build_questions():
    return [
        ("How many days of earned leave do full-time employees get each year?", "rag", ["18"]),
        ("What salary increase does an employee with a rating of 4 get?", "rag", ["9%|9 %|nine percent"]),
        ("How long must a password be?", "rag", ["14"]),
        ("How many earned leave days does E001 have left?", "sql", [earned_left("E001")]),
        ("What was the net pay of E003 in 2026-02?", "sql", [net_pay("E003", "2026-02")]),
        ("How many employees work in Engineering?", "sql", [str(count_employees("Engineering")["employees"])]),
        ("How many earned leave days does E001 have left, and can unused earned leave be carried forward?",
         "both", [earned_left("E001"), "30"]),
        ("What was the net pay of E002 in 2026-03, and on which day are salaries paid?",
         "both", [net_pay("E002", "2026-03"), "last working day"]),
    ]


def main():
    rows = []
    for number, (question, correct_route, expected) in enumerate(build_questions(), start=1):
        if number > 1:
            time.sleep(PAUSE_SECONDS)
        result = answer_question(question)

        route_ok = result["route"] == correct_route
        answer = result["answer"].lower()
        answer_ok = all(any(option.lower() in answer for option in fact.split("|")) for fact in expected)

        rows.append([question, result["route"], "Y" if route_ok else "N", "Y" if answer_ok else "N",
                     result["answer"], ", ".join(result["sources"]) or "-"])
        print(f"{number}. {question}")
        print(f"   route: {result['route']} (correct: {correct_route}) | answer correct: {'Y' if answer_ok else 'N'}")
        print(f"   answer: {result['answer']}")
        print(f"   sources: {', '.join(result['sources']) or 'none'}\n")

    routes = sum(row[2] == "Y" for row in rows)
    answers = sum(row[3] == "Y" for row in rows)
    print(f"Correct routes: {routes}/{len(rows)} | Correct answers: {answers}/{len(rows)}")

    lines = ["# Router evaluation", "", f"Correct routes: {routes}/{len(rows)} | Correct answers: {answers}/{len(rows)}", "",
             "| Question | Route chosen | Correct route (Y/N) | Answer correct (Y/N) | Answer | Sources |",
             "|---|---|---|---|---|---|"]
    for row in rows:
        lines.append("| " + " | ".join(" ".join(str(cell).split()).replace("|", "/") for cell in row) + " |")
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved the table in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
