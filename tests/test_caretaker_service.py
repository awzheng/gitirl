import unittest

from src.gitirl_agent.caretaker.service import CaretakerJobError, CaretakerService
from src.gitirl_agent.robot.mock import MockRobotAdapter
from src.gitirl_agent.state.models import ObjectState, WorldState


class CaretakerServiceTests(unittest.TestCase):
    def setUp(self):
        self.robot = MockRobotAdapter(
            WorldState(objects=(ObjectState("box_A", label="box", position="Y"),))
        )
        self.service = CaretakerService(self.robot)

    def test_executes_daniel_point_job(self):
        result = self.service.execute(
            {
                "job_id": "job_point",
                "command": "point",
                "object_id": "keys_7c2e",
                "target_pose": {"x": 0.8, "y": 0.3, "z": 0.9},
                "zone": "shelf",
            }
        )
        self.assertEqual(result.status, "succeeded")
        self.assertEqual(self.robot.execute_calls, 1)

    def test_duplicate_job_is_not_executed_twice(self):
        job = {
            "job_id": "job_move",
            "command": "move",
            "ops": [
                {
                    "op": "moved",
                    "object_id": "box_A",
                    "class": "box",
                    "from": {"x": 0, "y": 0, "z": 0},
                    "to": {"x": 1, "y": 0, "z": 0},
                }
            ],
        }
        first = self.service.execute(job)
        second = self.service.execute(job)
        self.assertIs(first, second)
        self.assertEqual(self.robot.execute_calls, 1)

    def test_unsupported_job_never_reaches_robot(self):
        with self.assertRaises(CaretakerJobError):
            self.service.execute(
                {
                    "job_id": "job_bad",
                    "command": "dance",
                    "ops": [{"op": "added", "object_id": "box_A"}],
                }
            )
        self.assertEqual(self.robot.execute_calls, 0)

    def test_multiple_moves_are_rejected_for_mvp(self):
        operation = {
            "op": "moved",
            "object_id": "box_A",
            "from": {"x": 0, "y": 0, "z": 0},
            "to": {"x": 1, "y": 0, "z": 0},
        }
        with self.assertRaisesRegex(CaretakerJobError, "exactly one"):
            self.service.execute(
                {
                    "job_id": "job_many",
                    "command": "move",
                    "ops": [operation, {**operation, "object_id": "box_B"}],
                }
            )
        self.assertEqual(self.robot.execute_calls, 0)


if __name__ == "__main__":
    unittest.main()
