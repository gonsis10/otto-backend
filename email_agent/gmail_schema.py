from pydantic import BaseModel
from typing import Optional, List

class SendEmailInput(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    format: str = "plain"

class SearchEmailsInput(BaseModel):
    query: str = "is:inbox"
    max_results: Optional[int] = 5
    days_back: Optional[int] = None

class InspectEmailInput(BaseModel):
    message_id: str
    format: Optional[str] = "full"

class ReplyEmailInput(BaseModel):
    message_id: str
    body: str
    add_label_ids: Optional[List[str]] = None
    remove_label_ids: Optional[List[str]] = None

class MarkEmailInput(BaseModel):
    message_id: str
    add_labels: Optional[List[str]] = None
    remove_labels: Optional[List[str]] = None
