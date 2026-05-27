"""Monta um mosaico rotulado a partir de uma lista de pngs."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
# args: out.png  cols  "path:label" "path:label" ...
out=sys.argv[1]; cols=int(sys.argv[2]); items=sys.argv[3:]
imgs=[]
for it in items:
    p,lab=it.rsplit("|",1)
    im=Image.open(p).convert("RGB")
    imgs.append((im,lab))
if not imgs: sys.exit("no imgs")
cw=max(i.width for i,_ in imgs); ch=max(i.height for i,_ in imgs)
lab_h=28
rows=(len(imgs)+cols-1)//cols
W=cols*cw; H=rows*(ch+lab_h)
canvas=Image.new("RGB",(W,H),(20,20,24))
d=ImageDraw.Draw(canvas)
try: font=ImageFont.truetype("arial.ttf",20)
except: font=ImageFont.load_default()
for k,(im,lab) in enumerate(imgs):
    r=k//cols; c=k%cols
    x=c*cw; y=r*(ch+lab_h)
    canvas.paste(im,(x,y))
    d.text((x+6,y+ch+3),lab,fill=(240,240,240),font=font)
canvas.save(out)
print("saved",out,canvas.size)
