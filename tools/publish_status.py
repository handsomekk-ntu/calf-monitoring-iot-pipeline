"""Publish simulated status messages, to test the broker, database and dashboard
without the camera device.

    python tools/publish_status.py --count 20 --interval 1
"""

import argparse
import json
import random
import time

import paho.mqtt.client as mqtt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="farm/calf/status")
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--interval", type=float, default=1.0, help="seconds between messages")
    args = p.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(args.host, args.port, 60)
    client.loop_start()
    for _ in range(args.count):
        state = random.choice(["awake", "asleep"])
        client.publish(args.topic, json.dumps({"state": state}), qos=1).wait_for_publish()
        print("published", state)
        time.sleep(args.interval)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
