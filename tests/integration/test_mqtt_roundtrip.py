"""End-to-end through a real Mosquitto broker:
publisher -> broker -> StatusBridge -> (fake) database writer.

Runs only when MQTT_TEST_PORT is set, e.g.
    mosquitto -p 18830 -d
    MQTT_TEST_PORT=18830 pytest -m integration
"""

import json
import os
import threading
import time
import uuid

import paho.mqtt.client as mqtt
import pytest

from pipeline.subscriber import StatusBridge, make_client

PORT = os.environ.get("MQTT_TEST_PORT")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not PORT, reason="set MQTT_TEST_PORT to run against a real broker"),
]


def test_messages_flow_from_publisher_to_database():
    topic = f"test/calf/{uuid.uuid4().hex}"
    written = []
    got_three = threading.Event()

    def write(point):
        written.append(point.to_line_protocol())
        if len(written) == 3:
            got_three.set()

    bridge = StatusBridge(write, topic)
    sub = make_client(bridge, client_id=f"sub-{uuid.uuid4().hex[:8]}")
    subscribed = threading.Event()
    sub.on_subscribe = lambda *a, **k: subscribed.set()
    sub.connect("localhost", int(PORT), 30)
    sub.loop_start()
    try:
        assert subscribed.wait(5), "subscriber never subscribed"

        pub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        pub.connect("localhost", int(PORT), 30)
        pub.loop_start()
        for payload in (json.dumps({"state": "awake"}), "garbage", "asleep", json.dumps({"state": "awake"})):
            pub.publish(topic, payload, qos=1).wait_for_publish(5)
        pub.loop_stop()
        pub.disconnect()

        assert got_three.wait(5), f"only {len(written)} points written"
    finally:
        sub.loop_stop()
        sub.disconnect()

    time.sleep(0.2)
    assert [("state_num=1i" in w, "state_num=0i" in w) for w in written] == [
        (True, False), (False, True), (True, False)
    ]
    assert bridge.snapshot()["rejected"] == 1
