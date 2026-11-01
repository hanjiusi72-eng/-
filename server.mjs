import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve('public');
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.mp4':'video/mp4','.jpg':'image/jpeg','.wasm':'application/wasm','.json':'application/json'};
http.createServer(async(req,res)=>{
 try {
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname==='/'?'/index.html':new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)) {res.writeHead(403).end();return;}
  const info=await stat(file); if(!info.isFile()) throw Error();
  const data=await readFile(file); const headers={'Content-Type':mime[path.extname(file)]||'application/octet-stream','Accept-Ranges':'bytes','Cache-Control':'no-cache'};
  const range=req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
  if(range){const start=Number(range[1]),end=Math.min(range[2]?Number(range[2]):info.size-1,info.size-1);if(start> end){res.writeHead(416,{'Content-Range':`bytes */${info.size}`}).end();return;}res.writeHead(206,{...headers,'Content-Range':`bytes ${start}-${end}/${info.size}`,'Content-Length':end-start+1});res.end(data.subarray(start,end+1));}
  else {res.writeHead(200,{...headers,'Content-Length':info.size});res.end(data);}
 }catch {res.writeHead(404).end('Not found');}
}).listen(Number(process.env.PORT)||3000,'0.0.0.0',()=>console.log('Pattern instrument running on port '+(process.env.PORT||3000)));
