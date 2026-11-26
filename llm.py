import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def chat(messages, tools=None):
    client = OpenAI(max_retries=5)
    options = {"model": MODEL, "messages": messages, "temperature": 0}
    if tools:
        options["tools"] = tools
    return client.chat.completions.create(**options).choices[0].message
