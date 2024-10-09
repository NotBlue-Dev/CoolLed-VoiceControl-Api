import base64
import json
import re

def bytes_to_base64(byte_array):
    return base64.b64encode(byte_array).decode('utf-8')

def file_to_base64(filepath, slot):
    # Open the file in binary read mode
    if slot == "Image":
        finalFilePath = "assets/image/" + filepath
    elif slot == "Anim":
        finalFilePath = "assets/animations/" + filepath
    with open(finalFilePath, 'rb') as file:
        file_content = file.read()

    # Encode the content
    encoded_content = base64.b64encode(file_content)
    # Convert to string for easier handling
    return encoded_content.decode()

def process_payload(data, file=None, slot=None):
    
    base64_lists = [base64.b64encode(element).decode('utf-8') for element in data]
    json_data = json.dumps({"bytes": base64_lists})
    if file and slot:
        json_data = json.dumps({"bytes": base64_lists, "file": file_to_base64(file, slot)})

    return json_data

def split_bytearray(content, chunksize):
    # create a liste with one entry
    chunks = [content]
    # split the last chunk as long as it is larger than chunksize
    while (True):
        i = len(chunks) - 1
        if (len(chunks[i]) > chunksize):
            chunks.append(chunks[i][chunksize:])
            chunks[i] = chunks[i][:chunksize]
        else:
            return chunks


def get_xor_checksum(content):
    sum = 0
    for b in content:
        sum ^= b
    return sum


def escape_bytefield(data):
    data = re.sub(re.compile(b'\x02', re.MULTILINE), b'\x02\x06', data)  # needs to be first
    data = re.sub(re.compile(b'\x01', re.MULTILINE), b'\x02\x05', data)
    data = re.sub(re.compile(b'\x03', re.MULTILINE), b'\x02\x07', data)
    return data
