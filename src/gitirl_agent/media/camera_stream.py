"""Provisional camera-frame contract and HTTP sender."""

from __future__ import annotations

import asyncio
import importlib
import json
import struct
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Mapping, Optional, Protocol
from uuid import uuid4


MAGIC = b"GIRL"
WIRE_VERSION = 1
PREFIX = struct.Struct(">4sBI")
FRAME_LENGTH = struct.Struct(">I")
MAX_FRAME_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class CameraFrame:
    camera_id: str
    mount_angle_degrees: Optional[float]
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


class BBOSJPEGFrameSource:
    """Read one confirmed BracketBot JPEG topic without controlling hardware."""

    def __init__(
        self,
        camera_id: str,
        topic: str,
        mount_angle_degrees: Optional[float] = None,
        poll_interval_seconds: float = 0.01,
        reader_factory: Any = None,
    ) -> None:
        self.camera_id = camera_id
        self.topic = topic
        self.mount_angle_degrees = mount_angle_degrees
        self.poll_interval_seconds = poll_interval_seconds
        self._reader_factory = reader_factory

    async def frames(self) -> AsyncIterator[CameraFrame]:
        factory = self._reader_factory
        if factory is None:
            try:
                factory = importlib.import_module("bbos").Reader
            except (ImportError, AttributeError) as error:
                raise RuntimeError(
                    "BBOS is unavailable; run --bbos on the BracketBot host with "
                    "/home/bracketbot/bbos on PYTHONPATH"
                ) from error

        reader = factory(self.topic, keeptime=False).__enter__()
        sequence = 0
        try:
            while True:
                if not reader.ready():
                    await asyncio.sleep(self.poll_interval_seconds)
                    continue
                record = reader.data
                size = int(record["jpeg_len"])
                payload = bytes(record["jpeg"][:size])
                yield CameraFrame(
                    camera_id=self.camera_id,
                    mount_angle_degrees=self.mount_angle_degrees,
                    sequence=sequence,
                    captured_at=str(record["timestamp"]),
                    data=payload,
                    encoding="jpeg",
                    metadata={"bbos_topic": self.topic},
                )
                sequence += 1
        finally:
            reader.__exit__(None, None, None)


def encode_camera_frame(frame: CameraFrame, stream_id: str) -> bytes:
    """Encode one provisional self-describing binary HTTP body."""

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


class CameraHTTPSender:
    """POST self-contained frames to an HTTP API; no persistent socket."""

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not url:
            raise ValueError("Camera HTTP URL cannot be empty")
        self._url = url
        self._token = token
        self._timeout_seconds = timeout_seconds
        self.stream_id = str(uuid4())

    def _post(self, message: bytes) -> None:
        headers = {"Content-Type": "application/octet-stream"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(
            self._url, data=message, headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            response.read()

    async def send(self, frame: CameraFrame) -> None:
        message = encode_camera_frame(frame, self.stream_id)
        await asyncio.to_thread(self._post, message)

    async def stream(self, sources: Mapping[str, CameraFrameSource]) -> None:
        if len(sources) != 3:
            raise ValueError("Exactly three camera sources are required")

        async def forward(source: CameraFrameSource) -> None:
            async for frame in source.frames():
                await self.send(frame)

        await asyncio.gather(*(forward(source) for source in sources.values()))
