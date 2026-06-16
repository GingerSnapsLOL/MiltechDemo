"""Services: lifecycle and correlation rules enforced over the schema contracts."""

from miltech_demo.services.protocol import (
    ProtocolViolationError,
    advance_task_status,
    attach_artifact,
    attach_message,
    validate_artifact_belongs_to_task,
    validate_message_belongs_to_task,
)

__all__ = [
    "ProtocolViolationError",
    "advance_task_status",
    "attach_artifact",
    "attach_message",
    "validate_artifact_belongs_to_task",
    "validate_message_belongs_to_task",
]
