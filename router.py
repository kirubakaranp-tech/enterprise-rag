import json
import sys

from llm import chat
from rag_search import search_policies
from sql_tools import TOOL_SCHEMAS, run_tool

ROUTES = ["rag", "sql", "both"]
MAX_TOOL_ROUNDS = 4

ROUTER_PROMPT = """Decide how to answer a question from an employee of Northwind Software.

- rag: the question is about company rules or policies, for example leave rules, salary revision rules,
  password rules or travel rules.
- sql: the question is about specific data in the HR database: one employee's leave balance or
  payslip, or how many employees work in a department.
- both: the question needs a policy rule AND specific employee data.

Reply with exactly one word: rag, sql or both.

Question: {question}"""

ANSWER_PROMPT = """You are the HR assistant of Northwind Software.
Answer only from the policy context below and from the results of the database tools.
If they do not contain the answer, reply with exactly: I don't know.
Answer in one to three short sentences.

Policy context:
{context}"""


def decide_route(question):
    reply = (chat([{"role": "user", "content": ROUTER_PROMPT.format(question=question)}]).content or "").strip().lower()
    for route in ROUTES:
        if reply.startswith(route):
            return route
    return "both"


def describe_call(name, arguments_text):
    try:
        values = json.loads(arguments_text or "{}").values()
    except (json.JSONDecodeError, AttributeError):
        values = []
    return f"{name}({', '.join(str(value) for value in values)})"


def answer_question(question):
    route = decide_route(question)
    sources = []

    chunks = search_policies(question) if route in ("rag", "both") else []
    for chunk in chunks:
        source = f"{chunk['source']} p.{chunk['page']}"
        if source not in sources:
            sources.append(source)

    context = "\n\n".join(f"[{chunk['source']} p.{chunk['page']}]\n{chunk['text']}" for chunk in chunks) or "(none)"
    messages = [
        {"role": "system", "content": ANSWER_PROMPT.format(context=context)},
        {"role": "user", "content": question},
    ]
    tools = TOOL_SCHEMAS if route in ("sql", "both") else None

    for _ in range(MAX_TOOL_ROUNDS):
        message = chat(messages, tools)
        if not message.tool_calls:
            answer = " ".join((message.content or "").split()) or "I don't know."
            return {"route": route, "answer": answer, "sources": sources}

        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {"id": call.id, "type": "function",
                 "function": {"name": call.function.name, "arguments": call.function.arguments}}
                for call in message.tool_calls
            ],
        })
        for call in message.tool_calls:
            result = run_tool(call.function.name, call.function.arguments)
            sources.append(f"hr_db: {describe_call(call.function.name, call.function.arguments)}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})

    return {"route": route, "answer": "Sorry, I could not finish the answer.", "sources": sources}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How many earned leave days does E001 have left?"
    result = answer_question(question)
    print(f"Question: {question}")
    print(f"Route: {result['route']}")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {', '.join(result['sources']) or 'none'}")
