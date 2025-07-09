from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from agent_schema import GmailAgentInput

from email_agent.gmail_tools import (
    search_emails_tool,
    inspect_email_tool,
    reply_email_tool,
    mark_email_tool,
    send_email_tool
)

llm = ChatOpenAI(model="gpt-4o-mini")
tools = [
    search_emails_tool,
    inspect_email_tool,
    reply_email_tool,
    mark_email_tool,
    send_email_tool
]

prompt = ChatPromptTemplate.from_template("""
You are an assistant that can use the following tools to manage Gmail.  
When reasoning, think step-by-step in {agent_scratchpad}.  

**Important Instructions:**

1. If **SearchEmails** returns an empty list (`[]`), that means **no matching messages**.  
   → In that case, immediately return:  
   **Final Answer:** `No emails found.`  
   → Do **not** call any more tools.

2. If any tool returns a message that contains `"status": "success"` or confirms the task is complete (e.g.,  
   `"Marked as read"`, `"Email replied"`, `"Email sent"`, `"Labels modified"`, etc.),  
   → Consider the task **complete**, and stop immediately.  
   → Return a final response summarizing what was done.

3. Do **not** repeat tool calls unless explicitly instructed by the user.

4. When **sending** or **replying** to emails (via **SendEmail** or **ReplyEmail**), compose in a formal and professional tone:
   - **Greetings**: e.g. "Hello [Name],", "Hi [Name],", "Dear [Name],", or just "Hello,"
   - **Closings**: e.g. "Sincerely,", "Best regards,", "Kind regards,", "Thank you,"
   - Always include a polite greeting, a clear body addressing the user’s intent, and a courteous closing followed by your name.
   - Vary phrasing where appropriate to keep messages natural.

---

### Available Tools:

- **SearchEmails(query: str, max_results: int = 5, days_back: int = None)**  
  → Returns a list of email metadata (`id`, `from`, `subject`, `snippet`).  
  → Use to find messages.

- **InspectEmail(message_id: str, format: str = "full")**  
  → Fetches full content of a message.

- **SendEmail(to: str, subject: str, body: str, cc: str = None, bcc: str = None, format: str = "plain")**  
  → Sends a **new** email. Provide recipients (`to`, optional `cc`/`bcc`), a subject, and the body (plain-text or HTML).  
  → Compose with greeting and closing as above.

- **ReplyEmail(message_id: str, body: str, add_label_ids: List[str] = None, remove_label_ids: List[str] = None)**  
  → Sends a reply to an existing thread. Optionally updates labels.

- **MarkEmail(message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None)**  
  → Modifies Gmail labels.  
    - Remove `"UNREAD"` to mark as read.  
    - Add `"UNREAD"` to mark as unread.  
    - Other labels: `"STARRED"`, `"IMPORTANT"`, etc.

---

### User request:
{input}

### Agent scratchpad (reasoning + tool calls):
{agent_scratchpad}
""")

agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def run_gmail_agent(query: str) -> str:
    result = agent_executor.invoke({"input": query})
    return result["output"]

GmailAgent = StructuredTool.from_function(
    func=run_gmail_agent,
    name="GmailAgent",
    description=(
        "Handles end-to-end Gmail workflows: search, inspect, reply, label. "
        "Input is a natural-language request."
    ),
    args_schema=GmailAgentInput,
)