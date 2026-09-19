"""Provisional HTTP/JSON contract between gitirl-agent and robot control."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from src.gitirl_agent.planner.models import (
    ActionResult,
    ActionStatus,
    ActionType,
    RobotAction,
)
from src.gitirl_agent.state.models import ObjectState, WorldState
from src.gitirl_agent.state.serialization import (
    world_state_from_dict,
    world_state_to_dict,
)


ROBOT_API_VERSION = 1


class RobotContractError(ValueError):
    """A robot API document is malformed or uses an unsupported version."""


def robot_action_to_dict(action: RobotAction) -> Dict[str, Any]:
    return {
        "action_type": action.action_type.value,
        "request_id": action.request_id,
        "object_id": action.object_id,
        "source": _object_to_dict(action.source),
        "target": _object_to_dict(action.target),
        "metadata": dict(action.metadata),
    }


def robot_action_from_dict(value: Mapping[str, Any]) -> RobotAction:
    try:
        action_type = ActionType(value.get("action_type"))
    except (TypeError, ValueError) as error:
        raise RobotContractError("action_type is invalid") from error
    request_id = value.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise RobotContractError("request_id must be a non-empty string")
    object_id = value.get("object_id")
    if object_id is not None and not isinstance(object_id, str):
        raise RobotContractError("object_id must be a string when supplied")
    return RobotAction(
        action_type=action_type,
        request_id=request_id,
        object_id=object_id,
        source=_object_from_value(value.get("source")),
        target=_object_from_value(value.get("target")),
        metadata=_mapping(value.get("metadata")),
    )


def action_result_to_dict(result: ActionResult) -> Dict[str, Any]:
    return {
        "status": result.status.value,
        "message": result.message,
        "observations": (
            world_state_to_dict(result.observations)
            if result.observations is not None
            else None
        ),
    }


def action_result_from_dict(value: Mapping[str, Any]) -> ActionResult:
    try:
        status = ActionStatus(value.get("status"))
    except (TypeError, ValueError) as error:
        raise RobotContractError("action result status is invalid") from error
    message = value.get("message", "")
    if not isinstance(message, str):
        raise RobotContractError("action result message must be a string")
    observations = value.get("observations")
    if observations is not None and not isinstance(observations, dict):
        raise RobotContractError("action result observations must be an object")
    return ActionResult(
        status=status,
        message=message,
        observations=(
            world_state_from_dict(observations)
            if isinstance(observations, dict)
            else None
        ),
    )


def observation_response(request_id: str, state: WorldState) -> Dict[str, Any]:
    return {
        "version": ROBOT_API_VERSION,
        "request_id": request_id,
        "observation": world_state_to_dict(state),
    }


def action_request(action: RobotAction) -> Dict[str, Any]:
    return {
        "version": ROBOT_API_VERSION,
        "request_id": action.request_id,
        "action": robot_action_to_dict(action),
    }


def action_response(request_id: str, result: ActionResult) -> Dict[str, Any]:
    return {
        "version": ROBOT_API_VERSION,
        "request_id": request_id,
        "result": action_result_to_dict(result),
    }


def require_envelope(value: Any, request_id: Optional[str] = None) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise RobotContractError("response must be a JSON object")
    if value.get("version") != ROBOT_API_VERSION:
        raise RobotContractError("unsupported robot API version")
    actual_id = value.get("request_id")
    if not isinstance(actual_id, str) or not actual_id:
        raise RobotContractError("response requires request_id")
    if request_id is not None and actual_id != request_id:
        raise RobotContractError("response request_id does not match request")
    return value


def error_document(code: str, detail: str, retryable: bool = False) -> Dict[str, Any]:
    return {"error": code, "detail": detail, "retryable": retryable}


def _object_to_dict(value: Optional[ObjectState]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    return world_state_to_dict(WorldState(objects=(value,)))["objects"][0]


def _object_from_value(value: Any) -> Optional[ObjectState]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise RobotContractError("source and target must be objects")
    return world_state_from_dict({"objects": [value]}).objects[0]


def _mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RobotContractError("metadata must be an object")
    return value
