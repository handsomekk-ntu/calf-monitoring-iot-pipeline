from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from pipeline.app import create_app
from pipeline.config import ConfigError, Settings
from pipeline.messages import StatusReading
from pipeline.subscriber import StatusBridge, to_point


def test_point_line_protocol():
    when = datetime(2026, 4, 26, 12, 0, tzinfo=timezone.utc)
    line = to_point(StatusReading("awake", 1), "calf_status", when).to_line_protocol()
    assert line == 'calf_status state_num=1i,state_str="awake" 1777204800000000000'


class Recorder:
    def __init__(self, fail=False):
        self.points = []
        self.fail = fail

    def __call__(self, point):
        if self.fail:
            raise ConnectionError("database down")
        self.points.append(point)


def test_valid_message_is_written():
    rec = Recorder()
    bridge = StatusBridge(rec, "farm/calf/status")
    bridge.on_message(None, None, SimpleNamespace(payload=b'{"state":"asleep"}'))
    assert len(rec.points) == 1
    assert "state_num=0i" in rec.points[0].to_line_protocol()
    snap = bridge.snapshot()
    assert snap["received"] == 1 and snap["rejected"] == 0 and snap["last_state"] == "asleep"


def test_invalid_message_is_counted_not_written():
    rec = Recorder()
    bridge = StatusBridge(rec, "farm/calf/status")
    assert bridge.handle_payload(b"garbage") is False
    assert rec.points == []
    assert bridge.snapshot()["rejected"] == 1


def test_database_error_does_not_kill_the_subscriber():
    bridge = StatusBridge(Recorder(fail=True), "farm/calf/status")
    assert bridge.handle_payload(b"awake") is False
    assert bridge.handle_payload(b"asleep") is False  # still running


def test_subscribes_after_successful_connect():
    subscribed = []
    client = SimpleNamespace(subscribe=lambda topic, qos=0: subscribed.append((topic, qos)))
    bridge = StatusBridge(Recorder(), "farm/calf/status")
    bridge.on_connect(client, None, {}, 0)
    assert subscribed == [("farm/calf/status", 1)]


def test_health_endpoint_reports_last_state():
    bridge = StatusBridge(Recorder(), "farm/calf/status")
    bridge.handle_payload(b"awake")
    body = create_app(bridge).test_client().get("/health").get_json()
    assert body["received"] == 1 and body["last_state"] == "awake"


def test_settings_require_a_token():
    with pytest.raises(ConfigError):
        Settings.from_env({})
    s = Settings.from_env({"INFLUX_TOKEN": "t", "MQTT_PORT": "1884"})
    assert s.mqtt_port == 1884 and s.mqtt_host == "localhost"
