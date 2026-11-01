import {COLS,ROWS,cellAt,analyze,PinchGate,particleProgress} from './core.mjs';
const $=id=>document.getElementById(id),canvas=$('canvas'),ctx=canvas.getContext('2d'),video=$('pattern');
const frame=document.createElement('canvas');frame.width=1280;frame.height=720;const fc=frame.getContext('2d',{willReadFrequently:true});
const W=1280,H=720,CW=W/COLS,CH=H/ROWS;
const state={grid:false,paused:false,sound:false,volume:.6,speed:1,spread:70,restore:3,cursor:null,effects:new Map(),notes:0,lastNote:null,camera:false,tracking:false,voices:0};
let audio,master,compressor,firstPlay=true,hasFrame=false,lastPointerCell=-1,dragging=false,activePointer=null,lastDragTime=0,selected=0;
function audioGraph(){if(audio)return;audio=new AudioContext();master=audio.createGain();compressor=audio.createDynamicsCompressor();compressor.threshold.value=-15;compressor.ratio.value=5;master.gain.value=state.volume*.24;master.connect(compressor);compressor.connect(audio.destination);}
async function setSound(on){try{audioGraph();await audio.resume();state.sound=on;firstPlay=false;$('sound').setAttribute('aria-pressed',on);$('sound').innerHTML=on?'<span>♫</span> 声音已开启 <span>✓</span>':'<span>♫</span> 开启声音 <span>↗</span>';master.gain.setTargetAtTime(on?state.volume*.24:0,audio.currentTime,.04);}catch(e){$('cellInfo').textContent='声音启动失败：'+e.message;}}
function playTone(info){if(!state.sound||!audio||audio.state!=='running')return;const now=audio.currentTime,duration=.8+info.density*3.5;
 const gain=audio.createGain(),filter=audio.createBiquadFilter();filter.type='lowpass';filter.frequency.value=650+info.brightness*4200;filter.Q.value=.5;
 gain.gain.setValueAtTime(0,now);gain.gain.linearRampToValueAtTime(.65,now+.016);gain.gain.exponentialRampToValueAtTime(.001,now+duration);gain.connect(filter);filter.connect(master);
 const oscs=[1,2,3].map((multiple,i)=>{const o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.value=info.frequency*multiple;g.gain.value=[.7,.18*info.brightness,.06][i];o.connect(g);g.connect(gain);o.start(now);o.stop(now+duration+.1);return o;});
 state.voices++;oscs[0].onended=()=>{gain.disconnect();filter.disconnect();state.voices--;};
}
function trigger(cell,origin='pointer'){
 if(!hasFrame)return null;const x=(cell%COLS)*CW,y=Math.floor(cell/COLS)*CH,pixels=fc.getImageData(x,y,CW,CH),info=analyze(pixels.data);
 playTone(info);state.notes++;state.lastNote={...info,cell,origin,time:performance.now()};selected=cell;
 $('note').textContent=info.note;$('swatch').style.background=info.color;$('cellInfo').textContent=`第 ${cell%COLS+1} 列 · 第 ${Math.floor(cell/COLS)+1} 行 / ${Math.round(info.density*100)}% 填色`;
 const frozen=document.createElement('canvas');frozen.width=CW;frozen.height=CH;frozen.getContext('2d').putImageData(pixels,0,0);
 const particles=[];const step=5;
 for(let py=0;py<CH;py+=step)for(let px=0;px<CW;px+=step){const angle=Math.atan2(py-CH/2,px-CW/2)+(Math.random()-.5)*1.1;const distance=state.spread*(.35+Math.random());particles.push({px,py,dx:Math.cos(angle)*distance,dy:Math.sin(angle)*distance,rot:(Math.random()-.5)*2});}
 if(state.effects.size>=20)state.effects.delete(state.effects.keys().next().value);
 state.effects.set(cell,{cell,x,y,start:performance.now(),duration:state.restore*1000,particles,frozen,step});
 return info;
}
function draw(now){
 if(video.readyState>=2){fc.drawImage(video,0,0,W,H);hasFrame=true;$('loading').hidden=true;ctx.drawImage(frame,0,0);}
 else if(!hasFrame){const poster=$('poster');if(poster?.complete&&poster.naturalWidth)ctx.drawImage(poster,0,0,W,H);}
 for(const [id,e] of state.effects){const t=(now-e.start)/e.duration;if(t>=1){state.effects.delete(id);continue;}const spread=particleProgress(now-e.start,e.duration),join=Math.max(0,(t-.55)/.45);
  // Only the active cell is lifted from the live frame; all other cells keep playing.
  ctx.fillStyle='#c2d8bc';ctx.globalAlpha=1-join;ctx.fillRect(e.x,e.y,CW,CH);ctx.globalAlpha=1;
  for(const p of e.particles){const dx=e.x+p.px+p.dx*spread,dy=e.y+p.py+p.dy*spread;
   ctx.globalAlpha=1-join;ctx.drawImage(e.frozen,p.px,p.py,e.step,e.step,dx,dy,e.step,e.step);
   if(join){ctx.globalAlpha=join*(1-join);ctx.drawImage(frame,e.x+p.px,e.y+p.py,e.step,e.step,dx,dy,e.step,e.step);}
  }ctx.globalAlpha=1;
 }
 if(state.grid){ctx.strokeStyle='rgba(38,70,49,.28)';ctx.lineWidth=1;ctx.beginPath();for(let i=1;i<COLS;i++){ctx.moveTo(i*CW,0);ctx.lineTo(i*CW,H);}for(let i=1;i<ROWS;i++){ctx.moveTo(0,i*CH);ctx.lineTo(W,i*CH);}ctx.stroke();}
 if(state.cursor){const {x,y,pressed}=state.cursor,cx=x*W,cy=y*H,cell=cellAt(x,y);ctx.strokeStyle=pressed?'#fff9d0':'#355b46';ctx.lineWidth=1.5;ctx.strokeRect(cell%COLS*CW+2,Math.floor(cell/COLS)*CH+2,CW-4,CH-4);ctx.beginPath();ctx.arc(cx,cy,pressed?10:17,0,Math.PI*2);ctx.stroke();ctx.fillStyle=pressed?'#fff9d0':'#355b46';ctx.beginPath();ctx.arc(cx,cy,3,0,Math.PI*2);ctx.fill();}
 requestAnimationFrame(draw);
}
const poster=new Image();poster.id='poster';poster.src='./media/pattern-poster.jpg';poster.hidden=true;document.body.append(poster);
video.muted=true;video.play().catch(()=>{$('loading').textContent='轻触纹样，展开动态画面';});
video.addEventListener('error',()=>{$('loading').hidden=false;$('loading').textContent='纹样视频加载失败，请刷新或检查媒体文件。';});
requestAnimationFrame(draw);
function pointerPos(e){const r=canvas.getBoundingClientRect();return{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height)),pressed:dragging};}
canvas.addEventListener('pointerdown',async e=>{if(activePointer!==null)return;e.preventDefault();activePointer=e.pointerId;canvas.setPointerCapture(e.pointerId);dragging=true;state.cursor=pointerPos(e);lastPointerCell=cellAt(state.cursor.x,state.cursor.y);lastDragTime=performance.now();if(firstPlay)await setSound(true);if(video.paused&&!state.paused)video.play().catch(()=>{});trigger(lastPointerCell);});
canvas.addEventListener('pointermove',e=>{if(activePointer!==null&&e.pointerId!==activePointer)return;state.cursor=pointerPos(e);const cell=cellAt(state.cursor.x,state.cursor.y);if(dragging&&cell!==lastPointerCell&&performance.now()-lastDragTime>75){lastPointerCell=cell;lastDragTime=performance.now();trigger(cell,'drag');}});
function release(e){if(e.pointerId!==activePointer)return;dragging=false;activePointer=null;lastPointerCell=-1;if(state.cursor)state.cursor.pressed=false;}
canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('lostpointercapture',release);canvas.addEventListener('pointerleave',()=>{if(!dragging&&!state.tracking)state.cursor=null;});
canvas.addEventListener('keydown',async e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' ','Enter'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')selected=Math.max(0,selected-1);if(e.key==='ArrowRight')selected=Math.min(127,selected+1);if(e.key==='ArrowUp')selected=Math.max(0,selected-16);if(e.key==='ArrowDown')selected=Math.min(127,selected+16);state.cursor={x:(selected%16+.5)/16,y:(Math.floor(selected/16)+.5)/8,pressed:false};if((e.key===' '||e.key==='Enter')&&!e.repeat){if(firstPlay)await setSound(true);trigger(selected,'keyboard');}});
$('sound').onclick=()=>setSound(!state.sound);
$('volume').oninput=e=>{state.volume=Number(e.target.value)/100;$('volumeOut').textContent=e.target.value+'%';if(master)master.gain.setTargetAtTime(state.sound?state.volume*.24:0,audio.currentTime,.04);};
$('pause').onclick=()=>{state.paused=!state.paused;$('pause').setAttribute('aria-pressed',state.paused);$('pause').textContent=state.paused?'▶ 继续':'Ⅱ 暂停';if(state.paused)video.pause();else video.play().catch(()=>{});};
for(const key of ['speed','spread','restore'])$(key).oninput=e=>{state[key]=Number(e.target.value);$(key+'Out').textContent=key==='speed'?state[key].toFixed(2).replace(/0$/,'')+'×':key==='restore'?state[key].toFixed(1)+' s':state[key]<50?'轻柔':state[key]>100?'舒展':'适中';if(key==='speed')video.playbackRate=state.speed;};
$('grid').onclick=()=>{state.grid=!state.grid;$('grid').setAttribute('aria-pressed',state.grid);$('grid').textContent=state.grid?'▦ 隐藏分区':'▦ 显示分区';};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(e){$('cellInfo').textContent='当前浏览器不支持全屏：'+e.message;}};
$('about').onclick=()=>$('aboutDialog').showModal();$('closeAbout').onclick=()=>$('aboutDialog').close();
let stream,hands,trackingLoop=0,lastVideoTime=-1,startingCamera=false,startingTracking=false,lastHand=0;
const pinch=new PinchGate();
function cameraStatus(text){$('cameraStatus').textContent=text;}
function stopTracking(reason='识别已停止，取景保留。'){state.tracking=false;cancelAnimationFrame(trackingLoop);$('tracking').textContent='启动识别';$('modeLabel').textContent='鼠标 / 触屏演奏';state.cursor=null;pinch.reset();cameraStatus(reason);}
async function toggleCamera(){if(startingCamera)return;if(state.camera){stopTracking('摄像头已关闭，可继续用鼠标或触屏弹奏。');stream?.getTracks().forEach(t=>t.stop());$('camera').srcObject=null;state.camera=false;$('cameraPlaceholder').hidden=false;$('cameraBadge').textContent='CAMERA OFF';$('cameraStart').textContent='开启摄像头';$('tracking').disabled=true;return;}
 startingCamera=true;$('cameraStart').disabled=true;
 try{if(!navigator.mediaDevices?.getUserMedia)throw Error('浏览器需要 HTTPS 或 localhost 安全环境才能访问摄像头');stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'},audio:false});$('camera').srcObject=stream;await $('camera').play();state.camera=true;$('cameraPlaceholder').hidden=true;$('cameraBadge').textContent='LOCAL · MIRRORED';$('cameraStart').textContent='关闭摄像头';$('tracking').disabled=false;cameraStatus('取景已开启。点击「启动识别」，伸出食指并捏合。');stream.getVideoTracks()[0].onended=()=>{if(state.camera)toggleCamera();};}
 catch(e){const reasons={NotAllowedError:'摄像头权限被拒绝，请在浏览器设置中允许访问。',NotFoundError:'没有找到摄像头，请连接设备或使用鼠标与触屏。',NotReadableError:'摄像头被占用，请关闭其他取景程序。'};cameraStatus(reasons[e.name]||e.message);stream?.getTracks().forEach(t=>t.stop());}
 finally{startingCamera=false;$('cameraStart').disabled=false;}
}
$('cameraStart').onclick=toggleCamera;
function handleLandmarks(results){if(!state.tracking)return;const lm=results.multiHandLandmarks?.[0];if(!lm){if(performance.now()-lastHand>700){state.cursor=null;cameraStatus('未发现手部。将手放入取景范围，保持光线充足。');}return;}lastHand=performance.now();const tip=lm[8],thumb=lm[4],w=$('camera').videoWidth,h=$('camera').videoHeight;
 const distance=(a,b)=>Math.hypot((a.x-b.x)*w,(a.y-b.y)*h),scale=Math.max(15,distance(lm[0],lm[9]));const ratio=distance(tip,thumb)/scale;
 const target={x:1-tip.x,y:tip.y};const old=state.cursor;state.cursor={x:old?old.x*.35+target.x*.65:target.x,y:old?old.y*.35+target.y*.65:target.y,pressed:ratio<.28};
 if(pinch.update(ratio,performance.now()))trigger(cellAt(state.cursor.x,state.cursor.y),'pinch');cameraStatus(pinch.held?'已触发 · 松开拇指与食指后，可再次弹奏。':'识别中 · 食指移动定位，拇指与食指捏合弹奏。');
}
async function trackingTick(){if(!state.tracking)return;try{const cam=$('camera');if(cam.readyState>=2&&cam.currentTime!==lastVideoTime){lastVideoTime=cam.currentTime;await hands.send({image:cam});}}catch(e){stopTracking('手势识别失败：'+e.message+'。取景保留，可重试或用鼠标弹奏。');return;}trackingLoop=requestAnimationFrame(trackingTick);}
$('tracking').onclick=async()=>{if(startingTracking)return;if(state.tracking){stopTracking();return;}if(!state.camera)return;startingTracking=true;$('tracking').disabled=true;cameraStatus('正在加载本地手部模型…');
 try{if(typeof window.Hands!=='function')throw Error('本地识别运行库缺失');if(!hands){hands=new window.Hands({locateFile:file=>new URL('./vendor/hands/'+file,document.baseURI).href});hands.setOptions({maxNumHands:1,modelComplexity:1,minDetectionConfidence:.6,minTrackingConfidence:.6,selfieMode:false});hands.onResults(handleLandmarks);await hands.initialize();}if(!state.camera){cameraStatus('摄像头已关闭；重新开启后可启动识别。');return;}state.tracking=true;lastHand=performance.now();$('tracking').textContent='停止识别';$('modeLabel').textContent='食指定位 / 捏合弹奏';cameraStatus('模型就绪。请把手放入取景范围。');trackingTick();}
 catch(e){if(hands){try{hands.close();}catch{}}hands=null;stopTracking('识别启动失败：'+e.message+'。摄像头取景保留，仍可鼠标弹奏。');}
 finally{startingTracking=false;$('tracking').disabled=!state.camera;}
};
window.addEventListener('pagehide',()=>{state.tracking=false;stream?.getTracks().forEach(t=>t.stop());hands?.close();audio?.close();});
// Read-only observability used by readiness checks; actual inputs still drive the work.
window.instrument={get snapshot(){return{...state,effects:state.effects.size,cursor:state.cursor?{...state.cursor}:null,videoTime:video.currentTime,videoReady:hasFrame,audioState:audio?.state||'uninitialized'};}};

$('watchFilm').onclick=()=>{$('filmDialog').showModal();$('creationFilm').play().catch(()=>{});};$('closeFilm').onclick=()=>$('filmDialog').close();$('filmDialog').addEventListener('close',()=>$('creationFilm').pause());
