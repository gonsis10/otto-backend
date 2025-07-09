import base64
from googleapiclient.discovery import build
from auth import get_gmail_credentials
from typing import List, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict
from enum import Enum

class Status(Enum):
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    SKIPPED = "skipped"

def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None,
    format: str = "plain"
) -> Dict[str, str]:
    """
    Send an email via the user's Gmail account.

    Args:
        to (str): Comma-separated recipient email address(es).
        subject (str): Subject line of the email.
        body (str): The body text of the email.
        cc (str, optional): Comma-separated CC recipient(s). Defaults to None.
        bcc (str, optional): Comma-separated BCC recipient(s). Defaults to None.
        format (str): MIME subtype, "plain" or "html". Defaults to "plain".

    Returns:
        dict: { "status": "success", "id": <sent_message_id> }
    """
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Build the MIME message
    mime = MIMEText(body, _subtype=format)
    mime["To"] = to
    mime["Subject"] = subject
    if cc:
        mime["Cc"] = cc
    if bcc:
        mime["Bcc"] = bcc

    # Base64-url encode
    raw_message = base64.urlsafe_b64encode(mime.as_bytes()).decode()

    # Send it
    sent = service.users().messages().send(
        userId="me", body={"raw": raw_message}
    ).execute()

    return {"status": Status.SUCCESS.value, "id": sent.get("id", "")}
    

def search_emails(
    *,
    query: str = "is:inbox",
    max_results: int = 5,
    days_back: Optional[int] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Search for emails in the user's Gmail inbox based on a query.

    Args:
        query (str): Gmail search query string. Defaults to "is:inbox".
        max_results (int): Maximum number of results to return. Defaults to 5.
        days_back (Optional[int]): Number of days back to filter emails. Defaults to None.

    Returns:
        dict: {"emails": [...]} or {"emails": []} if no results
    """
    creds = get_gmail_credentials()
    svc = build("gmail", "v1", credentials=creds)

    if days_back is not None:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        date_str = cutoff.strftime("%Y/%m/%d")
        query = f"{query} after:{date_str}"

    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()

    out = []
    for m in resp.get("messages", []):
        msg = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata"
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        out.append({
            "id": m["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "snippet": msg.get("snippet", "")
        })

    return {"emails": out}

def inspect_email(message_id: str, format: str = "full") -> Dict[str, Dict]:
    """
    Inspect the details of a specific email.

    Args:
        message_id (str): The ID of the email to inspect.
        format (str): The format of the email data to retrieve. Defaults to "full".

    Returns:
        dict: {"status": "success", "data": {...}}
    """
    creds = get_gmail_credentials()
    svc = build("gmail", "v1", credentials=creds)
    msg = svc.users().messages().get(userId="me", id=message_id, format=format).execute()
    return {
        "status": Status.SUCCESS.value,
        "data": {
            "id": message_id,
            "format": format,
            "snippet": msg.get("snippet", ""),
            "payload": msg.get("payload", {})
        }
    }

def reply_email(
    message_id: str,
    body: str,
    add_label_ids: List[str] = None,
    remove_label_ids: List[str] = None
) -> Dict[str, str]:
    """
    Reply to an email with a specified message body.

    Args:
        message_id (str): The ID of the email to reply to.
        body (str): The body of the reply email.
        add_label_ids (List[str], optional): Labels to add to the replied email. Defaults to None.
        remove_label_ids (List[str], optional): Labels to remove from the replied email. Defaults to None.

    Returns:
        dict: {"status": "success", "id": <sent_message_id>}
    """
    creds = get_gmail_credentials()
    svc = build("gmail", "v1", credentials=creds)

    # Get original message metadata
    msg = svc.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["Message-ID", "References", "In-Reply-To", "Subject", "From"]
    ).execute()

    thread_id = msg["threadId"]
    hdrs = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    # Required headers
    in_reply_to = hdrs.get("Message-ID", "")
    references = hdrs.get("References", in_reply_to)
    subject = hdrs.get("Subject", "(no subject)")
    to_email = hdrs.get("From", "")

    mime = MIMEText(body)
    mime["To"] = to_email
    mime["Subject"] = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
    mime["In-Reply-To"] = in_reply_to
    mime["References"] = references

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    send_body = {"raw": raw, "threadId": thread_id}

    # Send reply
    sent = svc.users().messages().send(userId="me", body=send_body).execute()

    # Modify labels (optional)
    if add_label_ids or remove_label_ids:
        svc.users().messages().modify(
            userId="me",
            id=sent["id"],
            body={
                "addLabelIds": add_label_ids or [],
                "removeLabelIds": remove_label_ids or []
            }
        ).execute()

    return {"status": Status.SUCCESS.value, "id": sent.get("id")}

def mark_email(*, message_id: str, add_labels=None, remove_labels=None) -> Dict[str, str]:
    """
    Modify labels on an email (e.g., mark as read/unread).

    Args:
        message_id (str): The ID of the email to modify.
        add_labels (list, optional): Labels to add to the email. Defaults to None.
        remove_labels (list, optional): Labels to remove from the email. Defaults to None.

    Returns:
        dict: {"status": "success"} or {"status": "skipped"}
    """
    creds = get_gmail_credentials()
    svc = build("gmail", "v1", credentials=creds)

    # Handle "READ" = remove "UNREAD"
    if add_labels and "READ" in [l.upper() for l in add_labels]:
        remove_labels = (remove_labels or []) + ["UNREAD"]
        add_labels = [l for l in add_labels if l.upper() != "READ"]

    # Check current labels before modifying
    current_labels = svc.users().messages().get(userId="me", id=message_id, format="metadata").execute().get("labelIds", [])
    if "UNREAD" not in current_labels and (remove_labels and "UNREAD" in [l.upper() for l in remove_labels]):
        return {"status": Status.SKIPPED.value}

    svc.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label.upper() for label in (add_labels or [])],
            "removeLabelIds": [label.upper() for label in (remove_labels or [])],
        },
    ).execute()

    return {"status": Status.SUCCESS.value}
