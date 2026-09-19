"""Small dependency-free Server-Sent Events parser."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Optional


@dataclass(frozen=True)
class SSEEvent:
    event: str
    data: Any
    event_id: Optional[str] = None
    retry_ms: Optional[int] = None


def parse_sse(lines: Iterable[bytes]) -> Iterator[SSEEvent]:
    """Parse an SSE byte-line iterable, ignoring comments/heartbeats."""

    event_name = "message"
    data_lines = []
    event_id = None
    retry_ms = None

    for raw_line in lines:
        line = raw_line.decode("utf-8").rstrip("\r\n")
        if not line:
            if data_lines:
                text = "\n".join(data_lines)
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = text
                yield SSEEvent(event_name, data, event_id, retry_ms)
            event_name, data_lines, retry_ms = "message", [], None
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "event":
            event_name = value
        elif field == "data":
            data_lines.append(value)
        elif field == "id" and "\x00" not in value:
            event_id = value
        elif field == "retry":
            try:
                retry_ms = int(value)
            except ValueError:
                pass


def encode_sse(event: SSEEvent) -> bytes:
    """Encode an event for fixtures and transport tests."""

    lines = []
    if event.event_id is not None:
        lines.append(f"id: {event.event_id}")
    if event.event:
        lines.append(f"event: {event.event}")
    if event.retry_ms is not None:
        lines.append(f"retry: {event.retry_ms}")
    data = (
        event.data
        if isinstance(event.data, str)
        else json.dumps(event.data, separators=(",", ":"))
    )
    lines.extend(f"data: {line}" for line in data.splitlines() or [""])
    return ("\n".join(lines) + "\n\n").encode("utf-8")
