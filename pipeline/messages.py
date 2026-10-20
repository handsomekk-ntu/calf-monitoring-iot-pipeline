"""Parse the status messages the edge device publishes over MQTT.

The device may send either JSON (`{"state": "awake"}`) or plain text (`awake`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

STATE_VALUES = {"awake": 1, "asleep": 0}


@dataclass(frozen=True)
class StatusReading:
    state: str   # "awake" or "asleep"
    value: int   # 1 = awake, 0 = asleep (numeric field for Grafana graphs)


def parse_status(payload: bytes | str) -> StatusReading | None:
    """Return the reading, or None if the message is not a known state."""
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            return None
    raw = payload.strip()

    state = raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        state = str(data.get("state", "")).strip()
    elif isinstance(data, str):
        state = data.strip()

    state = state.lower()
    if state not in STATE_VALUES:
        return None
    return StatusReading(state=state, value=STATE_VALUES[state])
