import logging

from app.core.planner_audit import log_planner_event


def test_planner_event_logs_only_allowlisted_metadata(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="visitlibya.planner.audit"):
        log_planner_event(
            "planner_run_created",
            actor_id=7,
            request_id="request-1",
            planner_run_id=8,
            trip_id=9,
            status="generated",
            input_snapshot={"secret": "must-not-log"},
            token="must-not-log",
        )
    message = caplog.messages[-1]
    assert "event=planner_run_created" in message
    assert "actor_id=7" in message and "request_id=request-1" in message
    assert "planner_run_id=8" in message and "status=generated" in message
    assert "secret" not in message and "token" not in message
