from fastapi import FastAPI
from pydantic import BaseModel
from .data import createTextPayload, createImagePayload, createAnimationPayload, encapsulate_payload
from .utils import process_payload

app = FastAPI()

class Message(BaseModel):
    value: str
    color: str = None

class Value(BaseModel):
    value: int

class StrValue(BaseModel):
    value: str

@app.post("/write")
async def write_message(message: Message):
    data = createTextPayload(message.value, message.color)
    return process_payload(data)

@app.post("/image")
async def image_message(message: Message):
    data = createImagePayload(message.value)
    return process_payload(data, message.value, "Image")

@app.post("/anim")
async def anim_message(message: Message):
    data = createAnimationPayload(message.value, 250)
    return process_payload(data, message.value, "Anim")

@app.post("/speed")
async def speed_message(message: Value):
    command = bytearray().join([b'\x07', message.value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/mode")
async def mode_message(message: Value):
    command = bytearray().join([b'\x06', message.value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/brightness")
async def brightness_message(message: Value):
    command = bytearray().join([b'\x08', message.value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/state")
async def state_message(message: StrValue):
    if message.value == "Off":
        data = [bytearray(b'\x01\x00\x02\x06\x09\x00\x03')]
    else:
        data = [bytearray(b'\x01\x00\x02\x06\x09\x02\x05\x03')]
    return process_payload(data)