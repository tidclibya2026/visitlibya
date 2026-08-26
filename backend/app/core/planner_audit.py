import logging
from typing import Any


logger = logging.getLogger("visitlibya.planner.audit")


def log_planner_event(
    event: str,
    *,
    actor_id: int,
    request_id: str | None = None,
    **identifiers: Any,
) -> None:
    """Log allowlisted planner metadata; snapshots and credentials are never accepted."""
    fields = [f"event={event}", f"actor_id={actor_id}"]
    if request_id:
        fields.append(f"request_id={request_id}")
    for name in (
        "destination_id",
        "planner_run_id",
        "trip_id",
        "status",
        "verification_status",
    ):
        value = identifiers.get(name)
        if value is not None:
            fields.append(f"{name}={value}")
    logger.info("planner_event %s", " ".join(fields))

