from pydantic import BaseModel

class GmailAgentInput(BaseModel):
    """Wraps the natural-language request for the Gmail agent."""
    query: str
