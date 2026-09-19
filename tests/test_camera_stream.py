import asyncio
import struct
import tempfile
import unittest
from pathlib import Path

from src.gitirl_agent.media.camera_stream import (
    BBOSJPEGFrameSource,
    CameraFrame,
    LengthPrefixedFrameSource,
    decode_camera_frame,
    encode_camera_frame,
)


class CameraStreamTests(unittest.IsolatedAsyncioTestCase):
    def test_binary_frame_round_trip(self) -> None:
        frame = CameraFrame(
            camera_id="camera_1",
            mount_angle_degrees=12.5,
            sequence=7,
            captured_at="2026-09-18T12:00:00+00:00",
            data=b"raw-frame-bytes",
            metadata={"width": 2, "height": 2},
        )

        header, payload = decode_camera_frame(
            encode_camera_frame(frame, "stream-123")
        )

        self.assertEqual(header["camera_id"], "camera_1")
        self.assertEqual(header["mount_angle_degrees"], 12.5)
        self.assertEqual(header["stream_id"], "stream-123")
        self.assertEqual(payload, b"raw-frame-bytes")

    async def test_length_prefixed_source_reads_frames(self) -> None:
        payloads = (b"camera-frame-one", b"camera-frame-two")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "camera.frames"
            with path.open("wb") as stream:
                for payload in payloads:
                    stream.write(struct.pack(">I", len(payload)))
                    stream.write(payload)

            source = LengthPrefixedFrameSource("camera_0", 0.0, path)
            frames = [frame async for frame in source.frames()]

        self.assertEqual(tuple(frame.data for frame in frames), payloads)
        self.assertEqual([frame.sequence for frame in frames], [0, 1])

    async def test_bbos_source_reads_confirmed_jpeg_record(self) -> None:
        class Reader:
            data = {
                "jpeg_len": 4,
                "jpeg": b"jpeg-unused-capacity",
                "timestamp": "robot-time",
            }

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                pass

            def ready(self):
                return True

        source = BBOSJPEGFrameSource(
            "head",
            "camera.head.jpeg",
            reader_factory=lambda topic, keeptime=False: Reader(),
        )
        stream = source.frames()
        frame = await stream.__anext__()
        await stream.aclose()

        self.assertEqual(frame.camera_id, "head")
        self.assertIsNone(frame.mount_angle_degrees)
        self.assertEqual(frame.data, b"jpeg")
        self.assertEqual(frame.encoding, "jpeg")
        self.assertEqual(frame.metadata["bbos_topic"], "camera.head.jpeg")


if __name__ == "__main__":
    unittest.main()
