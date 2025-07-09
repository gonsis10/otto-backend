from langchain.tools import StructuredTool
from email_agent.gmail_schema import (
    SearchEmailsInput,
    InspectEmailInput,
    ReplyEmailInput,
    MarkEmailInput,
    SendEmailInput
)
from email_agent.gmail_functions import (
    search_emails,
    inspect_email,
    reply_email,
    mark_email,
    send_email
)

send_email_tool = StructuredTool.from_function(
    func=send_email,
    name="SendEmail",
    description=(
        "Send a new email via Gmail. "
        "Provide `to`, `subject`, and `body`, with optional `cc` and `bcc`. "
        "The `body` can be plain text or HTML."
    ),
    args_schema=SendEmailInput,
)

search_emails_tool = StructuredTool.from_function(
    func=search_emails,
    name="SearchEmails",
    description=(
      "Quickly list messages by Gmail query. "
      "Pass `days_back` to auto-filter to the last N days."
    ),
    args_schema=SearchEmailsInput
)


inspect_email_tool = StructuredTool.from_function(
    func=inspect_email,
    name="InspectEmail",
    description="Fetch the full Gmail API payload for a single message_id.",
    args_schema=InspectEmailInput
)

reply_email_tool = StructuredTool.from_function(
    func=reply_email,
    name="ReplyEmail",
    description=(
        "Send a formal and professionally written reply to a specific email using its message_id. "
        "When writing the response body, include a polite greeting (e.g., 'Hello', 'Hi', or 'Dear') and a courteous closing "
        "(e.g., 'Sincerely', 'Best regards', 'Kind regards'). Vary phrasing where appropriate to keep replies natural. "
        "Provide the response body as plain text. Optionally, label IDs can be added or removed from the sent message."
    ),
    args_schema=ReplyEmailInput
)

mark_email_tool = StructuredTool.from_function(
    func=mark_email,
    name="MarkEmail",
    description=(
        "Add or remove Gmail labels on an email using its message_id. "
        "To mark an email as READ, remove the 'UNREAD' label. "
        "To mark it as UNREAD, add the 'UNREAD' label. "
        "You can also use labels like 'STARRED', 'IMPORTANT', etc."
    ),
    args_schema=MarkEmailInput
)

tools = [
    search_emails_tool,
    inspect_email_tool,
    reply_email_tool,
    mark_email_tool
]
