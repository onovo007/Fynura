"""Generate a code-native Devpost thumbnail, and requested filename aliases."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

root = Path(__file__).resolve().parent
image = Image.new("RGB", (1500, 1000), "#102c24")
d = ImageDraw.Draw(image)
def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)

# Abstract geographic grid, not fabricated epidemiological observations.
for radius in (190, 280, 370, 460):
    d.ellipse((1030-radius, 380-radius, 1030+radius, 380+radius), outline="#235144", width=3)
for y in (190, 300, 410, 520, 630):
    d.line((720,y,1490,y),fill="#235144",width=3)
d.rounded_rectangle((85,90,190,195),radius=26,fill="#f1f7f3")
d.text((115,104),"F",font=font(77,True),fill="#12372a")
d.text((218,98),"FYNURA",font=font(66,True),fill="#ffffff")
d.text((85,330),"See the signal",font=font(106,True),fill="#ffffff")
d.text((85,450),"sooner.",font=font(120,True),fill="#57d3a0")
d.text((90,650),"Global public-health intelligence",font=font(43),fill="#e1eee7")
d.text((90,735),"Explore evidence. Ask questions. Trace sources.",font=font(31),fill="#b8d0c3")
d.line((90,850,1410,850),fill="#366651",width=2)
d.text((90,889),"Powered by Gemini and Google Cloud",font=font(29),fill="#b8d0c3")
image.save(root/"fynura-thumbnail.png")
for old,new in [("fynura_architecture.png","fynura-architecture.png"),
                ("fynura_architecture.svg","fynura-architecture.svg"),
                ("DEVPOST_PROJECT_DETAILS.md","devpost-about.md")]:
    shutil.copyfile(root/old, root/new)
print("Generated 1500x1000 thumbnail and requested filename aliases.")
