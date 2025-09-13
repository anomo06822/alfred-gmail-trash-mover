import os
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

try:
    from .util import resolve_paths
except Exception:  # pragma: no cover - fallback when run as script
    from util import resolve_paths  # type: ignore


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_service(credentials_path: Optional[str] = None, token_path: Optional[str] = None, scopes: Optional[list[str]] = None):
    cred_path, tok_path = resolve_paths(credentials_path, token_path)
    use_scopes = scopes or SCOPES

    creds: Optional[Credentials] = None
    if os.path.exists(tok_path):
        creds = Credentials.from_authorized_user_file(tok_path, use_scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"找不到憑證檔案：{cred_path}")
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, use_scopes)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(tok_path), exist_ok=True)
        with open(tok_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service
