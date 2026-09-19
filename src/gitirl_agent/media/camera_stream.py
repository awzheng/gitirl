"""Provisional binary camera-frame contract and WebSocket sender."""

from __future__ import annotations

import asyncio
import inspect
import json
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Mapping, Optional, Protocol
from uuid import uuid4


MAGIC = b"GIRL"
WIRE_VERSION = 1
PREFIX = struct.Struct(">4sBI")
FRAME_LENGTH = struct.Struct(">I")
MAX_FRAME_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class CameraFrame:
    camera_id: str
    mount_angle_degrees: float
    sequence: int
    captured_at: str
    data: bytes
    encoding: str = "raw"
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


class CameraFrameSource(Protocol):
    def frames(self) -> AsyncIterator[CameraFrame]:
        """Yield camera frames without assuming a capture SDK."""


class LengthPrefixedFrameSource:
    """Development source for files/FIFOs containing framed camera bytes.

    Each frame is a four-byte big-endian payload length followed by that many
    bytes. The source does not interpret, compress, or transcode the payload.
    """

    def __init__(
        self,
        camera_id: str,
        mount_angle_degrees: float,
        path: Path,
        encoding: str = "raw",
        max_frame_bytes: int = MAX_FRAME_BYTES,
    ) -> None:
        self.camera_id = camera_id
        self.mount_angle_degrees = mount_angle_degrees
        self.path = path
        self.encoding = encoding
        self.max_frame_bytes = max_frame_bytes

    async def frames(self) -> AsyncIterator[CameraFrame]:
        stream = await asyncio.to_thread(self.path.open, "rb")
        sequence = 0
        try:
            while True:
                prefix = await asyncio.to_thread(
                    _read_exact,
                    stream,
                    FRAME_LENGTH.size,
                    True,
                )
                if prefix is None:
                    return
                (payload_size,) = FRAME_LENGTH.unpack(prefix)
                if payload_size > self.max_frame_bytes:
                    raise ValueError(
                        f"Frame from {self.camera_id} exceeds configured limit"
                    )
                payload = await asyncio.to_thread(
                    _read_exact,
                    stream,
                    payload_size,
                    False,
                )
                yield CameraFrame(
                    camera_id=self.camera_id,
                    mount_angle_degrees=self.mount_angle_degrees,
                    sequence=sequence,
                    captured_at=datetime.now(timezone.utc).isoformat(),
                    data=payload,
                    encoding=self.encoding,
                )
                sequence += 1
        finally:
            await asyncio.to_thread(stream.close)


def encode_camera_frame(frame: CameraFrame, stream_id: str) -> bytes:
    """Encode one provisional binary WebSocket message."""

    header = {
        "type": "camera_frame",
        "version": WIRE_VERSION,
        "stream_id": stream_id,
        "camera_id": frame.camera_id,
        "mount_angle_degrees": frame.mount_angle_degrees,
        "sequence": frame.sequence,
        "captured_at": frame.captured_at,
        "encoding": frame.encoding,
        "payload_bytes": len(frame.data),
        "metadata": dict(frame.metadata),
    }
    encoded_header = json.dumps(
        header,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return (
        PREFIX.pack(MAGIC, WIRE_VERSION, len(encoded_header))
        + encoded_header
        + frame.data
    )


def _read_exact(stream: Any, size: int, allow_clean_eof: bool) -> Optional[bytes]:
    chunks = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            if allow_clean_eof and not chunks:
                return None
            raise ValueError("Incomplete length-prefixed camera frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def decode_camera_frame(message: bytes) -> tuple:
    """Decode a frame for tests and Daniel's provisional receiver adapter."""

    if len(message) < PREFIX.size:
        raise ValueError("Camera message is too short")
    magic, version, header_size = PREFIX.unpack(message[: PREFIX.size])
    if magic != MAGIC or version != WIRE_VERSION:
        raise ValueError("Unsupported camera message")
    header_end = PREFIX.size + header_size
    if len(message) < header_end:
        raise ValueError("Camera message header is incomplete")
    header = json.loads(message[PREFIX.size : header_end].decode("utf-8"))
    payload = message[header_end:]
    if header.get("payload_bytes") != len(payload):
        raise ValueError("Camera payload length does not match header")
    return header, payload


class CameraWebSocketSender:
    """Binary WebSocket sender with bounded reconnect attempts."""

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        max_reconnect_attempts: int = 5,
        reconnect_delay_seconds: float = 1.0,
    ) -> None:
        if not url:
            raise ValueError("Camera WebSocket URL cannot be empty")
        self._url = url
        self._token = token
        self._max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_delay_seconds = reconnect_delay_seconds
        self._connection: Any = None
        self._send_lock = asyncio.Lock()
        self.stream_id = str(uuid4())

    async def connect(self) -> None:
        try:
            import websockets
        except ImportError as error:
            raise RuntimeError(
                "Camera streaming requires: python3 -m pip install -r requirements.txt"
            ) from error

        kwargs: Dict[str, Any] = {}
        if self._token:
            headers = {"Authorization": f"Bearer {self._token}"}
            parameters = inspect.signature(websockets.connect).parameters
            header_name = (
                "additional_headers"
                if "additional_headers" in parameters
                else "extra_headers"
            )
            kwargs[header_name] = headers
        # No local port is fixed. The operating system selects an ephemeral
        # source port for this outbound connection.
        self._connection = await websockets.connect(self._url, **kwargs)

    async def disconnect(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def send(self, frame: CameraFrame) -> None:
        message = encode_camera_frame(frame, self.stream_id)
        async with self._send_lock:
            for attempt in range(self._max_reconnect_attempts + 1):
                try:
                    if self._connection is None:
                        await self.connect()
                    await self._connection.send(message)
                    return
                except Exception:
                    await self.disconnect()
                    if attempt == self._max_reconnect_attempts:
                        raise
                    await asyncio.sleep(self._reconnect_delay_seconds)

    async def stream(self, sources: Mapping[str, CameraFrameSource]) -> None:
        if len(sources) != 3:
            raise ValueError("Exactly three camera sources are required")

        async def forward(source: CameraFrameSource) -> None:
            async for frame in source.frames():
                await self.send(frame)

        try:
            await asyncio.gather(*(forward(source) for source in sources.values()))
        finally:
            await self.disconnect()
