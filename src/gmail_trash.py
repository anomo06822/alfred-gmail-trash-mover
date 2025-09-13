import argparse
import os
import sys
from typing import Optional

from dotenv import load_dotenv

try:
    from .auth import get_service
    from .gmail_ops import (
        search_message_ids,
        move_to_trash_batch,
        get_snippets,
        count_unique_senders,
        BATCH_SIZE,
    )
    from .util import setup_logger, format_summary, resolve_paths
except Exception:  # pragma: no cover - fallback when run as a file
    from auth import get_service  # type: ignore
    from gmail_ops import (  # type: ignore
        search_message_ids,
        move_to_trash_batch,
        get_snippets,
        count_unique_senders,
        BATCH_SIZE,
    )
    from util import setup_logger, format_summary, resolve_paths  # type: ignore


EXIT_INPUT_ERROR = 1
EXIT_AUTH_ERROR = 2
EXIT_API_ERROR = 3
EXIT_UNKNOWN_ERROR = 4


def parse_args(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Alfred Gmail Trash Mover")
    parser.add_argument("--query", required=True, help="Gmail 搜尋語法")
    parser.add_argument("--dry-run", action="store_true", help="乾跑，不進行實際搬移")
    parser.add_argument("--list-from", action="store_true", help="列出命中郵件的唯一發件者與次數")
    parser.add_argument("--limit", type=int, default=None, help="限制處理筆數")
    parser.add_argument("--log-level", choices=["INFO", "DEBUG"], default="INFO")
    parser.add_argument("--credentials-path", default=None)
    parser.add_argument("--token-path", default=None)
    # Filtering / safety options
    parser.add_argument("--no-skip-starred", dest="skip_starred", action="store_false", help="包含已加星郵件（預設跳過）")
    parser.add_argument("--no-skip-sensitive", dest="skip_sensitive", action="store_false", help="包含可能含帳密/驗證碼等敏感字樣（預設跳過）")
    parser.add_argument("--no-mark-important-star", dest="mark_important_star", action="store_false", help="不要將重要郵件加星（預設會加星並跳過）")
    parser.set_defaults(skip_starred=True, skip_sensitive=True, mark_important_star=True)
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    logger = setup_logger(args.log_level)

    query = (args.query or "").strip()
    if not query:
        sys.stderr.write("參數錯誤：--query 不可為空\n")
        return EXIT_INPUT_ERROR

    try:
        cred_path, tok_path = resolve_paths(args.credentials_path, args.token_path)
        service = get_service(cred_path, tok_path, None)
    except FileNotFoundError as e:
        sys.stderr.write(f"認證失敗：{e}\n")
        return EXIT_AUTH_ERROR
    except Exception as e:  # OAuth errors
        sys.stderr.write(f"認證失敗：{e}\n")
        return EXIT_AUTH_ERROR

    try:
        ids = search_message_ids(service, "me", query, args.limit)
        count = len(ids)
        if args.list_from:
            pairs = count_unique_senders(service, "me", ids)
            lines = [f"發件者統計（共 {len(pairs)} 個）："]
            for email, n in pairs:
                lines.append(f"- {email}: {n}")
            print("\n".join(lines))
            return 0
        if args.dry_run:
            samples = get_snippets(service, "me", ids, sample=3)
            summary = format_summary(count, dry=True)
            out = [summary]
            for s in samples:
                out.append(f"- {s}")
            print("\n".join(out))
            return 0

        # Fetch metadata and apply filters
        try:
            from .gmail_ops import get_messages_metadata, filter_ids_for_trash, add_star_label_batch
        except Exception:  # pragma: no cover
            from gmail_ops import get_messages_metadata, filter_ids_for_trash, add_star_label_batch  # type: ignore

        metas = get_messages_metadata(service, "me", ids, headers=["Subject", "From"])

        # Star important ones, skip them from trash
        if args.mark_important_star:
            to_star = [m["id"] for m in metas if "IMPORTANT" in set(m.get("labelIds", [])) and "STARRED" not in set(m.get("labelIds", []))]
            if to_star:
                add_star_label_batch(service, "me", to_star)

        trash_ids, skipped = filter_ids_for_trash(
            metas,
            skip_starred=args.skip_starred,
            skip_important=True,
            skip_sensitive=args.skip_sensitive,
        )

        moved = move_to_trash_batch(service, "me", trash_ids)
        limited = args.limit if args.limit is not None and args.limit < count else None
        print(format_summary(count, moved=moved, limited=limited, dry=False))
        print(f"已跳過：加星 {skipped.get('starred',0)}、重要 {skipped.get('important',0)}、敏感 {skipped.get('sensitive',0)}")
        logger.debug(f"批次大小: {BATCH_SIZE}")
        return 0
    except Exception as e:
        # Distinguish API vs unknown only loosely here
        msg = str(e)
        if "HttpError" in e.__class__.__name__:
            sys.stderr.write(f"API 錯誤：{msg}\n")
            return EXIT_API_ERROR
        sys.stderr.write(f"未預期錯誤：{msg}\n")
        return EXIT_UNKNOWN_ERROR


if __name__ == "__main__":
    sys.exit(main())
