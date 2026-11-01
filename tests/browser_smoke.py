"""Real-browser integration: video, position, audio samples, gestures runtime,
pointer/touch fallback and failure isolation. Uses Chromium fake camera (no hand).
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
results=[]
def passed(name):
    results.append(name)
    print('PASS',name,flush=True)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required'])
    context=browser.new_context(viewport={'width':1440,'height':1100},permissions=['camera'])
    page=context.new_page(); errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script('''const Native=window.AudioContext;window.AudioContext=class extends Native{constructor(...a){super(...a);window.__audio=this;const original=this.createDynamicsCompressor.bind(this);this.createDynamicsCompressor=()=>{const c=original();window.__meter=this.createAnalyser();c.connect(window.__meter);return c;};}};''')
    page.goto('http://127.0.0.1:3000')
    page.wait_for_function('window.instrument?.snapshot.videoReady')
    t=page.evaluate('window.instrument.snapshot.videoTime');page.wait_for_timeout(400)
    assert page.evaluate('window.instrument.snapshot.videoTime')>t
    assert not page.locator('#loading').is_visible();passed('muted source video loops and renders')
    page.locator('#pause').click();page.wait_for_timeout(100);t=page.evaluate('window.instrument.snapshot.videoTime');page.wait_for_timeout(300)
    assert abs(page.evaluate('window.instrument.snapshot.videoTime')-t)<.05;passed('dynamic pause preserves frame')
    page.locator('#sound').click()
    rect=page.locator('#canvas').bounding_box()
    def point(col,row):return (rect['x']+(col+.5)*rect['width']/16,rect['y']+(row+.5)*rect['height']/8)
    page.mouse.click(*point(8,4));page.wait_for_timeout(100)
    s=page.evaluate('window.instrument.snapshot')
    assert s['lastNote']['cell']==72 and s['effects']==1 and s['audioState']=='running'
    energy=page.evaluate('''()=>{const a=new Float32Array(__meter.fftSize);__meter.getFloatTimeDomainData(a);return a.reduce((s,v)=>s+v*v,0)/a.length}''')
    assert energy>1e-8,energy;passed('canvas cell 72 triggers real nonzero Web Audio samples and particles')
    page.screenshot(path=str(ROOT/'deliverables/interaction.png'))
    page.wait_for_timeout(3100);assert page.evaluate('window.instrument.snapshot.effects')==0;passed('particles fully return after three seconds')
    before=page.evaluate('window.instrument.snapshot.notes');page.mouse.move(*point(2,2));page.mouse.down()
    for col in range(3,7):page.wait_for_timeout(100);page.mouse.move(*point(col,2))
    page.mouse.up();assert page.evaluate('window.instrument.snapshot.notes')>=before+5;passed('held mouse drag plays distinct regions')
    page.locator('#grid').click();assert page.locator('#grid').get_attribute('aria-pressed')=='true'
    page.locator('#speed').fill('1.5');assert page.evaluate('document.querySelector("#pattern").playbackRate')==1.5
    page.locator('#volume').fill('35');assert page.evaluate('window.instrument.snapshot.volume')==.35
    passed('grid, playback speed and volume controls update live state')
    page.locator('#cameraStart').click();page.wait_for_function('window.instrument.snapshot.camera')
    assert not page.evaluate('window.instrument.snapshot.tracking');passed('camera preview starts independently of recognition')
    page.locator('#tracking').click();page.wait_for_function('window.instrument.snapshot.tracking',timeout=60000)
    page.wait_for_timeout(3500);assert page.evaluate('window.instrument.snapshot.tracking');passed('local MediaPipe model and WASM run inference on fake camera frames')
    page.locator('#tracking').click();assert page.evaluate('window.instrument.snapshot.camera');passed('stopping recognition preserves camera preview')
    page.locator('#cameraStart').click();assert not page.evaluate('window.instrument.snapshot.camera')
    page.locator('#watchFilm').click();page.wait_for_function('document.querySelector("#creationFilm").currentTime>.1');page.locator('#closeFilm').click();page.wait_for_function('document.querySelector("#creationFilm").paused');passed('scored creation film plays in page and pauses on close')
    assert not errors,errors;passed('no uncaught browser errors')
    # Separate context: intentionally missing inference runtime must not remove preview.
    failure=browser.new_context(permissions=['camera'])
    failure.route('**/vendor/hands/hands.js',lambda route:route.abort())
    q=failure.new_page();q.goto('http://127.0.0.1:3000');q.locator('#cameraStart').click();q.wait_for_function('window.instrument.snapshot.camera');q.locator('#tracking').click();q.wait_for_function('document.querySelector("#cameraStatus").textContent.includes("识别启动失败")')
    assert q.evaluate('window.instrument.snapshot.camera && !window.instrument.snapshot.tracking');passed('recognition load failure reports reason and preserves preview')
    # Mobile layout and actual touchscreen event.
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
    q=mobile.new_page();q.goto('http://127.0.0.1:3000');q.wait_for_function('window.instrument?.snapshot.videoReady');q.locator('#canvas').tap(position={'x':70,'y':60});q.wait_for_timeout(150)
    assert q.evaluate('window.instrument.snapshot.notes')==1
    assert q.evaluate('document.documentElement.scrollWidth<=innerWidth');q.screenshot(path=str(ROOT/'deliverables/mobile.png'),full_page=True);passed('touchscreen plays and 390px layout has no horizontal overflow')
    browser.close()

(ROOT/'deliverables/browser-validation.json').write_text(json.dumps({'passed':results,'limitations':['Real physical hand positioning and pinch must still be checked with a real camera; automated inference used the browser fake camera.','Projection calibration intentionally deferred.']},ensure_ascii=False,indent=2))
