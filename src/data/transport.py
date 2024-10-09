import re
import asyncio
from ..utils import split_bytearray, escape_bytefield, get_xor_checksum

CONTENT_TYPE_TEXT = 0x00
CONTENT_TYPE_DRAW = 0x01
CONTENT_TYPE_ANIMATE = 0x02

def encapsulate_payload(payload):
    length = len(payload)
    checksum = 0
    for byte in payload:
        checksum ^= byte
    payload = bytearray([0x01]) + payload + bytearray([length & 0xFF, checksum])
    return payload

def get_transport_payloads_for_content(content_type_id, content):
    # split the content into (128-byte) chunks
    raw_chunks = split_bytearray(content, 128)

    # add header information to the chunks
    download_payloads = list()
    for chunk_id, raw_chunk in enumerate(raw_chunks):
        # create bytearray of for the content of the chunk including checksum
        formatted_chunk = bytearray()
        # unknown single 0x00 byte TODO
        formatted_chunk += b'\x00'
        # length of the playload before it was split (16-bit)
        formatted_chunk += len(content).to_bytes(2, byteorder='big')
        # current chunk-number (16-bit)
        formatted_chunk += chunk_id.to_bytes(2, byteorder='big')
        # size of the chunk (8-bit)
        formatted_chunk += len(raw_chunk).to_bytes(1, byteorder='big')
        # the data of the chunk
        formatted_chunk += raw_chunk
        # append XOR checksum to make the complete the formatted chunk
        formatted_chunk.append(get_xor_checksum(formatted_chunk))

        # create transfer command for the chunk
        download_payload = bytearray()
        # size of the formatted_chunk plus command
        download_payload += (len(formatted_chunk) + 1).to_bytes(2, byteorder='big')
        # command ID as defined in argument
        download_payload += content_type_id.to_bytes(1, byteorder='big')
        # rest of the chunk
        download_payload += formatted_chunk

        # escape the payload
        download_payload = escape_bytefield(download_payload)

        # add start/stop markers to the escaped payloads and add it to the list
        full_payload = bytearray().join([b'\x01', download_payload, b'\x03'])
        download_payloads.append(full_payload)

    return download_payloads