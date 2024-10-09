from fastapi import FastAPI
from pydantic import BaseModel
from payloads import createTextPayload, createImagePayload, createAnimationPayload
from transport import encapsulate_payload
from src.utils.utils_bytes import process_payload

app = FastAPI()

class Message(BaseModel):
    slot: str
    value: str
    color: str = None  # Optional for Write

@app.post("/write")
async def write_message(message: Message):
    data = createTextPayload(message.value, message.color)
    return process_payload(data)

@app.post("/image")
async def image_message(message: Message):
    data = createImagePayload(message.value)
    return process_payload(data, message.value, message.slot)

@app.post("/anim")
async def anim_message(message: Message):
    data = createAnimationPayload(message.value, 250)
    return process_payload(data, message.value, message.slot)

@app.post("/speed")
async def speed_message(value: int):
    command = bytearray().join([b'\x07', value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/mode")
async def mode_message(value: int):
    command = bytearray().join([b'\x06', value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/brightness")
async def brightness_message(value: int):
    command = bytearray().join([b'\x08', value.to_bytes(1, byteorder='big')])
    payload = encapsulate_payload(command)
    return process_payload([payload])

@app.post("/state")
async def state_message(value: str):
    if value == "Off":
        data = [bytearray(b'\x01\x00\x02\x06\x09\x00\x03')]
    else:
        data = [bytearray(b'\x01\x00\x02\x06\x09\x02\x05\x03')]
    return process_payload(data)