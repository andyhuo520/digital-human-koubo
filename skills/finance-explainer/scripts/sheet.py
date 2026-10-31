import subprocess,sys,os
from PIL import Image,ImageDraw,ImageFont
src,out,start,dur,step=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
cols=int(sys.argv[6]) if len(sys.argv)>6 else 6
os.makedirs(out,exist_ok=True)
def load_font(size=16):
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/Consolas.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]

    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    return ImageFont.load_default()


font = load_font(16)
frames=[];t=start
while t<start+dur:
    p=f'{out}/_f.jpg'
    subprocess.run(['ffmpeg','-loglevel','error','-y','-ss',str(t),'-i',src,'-frames:v','1','-vf','scale=384:-1',p])
    if not os.path.exists(p): break
    im=Image.open(p).convert('RGB'); d=ImageDraw.Draw(im)
    lab=f'{int(t//60)}:{t%60:04.1f}'; d.rectangle([0,0,90,20],fill=(0,0,0)); d.text((3,1),lab,fill=(255,230,0),font=font)
    frames.append(im); os.remove(p); t+=step
W,H=frames[0].size; rows=(len(frames)+cols-1)//cols
sheet=Image.new('RGB',(W*cols,H*rows))
for i,f in enumerate(frames): sheet.paste(f,((i%cols)*W,(i//cols)*H))
name=f'{out}/sheet_{int(start):04d}.jpg'; sheet.save(name,quality=82); print(name)
