from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_FORMATS = {"json", "csv", "txt"}
HEADER_RE = re.compile(r"^===\s*(?P<id>[^|]+?)\s*\|\s*(?P<title>[^|]+?)\s*\|\s*(?P<created>.+?)\s*===\s*$")
TXT_MESSAGE_RE = re.compile(r"^(?P<role>[A-Za-z_]+)\s*\[(?P<timestamp>[^\]]+)\]:\s*(?P<content>.*)$")
CSV_MESSAGE_RE = re.compile(r"^(?P<role>[A-Za-z_]+):\s*(?P<content>.*)$")


class UnsupportedImportFormat(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedMessage:
    external_id: str | None
    role: str
    timestamp: datetime | None
    content: str


@dataclass(frozen=True)
class NormalizedChat:
    external_id: str
    title: str
    created_at: datetime | None
    updated_at: datetime | None
    messages: list[NormalizedMessage]
    content_fingerprint: str
    source_index: int


@dataclass(frozen=True)
class ParseIssue:
    scope: str
    code: str
    message: str
    record_reference: str | None = None
    severity: str = "ERROR"


@dataclass
class ParseResult:
    chats: list[NormalizedChat] = field(default_factory=list)
    issues: list[ParseIssue] = field(default_factory=list)


def detect_format(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_FORMATS:
        raise UnsupportedImportFormat(f"Unsupported file format: .{suffix or 'unknown'}")
    return suffix


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_role(value: Any) -> str:
    role = str(value or "unknown").strip().lower()
    aliases = {"human": "user", "bot": "assistant", "ai": "assistant"}
    return aliases.get(role, role or "unknown")


def normalize_content(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def make_fingerprint(messages: list[NormalizedMessage]) -> str:
    canonical = "\n".join(f"{message.role}:{message.content}" for message in messages)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _chat(
    external_id: str,
    title: str,
    created_at: datetime | None,
    updated_at: datetime | None,
    messages: list[NormalizedMessage],
    source_index: int,
) -> NormalizedChat:
    return NormalizedChat(
        external_id=external_id.strip(),
        title=title.strip() or external_id.strip(),
        created_at=created_at,
        updated_at=updated_at or next((message.timestamp for message in reversed(messages) if message.timestamp is not None), created_at),
        messages=messages,
        content_fingerprint=make_fingerprint(messages),
        source_index=source_index,
    )


def parse_import_file(filename: str, content: bytes) -> ParseResult:
    file_format = detect_format(filename)
    if file_format == "json":
        return parse_json(content)
    if file_format == "csv":
        return parse_csv(content)
    return parse_txt(content)


def parse_json(content: bytes) -> ParseResult:
    result = ParseResult()
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        result.issues.append(ParseIssue("FILE", "INVALID_JSON", f"JSON could not be decoded: {exc}"))
        return result

    conversations = payload.get("conversations") if isinstance(payload, dict) else payload
    if not isinstance(conversations, list):
        result.issues.append(ParseIssue("FILE", "JSON_CONVERSATIONS_REQUIRED", "JSON must contain a conversations array"))
        return result

    for index, item in enumerate(conversations):
        reference = f"conversation[{index}]"
        if not isinstance(item, dict):
            result.issues.append(ParseIssue("RECORD", "INVALID_CONVERSATION", "Conversation must be an object", reference))
            continue
        external_id = str(item.get("id") or f"json-chat-{index + 1}").strip()
        title = str(item.get("title") or external_id).strip()
        raw_messages = item.get("messages")
        if not isinstance(raw_messages, list) or not raw_messages:
            result.issues.append(ParseIssue("RECORD", "MESSAGES_REQUIRED", "Conversation has no valid messages array", external_id))
            continue
        messages: list[NormalizedMessage] = []
        for message_index, raw in enumerate(raw_messages):
            if not isinstance(raw, dict):
                result.issues.append(ParseIssue("MESSAGE", "INVALID_MESSAGE", "Message must be an object", f"{external_id}:{message_index}"))
                continue
            message_content = normalize_content(raw.get("content"))
            if not message_content:
                result.issues.append(ParseIssue("MESSAGE", "EMPTY_MESSAGE", "Empty message was skipped", f"{external_id}:{message_index}", "WARNING"))
                continue
            messages.append(
                NormalizedMessage(
                    external_id=str(raw.get("id")) if raw.get("id") is not None else None,
                    role=normalize_role(raw.get("role")),
                    timestamp=parse_datetime(raw.get("timestamp")),
                    content=message_content,
                )
            )
        if not messages:
            result.issues.append(ParseIssue("RECORD", "NO_IMPORTABLE_MESSAGES", "Conversation has no importable messages", external_id))
            continue
        result.chats.append(
            _chat(
                external_id,
                title,
                parse_datetime(item.get("created_at")) or messages[0].timestamp,
                parse_datetime(item.get("updated_at")),
                messages,
                index,
            )
        )
    return result


def parse_csv(content: bytes) -> ParseResult:
    result = ParseResult()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        result.issues.append(ParseIssue("FILE", "INVALID_ENCODING", f"CSV must be UTF-8: {exc}"))
        return result
    reader = csv.DictReader(io.StringIO(text))
    required = {"chat_id", "title", "created_at", "transcript"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        result.issues.append(ParseIssue("FILE", "CSV_HEADERS_REQUIRED", "CSV headers must include chat_id,title,created_at,transcript"))
        return result

    for index, row in enumerate(reader):
        external_id = str(row.get("chat_id") or f"csv-chat-{index + 1}").strip()
        transcript = str(row.get("transcript") or "")
        messages: list[NormalizedMessage] = []
        for raw_line in transcript.splitlines():
            match = CSV_MESSAGE_RE.match(raw_line.strip())
            if match:
                content_value = normalize_content(match.group("content"))
                if content_value:
                    messages.append(
                        NormalizedMessage(
                            external_id=f"{external_id}-message-{len(messages) + 1}",
                            role=normalize_role(match.group("role")),
                            timestamp=None,
                            content=content_value,
                        )
                    )
            elif messages and raw_line.strip():
                previous = messages[-1]
                messages[-1] = NormalizedMessage(
                    external_id=previous.external_id,
                    role=previous.role,
                    timestamp=previous.timestamp,
                    content=f"{previous.content}\n{normalize_content(raw_line)}",
                )
        if not messages:
            result.issues.append(ParseIssue("RECORD", "TRANSCRIPT_REQUIRED", "CSV row has no parseable transcript", external_id))
            continue
        created_at = parse_datetime(row.get("created_at"))
        if messages and created_at:
            first = messages[0]
            messages[0] = NormalizedMessage(first.external_id, first.role, created_at, first.content)
        result.chats.append(_chat(external_id, str(row.get("title") or external_id), created_at, None, messages, index))
    return result


def parse_txt(content: bytes) -> ParseResult:
    result = ParseResult()
    try:
        lines = content.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        result.issues.append(ParseIssue("FILE", "INVALID_ENCODING", f"TXT must be UTF-8: {exc}"))
        return result

    current: dict[str, Any] | None = None
    blocks: list[dict[str, Any]] = []
    for line in lines:
        header = HEADER_RE.match(line)
        if header:
            if current is not None:
                blocks.append(current)
            current = {
                "id": header.group("id").strip(),
                "title": header.group("title").strip(),
                "created": header.group("created").strip(),
                "messages": [],
            }
            continue
        if current is None:
            if line.strip():
                result.issues.append(ParseIssue("FILE", "TEXT_OUTSIDE_BLOCK", "Text outside a chat block was ignored", severity="WARNING"))
            continue
        match = TXT_MESSAGE_RE.match(line)
        if match:
            content_value = normalize_content(match.group("content"))
            if content_value:
                current["messages"].append(
                    NormalizedMessage(
                        external_id=f"{current['id']}-message-{len(current['messages']) + 1}",
                        role=normalize_role(match.group("role")),
                        timestamp=parse_datetime(match.group("timestamp")),
                        content=content_value,
                    )
                )
        elif line.strip() and current["messages"]:
            previous = current["messages"][-1]
            current["messages"][-1] = NormalizedMessage(
                previous.external_id,
                previous.role,
                previous.timestamp,
                f"{previous.content}\n{normalize_content(line)}",
            )
    if current is not None:
        blocks.append(current)

    if not blocks:
        result.issues.append(ParseIssue("FILE", "TXT_BLOCKS_REQUIRED", "TXT must contain chat blocks with === headers"))
        return result

    for index, block in enumerate(blocks):
        if not block["messages"]:
            result.issues.append(ParseIssue("RECORD", "NO_IMPORTABLE_MESSAGES", "TXT chat block has no messages", block["id"]))
            continue
        result.chats.append(
            _chat(
                block["id"],
                block["title"],
                parse_datetime(block["created"]) or block["messages"][0].timestamp,
                None,
                block["messages"],
                index,
            )
        )
    return result
