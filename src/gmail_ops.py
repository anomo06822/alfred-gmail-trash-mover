from __future__ import annotations

from typing import List, Sequence

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

try:
    from .util import is_retryable
except Exception:  # pragma: no cover - fallback when run as script
    from util import is_retryable  # type: ignore


BATCH_SIZE = 1000


def search_message_ids(service, user_id: str, query: str, limit: int | None = None) -> List[str]:
    ids: List[str] = []
    page_token = None
    while True:
        max_results = 500
        req = (
            service.users()
            .messages()
            .list(userId=user_id, q=query, pageToken=page_token, maxResults=max_results)
        )
        res = req.execute()
        for m in res.get("messages", []):
            ids.append(m["id"])  # type: ignore[index]
            if limit is not None and len(ids) >= limit:
                return ids
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return ids


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1), retry=retry_if_exception(is_retryable))
def _batch_modify(service, user_id: str, batch_ids: Sequence[str]):
    body = {"addLabelIds": ["TRASH"], "ids": list(batch_ids)}
    return service.users().messages().batchModify(userId=user_id, body=body).execute()


def move_to_trash_batch(service, user_id: str, ids: Sequence[str]) -> int:
    total = 0
    for i in range(0, len(ids), BATCH_SIZE):
        chunk = ids[i : i + BATCH_SIZE]
        _batch_modify(service, user_id, chunk)
        total += len(chunk)
    return total


def get_snippets(service, user_id: str, ids: Sequence[str], sample: int = 3) -> List[str]:
    result: List[str] = []
    for mid in ids[: sample or 0]:
        res = service.users().messages().get(userId=user_id, id=mid, format="metadata").execute()
        snippet = res.get("snippet", "")
        snippet = snippet.replace("\n", " ").strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        result.append(f"[{mid}] {snippet}")
    return result


def _extract_from_header(payload_headers: list[dict]) -> str | None:
    for h in payload_headers:
        if h.get("name", "").lower() == "from":
            return h.get("value")
    return None


def get_from_addresses(service, user_id: str, ids: Sequence[str]) -> List[str]:
    addrs: List[str] = []
    for mid in ids:
        res = (
            service.users()
            .messages()
            .get(
                userId=user_id,
                id=mid,
                format="metadata",
                metadataHeaders=["From"],
            )
            .execute()
        )
        payload = res.get("payload", {})
        headers = payload.get("headers", [])
        from_raw = _extract_from_header(headers)
        if from_raw:
            addrs.append(from_raw)
    return addrs


def count_unique_senders(service, user_id: str, ids: Sequence[str]) -> list[tuple[str, int]]:
    from email.utils import getaddresses
    from collections import Counter

    raw_list = get_from_addresses(service, user_id, ids)
    parsed = []
    for raw in raw_list:
        # Extract just the email part
        addrs = getaddresses([raw])
        if not addrs:
            continue
        _, email_addr = addrs[0]
        if email_addr:
            parsed.append(email_addr.lower())
    counts = Counter(parsed)
    # Return sorted by count desc, then email asc
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
