"""MQTT -> InfluxDB bridge.

The edge device only publishes a short status string, so the link stays usable
on a weak farm network. This process subscribes to the topic, validates each
message, and writes it to InfluxDB as one point.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

import paho.mqtt.client as mqtt
from influxdb_client import Point

from .messages import StatusReading, parse_status

log = logging.getLogger(__name__)


def to_point(reading: StatusReading, measurement: str = "calf_status",
             when: datetime | None = None) -> Point:
    point = (
        Point(measurement)
        .field("state_str", reading.state)
        .field("state_num", reading.value)
    )
    if when is not None:
        point = point.time(when)
    return point


class StatusBridge:
    """Receives MQTT messages and hands valid readings to `write(point)`."""

    def __init__(self, write: Callable[[Point], None], topic: str, measurement: str = "calf_status"):
        self.write = write
        self.topic = topic
        self.measurement = measurement
        self.received = 0
        self.rejected = 0
        self.last_reading: StatusReading | None = None
        self.last_time: datetime | None = None
        self._lock = threading.Lock()

    # paho-mqtt callback API v2
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            log.info("Connected to MQTT broker, subscribing to %s", self.topic)
            client.subscribe(self.topic, qos=1)
        else:
            log.error("MQTT connection refused: %s", reason_code)

    def on_message(self, client, userdata, msg):
        self.handle_payload(msg.payload)

    def handle_payload(self, payload: bytes | str) -> bool:
        reading = parse_status(payload)
        with self._lock:
            self.received += 1
            if reading is None:
                self.rejected += 1
                log.warning("Ignored unknown status payload: %r", payload)
                return False
            now = datetime.now(timezone.utc)
            self.last_reading, self.last_time = reading, now
        try:
            self.write(to_point(reading, self.measurement, now))
        except Exception:  # keep the subscriber alive if the database hiccups
            log.exception("Writing to InfluxDB failed")
            return False
        return True

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "received": self.received,
                "rejected": self.rejected,
                "last_state": self.last_reading.state if self.last_reading else None,
                "last_time": self.last_time.isoformat() if self.last_time else None,
            }


def make_client(bridge: StatusBridge, client_id: str = "calf-backend") -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.on_connect = bridge.on_connect
    client.on_message = bridge.on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)  # survive network drops
    return client
