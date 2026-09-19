"""WebSocket transport only: connect, receive, send, and reconnect."""

from __future__ import annotations

import asyncio
import inspect
import os
from typing import Any, Awaitable, Callable, Optional, Sequence

from src.gitirl_agent.protocol.messages import MessageEnvelope
from src.gitirl_agent.protocol.serialization import (
    ProtocolMessageError,
    deserialize_message,
    serialize_message,
)


MessageHandler = Callable[
    [MessageEnvelope], Awaitable[Sequence[MessageEnvelope]]
]


class WebSocketTransport:
    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        reconnect_delay_seconds: float = 1.0,
        max_reconnect_attempts: int = 5,
    ) -> None:
        if not url:
            raise ValueError("WebSocket URL cannot be empty")
        self._url = url
        self._token = token
        self._reconnect_delay_seconds = reconnect_delay_seconds
        self._max_reconnect_attempts = max_reconnect_attempts
        self._connection: Any = None

    @classmethod
    def from_environment(cls) -> Optional["WebSocketTransport"]:
        url = os.environ.get("GITIRL_WS_URL")
        if not url:
            return None
        return cls(url=url, token=os.environ.get("GITIRL_WS_TOKEN"))

    async def connect(self) -> None:
        try:
            import websockets
        except ImportError as error:
            raise RuntimeError(
                "WebSocket mode requires: python3 -m pip install -r requirements.txt"
            ) from error

        headers = None
        if self._token:
            headers = {"Authorization": f"Bearer {self._token}"}

        connect_kwargs = {}
        if headers:
            parameters = inspect.signature(websockets.connect).parameters
            header_name = (
                "additional_headers"
                if "additional_headers" in parameters
                else "extra_headers"
            )
            connect_kwargs[header_name] = headers
        self._connection = await websockets.connect(self._url, **connect_kwargs)

    async def disconnect(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def receive(self) -> MessageEnvelope:
        if self._connection is None:
            raise RuntimeError("WebSocket is not connected")
        raw = await self._connection.recv()
        if not isinstance(raw, str):
            raise ProtocolMessageError("Binary WebSocket messages are unsupported")
        return deserialize_message(raw)

    async def send(self, message: MessageEnvelope) -> None:
        if self._connection is None:
            raise RuntimeError("WebSocket is not connected")
        await self._connection.send(serialize_message(message))

    async def listen(self, handler: MessageHandler) -> None:
        reconnect_attempts = 0
        while True:
            try:
                if self._connection is None:
                    await self.connect()
                reconnect_attempts = 0
                message = await self.receive()
                for response in await handler(message):
                    await self.send(response)
            except ProtocolMessageError:
                raise
            except Exception:
                await self.disconnect()
                reconnect_attempts += 1
                if reconnect_attempts > self._max_reconnect_attempts:
                    raise
                await asyncio.sleep(self._reconnect_delay_seconds)
