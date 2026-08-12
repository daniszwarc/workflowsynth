import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

print("=== Anthropic ===")
claude = ChatAnthropic(
    model="claude-opus-4-6",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=50,
)
response = claude.invoke([HumanMessage(content="Reply with only: OK")])
print(f"Content: {response.content}")
print(f"Response metadata: {response.response_metadata}")

print()
print("=== OpenAI ===")
gpt = ChatOpenAI(
    model="gpt-5.4-2026-03-05",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=50,
)
response = gpt.invoke([HumanMessage(content="Reply with only: OK")])
print(f"Content: {response.content}")
print(f"Response metadata: {response.response_metadata}")
