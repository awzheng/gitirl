# Provisional three-camera streaming

This development boundary forwards opaque frame bytes from three camera sources to a WebSocket endpoint supplied by Daniel. It does not capture from BracketBot, stitch a panorama, transform pixels, or assume a camera SDK.

## Topology

The default development labels represent three cameras mounted approximately 120 degrees apart:

| Camera | Nominal angle | Development input |
| --- | ---: | --- |
| `camera_0` | 0° | `/tmp/gitirl-camera-0.frames` |
| `camera_1` | 120° | `/tmp/gitirl-camera-1.frames` |
| `camera_2` | 240° | `/tmp/gitirl-camera-2.frames` |

Angles are descriptive metadata, not calibrated robot geometry.

## Input boundary

Each input file or FIFO contains repeated frames:

```text
4-byte unsigned big-endian payload length
N opaque frame bytes
```

The script neither interprets nor transcodes the bytes. Ryan and Sarah can initially write development frames into these streams, then replace `LengthPrefixedFrameSource` with a real `CameraFrameSource` after the capture API is known.

## Running

Install the optional WebSocket dependency yourself:

```bash
python3 -m pip install -r requirements.txt
```

Set the endpoint Daniel provides:

```bash
export GITIRL_CAMERA_WS_URL='wss://provided-by-daniel'
export GITIRL_CAMERA_WS_TOKEN='optional-token'
python3 scripts/stream_cameras.py
```

Or supply explicit development streams:

```bash
python3 scripts/stream_cameras.py \
  --camera camera_0:0:/tmp/cam0.frames \
  --camera camera_1:120:/tmp/cam1.frames \
  --camera camera_2:240:/tmp/cam2.frames
```

No server or local listening port is created. The operating system assigns an ephemeral source port to the outbound WebSocket connection.

## Provisional WebSocket frame

Each binary message contains:

```text
magic "GIRL"        4 bytes
wire version         1 byte
JSON header length   4 bytes, unsigned big-endian
JSON header          variable
frame bytes          variable
```

The JSON header carries the stream ID, camera ID, nominal mount angle, sequence, capture timestamp, encoding label, payload size, and metadata. Daniel's final media-ingest contract is authoritative; the codec is isolated in `media/camera_stream.py` so it can be replaced in one place.

## Bandwidth warning

Truly raw video is usually impractical over a hackathon network. Three 1920×1080 RGB streams at 30 FPS are roughly 560 MB/s before protocol overhead. The boundary accepts an encoding label and opaque bytes so the team can later choose JPEG, H.264, WebRTC, or another confirmed format without changing orchestration.

## Still required

From Daniel:

- Media WebSocket endpoint and authentication.
- Final binary/message framing.
- Maximum message size.
- Accepted codecs, resolution, frame rate, and metadata.
- Backpressure, acknowledgement, reconnect, and dropped-frame behavior.

From Ryan and Sarah:

- How all three camera streams are exposed.
- Frame format, dimensions, frame rate, and timestamps.
- Camera identifiers and calibrated mounting/extrinsic information.
- Whether capture already provides compression.
- Whether simultaneous reads are supported and how frames are synchronized.
