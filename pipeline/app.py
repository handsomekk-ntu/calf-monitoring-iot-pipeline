"""Backend entry point: MQTT subscriber + InfluxDB writer + a small health page.

    python -m pipeline.app
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify

from .config import Settings
from .subscriber import StatusBridge, make_client

log = logging.getLogger(__name__)


def create_app(bridge: StatusBridge) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home():
        return "Calf monitoring backend is running"

    @app.get("/health")
    def health():
        return jsonify(bridge.snapshot())

    return app


def main() -> None:  # pragma: no cover - needs a running broker and database
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS

    settings = Settings.from_env()
    db = InfluxDBClient(url=settings.influx_url, token=settings.influx_token, org=settings.influx_org)
    write_api = db.write_api(write_options=SYNCHRONOUS)

    def write(point):
        write_api.write(bucket=settings.influx_bucket, org=settings.influx_org, record=point)

    bridge = StatusBridge(write, settings.mqtt_topic, settings.measurement)
    client = make_client(bridge)
    client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_start()
    log.info("Listening on mqtt://%s:%s/%s", settings.mqtt_host, settings.mqtt_port, settings.mqtt_topic)
    try:
        create_app(bridge).run(host="0.0.0.0", port=settings.http_port)
    finally:
        client.loop_stop()
        db.close()


if __name__ == "__main__":  # pragma: no cover
    main()
