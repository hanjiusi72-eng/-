"""Record actual canvas feedback via MediaRecorder, driven by pointer events."""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    context=b.new_context(viewport={'width':1440,'height':1080})
    page=context.new_page();page.goto('http://127.0.0.1:3000');page.wait_for_function('window.instrument?.snapshot.videoReady')
    page.locator('#sound').click()
    page.evaluate('''()=>{window.__chunks=[];const s=document.querySelector('#canvas').captureStream(30);window.__rec=new MediaRecorder(s,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:6000000});__rec.ondataavailable=e=>__chunks.push(e.data);__rec.start(1000);}''')
    r=page.locator('#canvas').bounding_box()
    def move(c,row):page.mouse.move(r['x']+(c+.5)*r['width']/16,r['y']+(row+.5)*r['height']/8,steps=12)
    page.wait_for_timeout(1200)
    for c,row in [(3,3),(6,4),(9,2),(12,5),(7,3)]:
        move(c,row);page.wait_for_timeout(250);page.mouse.down();page.wait_for_timeout(100);page.mouse.up();page.wait_for_timeout(1100)
    move(2,5);page.mouse.down()
    for c in range(3,12):move(c,5);page.wait_for_timeout(200)
    page.mouse.up();page.wait_for_timeout(3500)
    data=page.evaluate('''async()=>{await new Promise(resolve=>{__rec.onstop=resolve;__rec.stop();});const blob=new Blob(__chunks,{type:'video/webm'});return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(blob);});}''')
    (root/'deliverables/canvas-performance.webm').write_bytes(base64.b64decode(data))
    page.screenshot(path=str(root/'deliverables/interface-still.png'));context.close();b.close()
print('Recorded real canvas and interface interactions')
