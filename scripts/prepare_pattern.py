"""Keep the clean first-frame geometry; recover the source's changing palette.
The supplied motion study contains baked UI/cursors. No simulated interaction is
carried into the playable surface. Run with the original motion MP4 as argv[1].
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = sys.argv[1]
vf = 'crop=1320:742:90:240,scale=1280:720'
raw = subprocess.check_output(['ffmpeg','-v','error','-i',source,'-vf',vf,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
base = Image.frombytes('RGB',(1280,720),raw)
quant = base.quantize(colors=64, dither=Image.Dither.NONE)
labels = np.array(quant)
small_labels = np.array(quant.resize((640,360),Image.Resampling.NEAREST)).ravel()
rng = np.random.default_rng(72)
indices = [rng.choice(np.flatnonzero(small_labels==i), min(160,int((small_labels==i).sum())),replace=False) for i in range(64)]
palette = np.array(quant.getpalette(),dtype=np.uint8).reshape(-1,3)[:64]
base.save(root/'public/media/pattern-poster.jpg',quality=95)
reader = subprocess.Popen(['ffmpeg','-v','error','-i',source,'-an','-vf','crop=1320:742:90:240,scale=640:360,fps=24','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
writer = subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(root/'public/media/pattern.mp4')],stdin=subprocess.PIPE)
count = 0
while True:
    data = reader.stdout.read(640*360*3)
    if len(data)!=640*360*3: break
    pixels = np.frombuffer(data,np.uint8).reshape(-1,3)
    colors = palette.copy()
    for i, ix in enumerate(indices):
        if len(ix): colors[i] = np.median(pixels[ix],axis=0)
    # Close the palette cycle smoothly without moving any geometry.
    if count>=552:
        mix=(count-552)/23
        colors=np.rint(colors.astype(float)*(1-mix)+palette.astype(float)*mix).astype(np.uint8)
    writer.stdin.write(colors[labels].tobytes())
    count += 1
writer.stdin.close()
assert writer.wait()==0 and reader.wait()==0
print(f'Prepared {count} frames, fixed geometry / original temporal palette')
