from .transport import get_transport_payloads_for_content, CONTENT_TYPE_TEXT, CONTENT_TYPE_DRAW, CONTENT_TYPE_ANIMATE
from ..image import get_separate_pixel_bytefields_for_animation, renderTextToImage, get_separate_pixel_bytefields
from PIL import Image

def createTextPayload(txt, color):
    color = color or "white"
    im = renderTextToImage(txt, color)
    
    imWidth, imHeight = im.size
    bR, bG, bB = get_separate_pixel_bytefields(im, imWidth, 16, "black")
    pixel_bits_all = bytearray().join([bR, bG, bB])

    pixel_payload = bytearray()
    pixel_payload += bytearray(24)
    pixel_payload += len(txt).to_bytes(1, byteorder='big')
    char_metadata = bytearray(80)
    for i, c in enumerate(txt):
        if (i < 80):
            char_metadata[i] = 0x30
    pixel_payload += char_metadata
    pixel_payload += len(pixel_bits_all).to_bytes(2, byteorder='big')
    pixel_payload += pixel_bits_all

    return get_transport_payloads_for_content(CONTENT_TYPE_TEXT, pixel_payload)

def createImagePayload(filename):
    im = None
    try:
        im = Image.open(f"assets/image/{filename}").convert('RGB')
    except:
        return []

    imWidth, imHeight = im.size
    bR, bG, bB = get_separate_pixel_bytefields(im, imWidth, 16, "black")
    pixel_bits_all = bytearray().join([bR, bG, bB])

    pixel_payload = bytearray()
    pixel_payload += bytearray(24)
    pixel_payload += len(pixel_bits_all).to_bytes(2, byteorder='big')
    pixel_payload += pixel_bits_all

    return get_transport_payloads_for_content(CONTENT_TYPE_DRAW, pixel_payload)

def createAnimationPayload(filename, speed=512):
    anim = None
    try:
        anim = Image.open(f"assets/animations/{filename}")
    except:
        return

    frames = anim.n_frames
    animR, animG, animB = get_separate_pixel_bytefields_for_animation(anim)
    pixel_bits_all = bytearray().join([animR, animG, animB])

    pixel_payload = bytearray()
    pixel_payload += bytearray(24)
    pixel_payload += frames.to_bytes(1, byteorder='big')
    pixel_payload += speed.to_bytes(2, byteorder='big')
    pixel_payload += pixel_bits_all

    return get_transport_payloads_for_content(CONTENT_TYPE_ANIMATE, pixel_payload)
