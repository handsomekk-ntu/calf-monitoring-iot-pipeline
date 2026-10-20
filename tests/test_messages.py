import pytest

from pipeline.messages import StatusReading, parse_status


@pytest.mark.parametrize(
    "payload, expected",
    [
        (b'{"state": "awake"}', StatusReading("awake", 1)),
        (b'{"state": "asleep"}', StatusReading("asleep", 0)),
        (b"awake", StatusReading("awake", 1)),          # plain text is accepted too
        (b"  ASLEEP \n", StatusReading("asleep", 0)),    # case and whitespace
        ('"awake"', StatusReading("awake", 1)),          # JSON string
        ("awake", StatusReading("awake", 1)),            # str instead of bytes
    ],
)
def test_known_states(payload, expected):
    assert parse_status(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        b'{"temperature": 25}',   # JSON without a state
        b"123",                   # JSON number (raised an error in the first version)
        b"[1, 2]",                # JSON list
        b"not awake",             # contains "awake" but is not a state
        b"",
        b"\xff\xfe",              # not UTF-8
    ],
)
def test_unknown_payloads_are_rejected(payload):
    assert parse_status(payload) is None
