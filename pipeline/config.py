"""Settings from environment variables (see `.env.example`)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "farm/calf/status"
    measurement: str = "calf_status"
    http_port: int = 5000

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        token = env.get("INFLUX_TOKEN", "").strip()
        if not token:
            raise ConfigError("INFLUX_TOKEN is not set (copy .env.example to .env)")
        try:
            mqtt_port = int(env.get("MQTT_PORT", "1883"))
            http_port = int(env.get("HTTP_PORT", "5000"))
        except ValueError as exc:
            raise ConfigError(f"Port must be an integer: {exc}") from exc
        return cls(
            influx_url=env.get("INFLUX_URL", "http://localhost:8086"),
            influx_token=token,
            influx_org=env.get("INFLUX_ORG", "my_farm"),
            influx_bucket=env.get("INFLUX_BUCKET", "calf_data"),
            mqtt_host=env.get("MQTT_HOST", "localhost"),
            mqtt_port=mqtt_port,
            mqtt_topic=env.get("MQTT_TOPIC", "farm/calf/status"),
            http_port=http_port,
        )
