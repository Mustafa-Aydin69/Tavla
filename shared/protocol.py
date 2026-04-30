import json


def encode(msg: dict) -> bytes:
    return (json.dumps(msg) + "\n").encode("utf-8")


def decode(line: str) -> dict:
    return json.loads(line)


# mesaj tipleri

JOIN = "JOIN"
WAITING = "WAITING"
MATCH = "MATCH"
ROLL = "ROLL"
MOVE = "MOVE"
STATE = "STATE"
REJECT = "REJECT"
TURN = "TURN"
GAME_OVER = "GAME_OVER"
