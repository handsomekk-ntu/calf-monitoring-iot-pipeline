"""Print every message on the status topic. Useful to check the device -> broker link.

    python tools/mqtt_monitor.py --host 192.168.1.20
"""

import argparse

import paho.mqtt.client as mqtt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="farm/calf/status")
    args = p.parse_args()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"connected ({reason_code}), subscribing to {args.topic}")
        client.subscribe(args.topic)

    def on_message(client, userdata, msg):
        print(f"{msg.topic}: {msg.payload.decode(errors='replace')}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
