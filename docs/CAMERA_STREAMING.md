# Deferred camera HTTP sender

This is a scaffold, not a production video pipeline. Do not build it further until Daniel and the robot team decide media ownership.

Confirmed BBOS JPEG topics are:

- `camera.head.jpeg` — stereo head camera
- `camera.left.jpeg` — left arm camera
- `camera.right.jpeg` — right arm camera

These are **not** confirmed as a 120-degree or 360° arrangement. Mounting/extrinsics are unknown.

If Daniel provides an HTTP upload endpoint, the read-only smoke path is:

```bash
GITIRL_CAMERA_HTTP_URL=http://HOST/PATH \
PYTHONPATH=/home/bracketbot/bbos \
python3 scripts/stream_cameras.py --bbos
```

Each frame is one ordinary HTTP `POST` with `Content-Type: application/octet-stream`. The body contains a small length-prefixed JSON header followed by the unchanged frame bytes. There is no persistent connection, stitching, capture control, or retry queue.

SSE is not used for camera bytes. Daniel still needs to define the endpoint, authentication, media type, size/rate limits, backpressure, and acknowledgement behavior.
