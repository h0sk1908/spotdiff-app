from PIL import Image, ImageDraw
import os
os.makedirs("images", exist_ok=True)
W, H = 512, 512

def base():
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for x in range(0, W, 64): d.line((x,0,x,H), fill=(230,230,230))
    for y in range(0, H, 64): d.line((0,y,W,y), fill=(230,230,230))
    d.rectangle((60,60,200,160), outline="black", width=3)
    d.ellipse((280,80,360,160), outline="black", width=3)
    d.rectangle((120,300,240,420), outline="black", width=3)
    return img

normal = base(); normal.save("images/normal.png")
lesion  = base(); ImageDraw.Draw(lesion).rectangle((300,140,360,200), outline="red", width=3)
lesion.save("images/lesion.png")
print("OK: images 생성 완료")
