from PIL import Image, ImageDraw, ImageFont, ImageColor

def renderTextToImage(txt, color):
    y_offset = -2
    color = ImageColor.getrgb(color)
    img = Image.new('RGBA', (2048, 64))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("assets/fonts/Montserrat-Medium.ttf", 15)
    
    x = 0
    for letter in txt:
        draw.text((x, y_offset), letter, color, font=font)
        x += font.getbbox(letter)[0] + 1

    del draw
    left, upper, right, lower = img.getbbox()
    return img.crop((0, 0, right, lower))

def get_separate_pixel_bytefields(img, width=32, height=16, bgColor="black"):
    if (height % 8 != 0):
        print("ERROR: target-height needs to be divisible by 8")
        return

    imWidth, imHeight = img.size
    defaultPx = ImageColor.getrgb(bgColor)

    barr_R, barr_G, barr_B = bytearray(), bytearray(), bytearray()
    tmp_R, tmp_G, tmp_B = 0, 0, 0

    for x in range(0, width):
        for y in range(0, height):
            if (y < imHeight and x < imWidth):
                px = img.getpixel((x, y))
            else:
                px = defaultPx

            tmp_R = (tmp_R << 1) + int(round(px[0] / 255))
            tmp_G = (tmp_G << 1) + int(round(px[1] / 255))
            tmp_B = (tmp_B << 1) + int(round(px[2] / 255))

            if (y % 8 == 7):
                barr_R.append(tmp_R)
                barr_G.append(tmp_G)
                barr_B.append(tmp_B)
                tmp_R, tmp_G, tmp_B = 0, 0, 0

    return barr_R, barr_G, barr_B

def get_separate_pixel_bytefields_for_animation(anim):
    is_animated = getattr(anim, 'is_animated', False)

    # print ("animation has {} frames".format(anim.n_frames))

    combined_image = None

    animR, animG, animB = bytearray(), bytearray(), bytearray()

    for frame in range(0, anim.n_frames):

        # switch to next frame
        anim.seek(frame)

        # it seems we have to care about applying the transparent pixels ourselves
        if (combined_image is None):
            combined_image = anim.convert('RGBA')
        else:
            combined_image = Image.alpha_composite(combined_image, anim.convert('RGBA'))

        print("Frame {}".format(frame))
        print_pixels(combined_image)

        # anims are always 32x16
        frameR, frameG, frameB = get_separate_pixel_bytefields(combined_image, 96, 16)
        #        for i in range(0, len(frameR), 2):
        #            print ("{0:08b}{1:08b}  {2:08b}{3:08b}  {4:08b}{5:08b}".format(frameR[i],frameR[i+1], frameG[i],frameG[i+1], frameB[i],frameB[i+1]))

        animR += frameR
        animG += frameG
        animB += frameB

    # returns all-pixels of all frames separately for each of the 3 color-components
    return animR, animG, animB

def print_pixels(im):
    imWidth, imHeight = im.size

    print("8-color Pixel Data from Image")

    for y in range(0, imHeight):
        for x in range(0, imWidth):
            px = im.getpixel((x, y))

            rb = int(round(px[0] / 255))
            gb = int(round(px[1] / 255))
            bb = int(round(px[2] / 255))

            bits = rb * 1 + gb * 2 + bb * 4

            print(bits, end=' ')

        print('')