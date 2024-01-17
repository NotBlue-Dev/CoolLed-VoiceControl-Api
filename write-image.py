#!/usr/bin/env python3
import base64
import re
import sys
from PIL import Image, ImageDraw, ImageFont, ImageColor, GifImagePlugin
import websockets
import asyncio
import json
import binascii

CONTENT_TYPE_MUSIC   =  1 
CONTENT_TYPE_TEXT    =  2
CONTENT_TYPE_DRAW    =  3 
CONTENT_TYPE_ANIMATE =  4
CONTENT_TYPE_ICON    =  5 
CONTENT_TYPE_MODE    =  6 
CONTENT_TYPE_SPEED   =  7 
CONTENT_TYPE_BRIGHT  =  8 
CONTENT_TYPE_SWITCH  =  9 
CONTENT_TYPE_XFER    = 10

def split_bytearray(content, chunksize):
    # create a liste with one entry
    chunks = [content]
    # split the last chunk as long as it is larger than chunksize
    while (True):
        i = len(chunks)-1
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
    data = re.sub(re.compile(b'\x02', re.MULTILINE), b'\x02\x06', data) # needs to be first
    data = re.sub(re.compile(b'\x01', re.MULTILINE), b'\x02\x05', data)
    data = re.sub(re.compile(b'\x03', re.MULTILINE), b'\x02\x07', data)
    return data


def encapsulate_payload(payload):    
    # size of the payload
    download_size = len(payload).to_bytes(2, byteorder='big')                  
    # join the payload with the size
    download_payload = bytearray().join([download_size, payload])    
    # escape the joined payload
    download_payload = escape_bytefield(download_payload)        
    # the full payload also needs start and stop markers
    return bytearray().join([b'\x01', download_payload, b'\x03'])

####################################################

# just a test to see if we can interpret image 
def print_pixels(im):
    imWidth, imHeight = im.size
    
    print ("8-color Pixel Data from Image")
    
    for y in range(0, imHeight):     
        for x in range(0, imWidth):        
            
            px = im.getpixel((x, y))
            
            rb = int(round(px[0]/255)) 
            gb = int(round(px[1]/255)) 
            bb = int(round(px[2]/255)) 
            
            bits = rb*1 + gb*2 + bb*4
            
            print(bits, end=' ')
            
        print('')


def renderTextToImage(txt, color):
    
    y_offset = -2
    color = ImageColor.getrgb(color)

    # create image canvas    
    img = Image.new('RGBA', (2048, 64))
    draw = ImageDraw.Draw(img)
    # write the text on the canvas (TODO font is a bit ugly as of now) 
    
    #font = ImageFont.load_default()
    x = 0
    font = ImageFont.truetype("/sdcard/Cooled/Montserrat-Medium.ttf", 15)
    for letter in txt:
        draw.text((x, y_offset), letter, color, font=font)
        x += font.getsize(letter)[0] + 1

    del draw
    # crop the canvas
    left, upper, right, lower = img.getbbox()
    return img.crop((0,0,right,lower))


# width/height are defining the size of the hardware, 
#the image will be cropped, or pixels will be replacesd with default
# single images width is arbitrary, for animations this has to be 32
def get_separate_pixel_bytefields(img, width=32, height=16, bgColor="black"):
    
    if (height % 8 != 0):
        print("ERROR: target-height needs to be divisible by 8")
        exit(1)
    
    imWidth, imHeight = img.size
    defaultPx = ImageColor.getrgb(bgColor)
    
    # buffer to hold the separate pixels
    barr_R, barr_G, barr_B  = bytearray(), bytearray(), bytearray()
    
    # temp values to shift the separate color bits while we iterate the pixels    
    tmp_R, tmp_G, tmp_B  = 0, 0, 0
        
    # iterate column from top to bottom (first 2 bytes will be the left column, most significant bit will be pixel on the top)
    for x in range(0, width):
        for y in range(0, height):
            # replace pixels outside image with default    
            if (y < imHeight and x < imWidth):
                px =  img.getpixel((x, y))
            else:
                px = defaultPx
            
            # for each color, add one bit for the current pixel (1 if color-component is > 127)
            tmp_R = (tmp_R << 1) + int(round(px[0]/255))
            tmp_G = (tmp_G << 1) + int(round(px[1]/255))
            tmp_B = (tmp_B << 1) + int(round(px[2]/255))
            
            # for every 8th pixel, add the byte to the bytefield and begin a new one
            if (y % 8 == 7):
                barr_R.append(tmp_R)
                barr_G.append(tmp_G)
                barr_B.append(tmp_B)
                tmp_R, tmp_G, tmp_B  = 0, 0, 0

    return barr_R, barr_G, barr_B


# returns 3 separate bytefield for all color bits of the animations
def get_separate_pixel_bytefields_for_animation(anim):
    
    is_animated = getattr(anim, 'is_animated', False)

    #print ("animation has {} frames".format(anim.n_frames))
    
    combined_image = None
    
    animR, animG, animB  = bytearray(), bytearray(), bytearray()
    
    for frame in range(0, anim.n_frames):

        # switch to next frame
        anim.seek(frame)        
        
        # it seems we have to care about applying the transparent pixels ourselves 
        if (combined_image is None):
            combined_image = anim.convert('RGBA')
        else:        
            combined_image = Image.alpha_composite(combined_image, anim.convert('RGBA'))
        
        print ("Frame {}".format(frame))
        print_pixels(combined_image)
        
        # anims are always 32x16
        frameR, frameG, frameB = get_separate_pixel_bytefields(combined_image, 32, 16)
#        for i in range(0, len(frameR), 2):
#            print ("{0:08b}{1:08b}  {2:08b}{3:08b}  {4:08b}{5:08b}".format(frameR[i],frameR[i+1], frameG[i],frameG[i+1], frameB[i],frameB[i+1]))
            
        animR += frameR
        animG += frameG
        animB += frameB

    # returns all-pixels of all frames separately for each of the 3 color-components
    return animR, animG, animB

def get_transport_payloads_for_content(content_type_id, content):
    
    print("raw before chunks: "+content.hex())
    
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

    print([x.hex() for x in download_payloads])
    return download_payloads

def createTextPayload(txt, color):
    
    color = color or "white"
    im = renderTextToImage(txt, color)
        
    imWidth, imHeight = im.size
    bR, bG, bB = get_separate_pixel_bytefields(im, imWidth, 16, "black")   # we only fix the height, witdh is dynamic     

    # all the pixel-bits, first red then green than blue
    pixel_bits_all = bytearray().join([bR, bG, bB])

    
    # create the image payload
    pixel_payload = bytearray()
    # unknown 24 zero-bytes
    pixel_payload += bytearray(24)    
        
    # length of string (pretty much irrelevant because the image will be used anyway)
    pixel_payload += len(txt).to_bytes(1, byteorder='big')
    
    # character string (pretty much irrelevant because the image will be used anyway)
    char_metadata = bytearray(80)
    for i, c in enumerate(txt):
        if (i<80):
            char_metadata[i] = 0x30
    pixel_payload += char_metadata

    # size of the pixel payload in it's un-split form.
    pixel_payload += len(pixel_bits_all).to_bytes(2, byteorder='big')
    # all the pixel-bits
    pixel_payload += pixel_bits_all
    # split image data in command-chunks (type: TEXT)
    return get_transport_payloads_for_content(CONTENT_TYPE_TEXT, pixel_payload)


def createImagePayload(filename):
        
    im = Image.open(filename).convert('RGB')    
    
    imWidth, imHeight = im.size
    bR, bG, bB = get_separate_pixel_bytefields(im, imWidth, 16, "black")   # we only fix the height, witdh is dynamic     

    # all the pixel-bits, first red then green than blue
    pixel_bits_all = bytearray().join([bR, bG, bB])
    
    # create the image payload
    pixel_payload = bytearray()    
    # unknown 24 zero-bytes
    pixel_payload += bytearray(24)    
    # size of the pixel payload in it's un-split form.
    pixel_payload += len(pixel_bits_all).to_bytes(2, byteorder='big')
    # all the pixel-bits
    pixel_payload += pixel_bits_all

        
    # split image data in command-chunks (type: DRAW)  
    return get_transport_payloads_for_content(CONTENT_TYPE_DRAW, pixel_payload)    



def createAnimationPayload(filename, speed=512):
        
    anim = Image.open(filename)
    frames = anim.n_frames        
    animR, animG, animB = get_separate_pixel_bytefields_for_animation(anim)   
    # all the pixel-bits, first red then green than blue
    pixel_bits_all = bytearray().join([animR, animG, animB])

        
    # create the image payload
    pixel_payload = bytearray()    
    # unknown 24 zero-bytes
    pixel_payload += bytearray(24) 
    # number of frames
    pixel_payload += frames.to_bytes(1, byteorder='big')
    # speed (16-bit)
    pixel_payload += speed.to_bytes(2, byteorder='big')
    # all the pixel-bits
    pixel_payload += pixel_bits_all

    
    # split image data in command-chunks (type: ANIMATE)  
    return get_transport_payloads_for_content(CONTENT_TYPE_ANIMATE, pixel_payload)

connected_clients = set()


def bytes_to_base64(byte_array):
    return base64.b64encode(byte_array).decode('utf-8')
async def recv(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            obj = json.loads(message)
            data = None
            if obj["slot"] == "Write":
                data = createTextPayload(obj["value"], obj["color"])
            elif obj["slot"] == "Image":
                data = createImagePayload(obj["value"])
            elif obj["slot"] == "Anim":
                data = createAnimationPayload(obj["value"], 250)
            elif obj["slot"] == "Speed":
                command = bytearray().join([b'\x07', int(obj["value"]).to_bytes(1, byteorder='big')])
                payload = encapsulate_payload(command)
                data = [payload]
            elif obj["slot"] == "Mode":
                command = bytearray().join([b'\x06', int(obj["value"]).to_bytes(1, byteorder='big')])
                payload = encapsulate_payload(command)
                data = [payload]
            elif obj["slot"] == "Brightness":
                command = bytearray().join([b'\x08', int(obj["value"]).to_bytes(1, byteorder='big')])
                payload = encapsulate_payload(command)
                data = [payload]
            elif obj["slot"] == "State":
                if(obj["value"] == "Off"):
                    data = [bytearray(b'\x01\x00\x02\x06\x09\x00\x03')]
                else:
                    data = [bytearray(b'\x01\x00\x02\x06\x09\x02\x05\x03')]
            try:
                base64_lists = [base64.b64encode(element).decode('utf-8') for element in data]
                json_data = json.dumps(base64_lists)
            except:
                json_data = "[]"
            await asyncio.wait([client.send(json_data) for client in connected_clients])
    finally:
        # Unregister client on disconnect
        connected_clients.remove(websocket)

async def send_data_to_clients(data):
    if connected_clients:  # Check if there are any clients connected
        await asyncio.wait([client.send(data) for client in connected_clients])

start_server = websockets.serve(recv, "localhost", 7681)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().create_task(send_data_to_clients("test"))
asyncio.get_event_loop().run_forever()


