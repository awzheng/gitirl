import unittest

from src.gitirl_agent.transport.sse import SSEEvent, encode_sse, parse_sse


class SSETests(unittest.TestCase):
    def test_parse_daniel_event_shape(self):
        lines = [
            b"id: boot-7\n",
            b"event: job\n",
            b'data: {"id":"job_1","state":"done"}\n',
            b"\n",
        ]

        event = next(parse_sse(lines))

        self.assertEqual(event.event, "job")
        self.assertEqual(event.event_id, "boot-7")
        self.assertEqual(event.data["state"], "done")

    def test_encode_then_parse(self):
        expected = SSEEvent(
            "status", {"clean": False, "changes": 3}, "boot-8", 2000
        )

        actual = next(parse_sse(encode_sse(expected).splitlines(keepends=True)))

        self.assertEqual(actual, expected)

    def test_comments_are_heartbeats_not_events(self):
        self.assertEqual(list(parse_sse([b": keepalive\n", b"\n"])), [])


if __name__ == "__main__":
    unittest.main()
