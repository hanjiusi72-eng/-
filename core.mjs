export const COLS=16, ROWS=8;
export function cellAt(x,y){return Math.floor(Math.max(0,Math.min(.999999,y))*ROWS)*COLS+Math.floor(Math.max(0,Math.min(.999999,x))*COLS);}
export function analyze(data){
 const bins=new Map();let lum=0,filled=0,n=0;
 for(let i=0;i<data.length;i+=4){const r=data[i]/255,g=data[i+1]/255,b=data[i+2]/255;const max=Math.max(r,g,b),min=Math.min(r,g,b),d=max-min;
  let h=0;if(d){if(max===r)h=((g-b)/d+6)%6;else if(max===g)h=(b-r)/d+2;else h=(r-g)/d+4;}h*=60;
  const l=.2126*r+.7152*g+.0722*b,s=max?d/max:0;
  lum+=l;n++; if(s>.18&&l<.92)filled++;
  const bin=Math.floor(h/15)%24,weight=.05+s*s;
  const v=bins.get(bin)||{w:0,r:0,g:0,b:0};v.w+=weight;v.r+=r*weight;v.g+=g*weight;v.b+=b*weight;bins.set(bin,v);
 }
 const [bin,v]=[...bins].sort((a,b)=>b[1].w-a[1].w)[0]||[0,{w:1,r:1,g:1,b:1}];
 const noteIndex=Math.floor(bin*5/24),notes=['C','D','E','G','A'],freq=[261.63,293.66,329.63,392,440];
 return {note:notes[noteIndex],frequency:freq[noteIndex],density:filled/Math.max(n,1),brightness:lum/Math.max(n,1),color:`rgb(${Math.round(v.r/v.w*255)},${Math.round(v.g/v.w*255)},${Math.round(v.b/v.w*255)})`};
}
export class PinchGate{
 constructor(){this.held=false;this.last=-Infinity;}
 update(ratio,now){if(ratio>.48)this.held=false;if(ratio<.28&&!this.held){this.held=true;if(now-this.last>=220){this.last=now;return true;}}return false;}
 reset(){this.held=false;}
}
export function particleProgress(elapsed,duration){const t=Math.max(0,Math.min(1,elapsed/duration));return t<.28?Math.sin(t/.28*Math.PI/2):Math.pow((1-t)/.72,1.5);}
