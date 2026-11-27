import sys, pcbnew
from PIL import Image, ImageDraw, ImageFont
b=pcbnew.LoadBoard(sys.argv[1]); out=sys.argv[2]; T=pcbnew.ToMM
K=14; PAD=20; W,H=53,82
im=Image.new("RGB",(int(W*K)+2*PAD,int(H*K)+2*PAD),(20,20,24)); d=ImageDraw.Draw(im)
def P(x,y): return ((T(x)-100)*K+PAD,(T(y)-100)*K+PAD)
d.rounded_rectangle([PAD,PAD,PAD+W*K,PAD+H*K],radius=3*K,outline=(200,200,0),width=2)
# zones (filled) faint
for z in b.Zones():
    col=(60,30,30) if z.GetLayer()==pcbnew.F_Cu else (30,30,70)
cols={pcbnew.F_Cu:(220,60,60),pcbnew.B_Cu:(70,120,255)}
tr=[t for t in b.GetTracks() if t.GetClass()=="PCB_TRACK"]
for lay in (pcbnew.B_Cu,pcbnew.F_Cu):
    for t in tr:
        if t.GetLayer()!=lay: continue
        c=cols[lay] if t.GetNetname() not in ("/VCC","/VBAT","/GND") else ({"/VCC":(255,160,40),"/VBAT":(255,90,200),"/GND":(120,220,120)}[t.GetNetname()] if lay==pcbnew.F_Cu else (40,200,220))
        d.line([P(t.GetStart().x,t.GetStart().y),P(t.GetEnd().x,t.GetEnd().y)],fill=c,width=max(2,int(T(t.GetWidth())*K)))
for f in b.GetFootprints():
    for p in f.Pads():
        bb=p.GetBoundingBox(); x0,y0=P(bb.GetX(),bb.GetY()); x1,y1=P(bb.GetRight(),bb.GetBottom())
        d.rectangle([x0,y0,x1,y1],outline=(230,230,230))
    r=f.GetReference(); q=f.GetPosition(); 
    d.text(P(q.x,q.y),r,fill=(150,150,150),anchor="mm")
for v in b.GetTracks():
    if v.GetClass()=="PCB_VIA":
        x,y=P(v.GetPosition().x,v.GetPosition().y); r=0.3*K
        d.ellipse([x-r,y-r,x+r,y+r],fill=(240,240,240),outline=(0,0,0))
im.save(out)
