from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

from email_agent.gmail_agent import GmailAgent

# 1. LLM and tools
llm = ChatOpenAI(model="gpt-4o-mini")
tools = [GmailAgent]

# 2. Memory (shared for full conversation context)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 3. Master prompt
prompt = ChatPromptTemplate.from_template("""
You are a super-assistant that can use the following tools:

- **GmailAgent(input: str)** — Use this to manage Gmail tasks (e.g. search emails, read messages, reply, label).  
  Use it if the user says anything like:
  - "Check my unread emails"
  - "Mark this message as read"
  - "Reply to an email"
  - "Find emails from [person]"

---

### Rules:

1. If the user request relates to email (reading, replying, labeling, searching), call `GmailAgent(input)` with the full natural-language request.
2. When `GmailAgent` returns a final answer or a message with `"status": "success"`, you should stop — the task is complete.
3. Do **not** re-invoke `GmailAgent` unless the user asks something new.
4. Avoid calling tools in loops or repeatedly on the same input.

---

### Prior conversation:
{chat_history}

### User says:
{input}

### Agent scratchpad:
{agent_scratchpad}
""")


# 4. Create the orchestrator agent
orchestrator_agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

orchestrator_executor = AgentExecutor(
    agent=orchestrator_agent,
    tools=tools,
    memory=memory,
    verbose=True
)

def main():
    print("Gmail assistant (type 'exit' or 'quit' to stop)\n")
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.strip().lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        invocation = orchestrator_executor.invoke({"input": user_input})
        print("Assistant:", invocation)
        print()

if __name__ == "__main__":
    main()