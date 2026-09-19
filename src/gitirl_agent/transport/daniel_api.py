"""HTTP/SSE boundary for Daniel's existing web/cloud service."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterator, Mapping, Optional

from src.gitirl_agent.transport.sse import SSEEvent, parse_sse


class DanielAPIError(RuntimeError):
    pass


class DanielAPIClient:
    """Match Daniel's current `/api/command`, `/api/events`, and event inlet."""

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("Daniel base URL must use http or https")
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls) -> Optional["DanielAPIClient"]:
        base_url = os.environ.get("GITIRL_CLOUD_BASE_URL", "").strip()
        if not base_url:
            return None
        return cls(base_url, os.environ.get("GITIRL_CLOUD_TOKEN") or None)

    def plan_command(self, command: str, args: Mapping[str, Any]) -> Any:
        return self._json_request(
            "POST", "/api/command", {"command": command, "args": dict(args)}
        )

    def get_state(self, ref: str = "HEAD") -> Any:
        query = urllib.parse.urlencode({"ref": ref})
        return self._json_request("GET", f"/api/state?{query}")

    def publish_event(self, event: str, data: Mapping[str, Any]) -> Any:
        """Publish to Daniel's loopback-only inlet when colocated with web/server.py."""

        return self._json_request(
            "POST", "/api/internal/event", {"event": event, "data": dict(data)}
        )

    def events(self, last_event_id: Optional[str] = None) -> Iterator[SSEEvent]:
        headers = {"Accept": "text/event-stream"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id
        request = urllib.request.Request(
            self._base_url + "/api/events", headers=headers, method="GET"
        )
        try:
            with urllib.request.urlopen(request, timeout=None) as response:
                yield from parse_sse(response)
        except (urllib.error.URLError, TimeoutError) as error:
            raise DanielAPIError(str(error)) from error

    def _json_request(
        self,
        method: str,
        path: str,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(
            self._base_url + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self._timeout_seconds
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                detail = {"error": "http_error", "detail": str(error)}
            raise DanielAPIError(
                f"HTTP {error.code}: {detail.get('error', 'cloud_error')}: "
                f"{detail.get('detail', '')}"
            ) from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise DanielAPIError(str(error)) from error
