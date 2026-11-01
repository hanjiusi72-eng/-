"""A 56-second scored film from supplied artwork + actual browser performance.
No third-party music. Creates original pentatonic felt-key/pad synthesis.
"""
from pathlib import Path
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';WORK=OUT/'film-build';WORK.mkdir(exist_ok=True)
W,H=1920,1080
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
if not Path(SERIF).exists():SERIF=FONT
def font(size,serif=False):return ImageFont.truetype(SERIF if serif else FONT,size)
def text(draw,xy,value,size=32,fill='#f4f0df',serif=False):draw.text(xy,value,font=font(size,serif),fill=fill)
def overlay(name,chapter,title,subtitle,dark=True,footer='纹样之声 / A PATTERN THAT LISTENS'):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        alpha=int(165*max(0,(230-y)/230)+200*max(0,(y-760)/320))
        d.line((0,y,W,y),fill=(12,26,23,alpha))
    text(d,(100,66),chapter,17,'#d4dcb6')
    text(d,(100,825),title,48,serif=True)
    text(d,(102,909),subtitle,23,'#d2d9c7')
    d.line((100,1006,1820,1006),fill='#7b8a73',width=1)
    text(d,(100,1020),footer,12,'#bec8af');text(d,(1685,1020),'STUDY / 2026',12,'#bec8af')
    p=WORK/(name+'.png');im.save(p);return p

overlays=[
 overlay('title','PROLOGUE / 序','纹 样 之 声','让色彩有回声，让指尖成为旋律。'),
 overlay('geometry','01 / 创作 · 从一条线开始','骨式生长，色彩醒来。','从提供的艺术短片出发，寻找纹样中反复出现的秩序。'),
 overlay('palette','02 / 创作 · 将色彩写成音符','C · D · E · G · A','固定结构，流动配色。填色密度决定延音，明暗改变音色。'),
 overlay('interface','03 / 交互 · 走进纹样','一块画布，128 个共鸣的单元。','屏幕原型界面 · 可用鼠标、触屏或手势参与'),
 overlay('performance','04 / 交互 · 原型操作实录','触发，散开，然后重新相遇。','实际网页鼠标演奏录屏 · 局部粒子实时生成，其他区域继续流动'),
 overlay('gesture','05 / 手势流程示意 · 非实拍','食指定位。轻轻捏合。松开，再继续。','摄像头取景与识别分别启动 · 仅在本地处理 · 捏合不等于桌面触碰'),
 overlay('end','EPILOGUE / 回响','纹样不止被观看，也可以被听见。','每一次相遇，都让秩序生长出新的声音。',footer='纹样之声 / 原创五声音阶配乐 · 屏幕端交互研究'),
]

# Minimal line illustration, explicitly a workflow diagram rather than live tracking.
im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
d.rounded_rectangle((1180,220,1780,720),radius=28,fill=(242,244,230,234),outline='#a8b88c',width=2)
text(d,(1230,250),'GESTURE / 捏合流程',19,'#526c4a')
# Anatomical abstract outline: palm, extended index, approaching thumb.
points=[(1350,650),(1305,565),(1290,520),(1305,505),(1338,530),(1344,390),(1350,347),(1367,338),(1385,350),(1389,445),(1410,464),(1440,468),(1466,486),(1480,515),(1492,540),(1488,592),(1468,650)]
d.line(points,fill='#526c4a',width=5,joint='curve')
d.ellipse((1338,323,1394,379),outline='#a0ae5b',width=3)
d.ellipse((1283,489,1327,533),outline='#a0ae5b',width=3)
d.line((1330,500,1362,385),fill='#b7a458',width=2)
text(d,(1530,362),'01 定位',23,'#526c4a');text(d,(1530,430),'02 捏合',23,'#526c4a');text(d,(1530,498),'03 松开',23,'#526c4a')
text(d,(1230,678),'示意图 / 不代表真实桌面接触',15,'#84916d')
diagram=WORK/'hand-diagram.png';im.save(diagram)

def run(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:raise RuntimeError(p.stderr.decode()[-5000:])

# Encode each chapter separately so rendering stays bounded in CPU/memory.
durations=[6,8,8,8,12,8,6]
sources=[ROOT/'public/media/origin.mp4',ROOT/'public/media/origin.mp4',ROOT/'public/media/pattern.mp4',OUT/'interface-still.png',OUT/'canvas-performance.webm',ROOT/'public/media/pattern.mp4',ROOT/'public/media/pattern.mp4']
starts=[0,6,0,0,1,12,18]
for i,(duration,source,start,ov) in enumerate(zip(durations,sources,starts,overlays)):
    cmd=['ffmpeg','-v','error','-y','-threads','2']
    if source.suffix=='.png':cmd+=['-loop','1','-i',str(source)]
    else:cmd+=['-stream_loop','-1','-ss',str(start),'-i',str(source)]
    cmd+=['-loop','1','-i',str(ov)]
    if i==5:cmd+=['-loop','1','-i',str(diagram)]
    # No extra deformation of the pattern; only framing and cinematic fades.
    base='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x12211c,setsar=1,fps=24'
    if i in (0,1):base='crop=1920:800:0:110,scale=1680:700,pad=1920:1080:120:80:color=0x101715,setsar=1,fps=24'
    if i==3:base='scale=1440:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x12211c,setsar=1,fps=24'
    chain=f'[0:v]{base}[base];[base][1:v]overlay=0:0:shortest=1[ov];'
    chain+=('[ov][2:v]overlay=0:0:shortest=1[art];[art]' if i==5 else '[ov]')
    chain+=f'fade=t=in:d=0.6,fade=t=out:st={duration-.65}:d=0.65,format=yuv420p[v]'
    target=WORK/f'chapter-{i}.mp4'
    cmd+=['-filter_complex_threads','2','-filter_complex',chain,'-map','[v]','-t',str(duration),'-an','-c:v','libx264','-preset','fast','-crf','20','-threads','2',str(target)]
    run(cmd);print(f'Chapter {i+1}/7 rendered',flush=True)

# Original 56s ambient score: warm fifths, gentle felt-key pentatonic melody,
# three soft stereo echoes and a long release; peak-normalized without clipping.
sr=48000;duration=sum(durations);n=sr*duration
music=np.zeros((n,2),np.float64)
def note(start,freq,length,amp,pan=0,pad=False):
    count=min(int(length*sr),n-int(start*sr));t=np.arange(count)/sr
    if pad:
        env=np.minimum(t/2,1)*np.minimum((length-t)/3,1)
        signal=(np.sin(2*np.pi*freq*t)+.25*np.sin(2*np.pi*freq*2.003*t))*.5*env
    else:
        env=(1-np.exp(-t/0.018))*np.exp(-t/1.8)*np.minimum((length-t)/.35,1)
        signal=(np.sin(2*np.pi*freq*t)+.27*np.sin(2*np.pi*freq*2*t)*np.exp(-t/1.1)+.1*np.sin(2*np.pi*freq*3*t)*np.exp(-t/.6))*env
    for delay,decay,side in [(0,1,pan),(.23,.17,-pan),(.47,.12,pan+.2),(.81,.07,-pan-.2)]:
        begin=int((start+delay)*sr);size=min(count,n-begin)
        if size<=0:continue
        side=max(-.8,min(.8,side));music[begin:begin+size,0]+=signal[:size]*amp*decay*math.sqrt((1-side)/2);music[begin:begin+size,1]+=signal[:size]*amp*decay*math.sqrt((1+side)/2)
for s,root in [(0,130.813),(12,110),(24,130.813),(36,146.832),(48,130.813)]:
    for mult,amp in [(1,.09),(1.5,.055),(2,.025)]:note(s,root*mult,15,amp,pad=True)
melody=[0,2,4,7,9,7,4,2,0,4,7,12,9,7,4,2,4,7,9,14,12,9,7,4,2,0]
freqs={k:261.626*2**(k/12) for k in set(melody)}
for i,key in enumerate(melody):note(1.5+i*1.95,freqs[key],5,.105 if i%3 else .14,pan=math.sin(i*1.3)*.45)
# A few high bell-like answers in the live-performance section.
for i,key in enumerate([12,16,19,21,19]):note(31+i*2.3,261.626*2**(key/12),4,.045,pan=(-1)**i*.5)
fade=np.minimum(np.arange(n)/sr/2,1)*np.minimum((n-1-np.arange(n))/sr/4,1)
music*=fade[:,None];music=music/max(1,np.max(np.abs(music))/.78)
pcm=(music*32767).astype('<i2')
with wave.open(str(OUT/'纹样之声_原创配乐.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes(pcm.tobytes())
listing=WORK/'chapters.txt';listing.write_text(''.join(f"file '{WORK}/chapter-{i}.mp4'\n" for i in range(7)))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'纹样之声_原创配乐.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-shortest','-movflags','+faststart',str(OUT/'纹样之声_创作与交互短片.mp4')])
print('Completed 56s 1080p film with original stereo score',flush=True)
