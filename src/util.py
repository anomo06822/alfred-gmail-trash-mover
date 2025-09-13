import logging
import os
from typing import Optional

try:
    # Imported only for typing/error detection; module may not be installed during tests.
    from googleapiclient.errors import HttpError  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    HttpError = None  # type: ignore


def setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("gmail_trash_mover")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def is_retryable(error: Exception) -> bool:
    # Retry Google API HttpError with 429/500/503
    if HttpError is not None and isinstance(error, HttpError):  # type: ignore
        try:
            status = int(getattr(error, "status_code", None) or error.resp.status)  # type: ignore
        except Exception:
            return False
        return status in (429, 500, 503)
    return False


def format_summary(count: int, moved: Optional[int] = None, limited: Optional[int] = None, dry: bool = False) -> str:
    if dry:
        return f"乾跑：命中 {count} 封，示例："
    moved_display = moved if moved is not None else 0
    base = f"命中 {count} 封；已搬移至垃圾桶 {moved_display} 封"
    if limited is not None:
        base += f"（限制 {limited}）"
    base += "。"
    return base


def resolve_paths(credentials_path: Optional[str], token_path: Optional[str]) -> tuple[str, str]:
    # Allow .env overrides for CONFIG_DIR, CREDENTIALS_PATH, TOKEN_PATH
    cred = credentials_path or os.getenv("CREDENTIALS_PATH")
    tok = token_path or os.getenv("TOKEN_PATH")
    cfg_dir = os.getenv("CONFIG_DIR")
    if not cred:
        cred = os.path.join("credentials", "credentials.json")
    if not tok:
        tok = os.path.join(cfg_dir or "data", "token.json")
    return cred, tok
