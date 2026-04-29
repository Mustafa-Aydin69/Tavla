import json

def encode(msg:dict)->bytes:
    return (json.dumps(msg) + "\n").encode("utf-8")

def decode(data:bytes)->dict:
    if isinstance(data,bytes):
        data = data.decode("utf-8")
    return json.loads(data.strip())


#mesaj tipleri

JOIN = "JOIN"
WAITING = "WAITING"
MATCH = "MATCH"
ROLL="ROLL"
MOVE = "MOVE"
STATE = "STATE"
REJECT = "REJECT"
TURN = "TURN"
GAME_OVER = "GAME_OVER"



    