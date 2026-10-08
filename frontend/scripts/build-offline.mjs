import {readdir,readFile,writeFile,cp} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {deflateSync} from 'node:zlib';

function crc(data){let c=0xffffffff;for(const b of data){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
function chunk(type,data){const t=Buffer.from(type),size=Buffer.alloc(4),sum=Buffer.alloc(4);size.writeUInt32BE(data.length);sum.writeUInt32BE(crc(Buffer.concat([t,data])));return Buffer.concat([size,t,data,sum]);}
for(const size of [192,512]){const raw=Buffer.alloc((size*4+1)*size);for(let y=0;y<size;y++)for(let x=0;x<size;x++){const a=x/size,b=y/size;const book=a>.23&&a<.77&&b>.27&&b<.73;const white=book&&(a<.26||a>.74||b<.30||b>.70||Math.abs(a-.5)<.015||((b>.42&&b<.445||b>.53&&b<.555)&&a>.32&&a<.68));const i=y*(size*4+1)+1+x*4;raw.set(white?[255,255,255,255]:[36,84,223,255],i);}const header=Buffer.alloc(13);header.writeUInt32BE(size);header.writeUInt32BE(size,4);header[8]=8;header[9]=6;await writeFile('dist/assets/icon-'+size+'.png',Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]));}
for(const folder of ['cmaps','standard_fonts'])await cp('node_modules/pdfjs-dist/'+folder,'dist/assets/pdf-'+folder,{recursive:true});
async function walk(dir){const result=[];for(const e of await readdir(dir,{withFileTypes:true})){const p=dir+'/'+e.name;result.push(...(e.isDirectory()?await walk(p):[p]));}return result;}
const files=(await walk('dist')).filter(p=>!p.endsWith('/sw.js'));
const hash=createHash('sha256');for(const path of files)hash.update(await readFile(path));
const cache='student-hub-shell-'+hash.digest('hex').slice(0,12);
const urls=['/',...files.filter(p=>!p.endsWith('/index.html')).map(p=>p.slice(4))];
await writeFile('dist/sw.js',`const CACHE=${JSON.stringify(cache)};const FILES=${JSON.stringify(urls)};
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil((async()=>{const names=(await caches.keys()).filter(n=>n.startsWith('student-hub-shell-'));for(const n of names.slice(0,-2))await caches.delete(n);await self.clients.claim();})()));
self.addEventListener('fetch',event=>{const u=new URL(event.request.url);if(u.origin!==self.location.origin||event.request.method!=='GET'||u.pathname.startsWith('/api/'))return;
if(event.request.mode==='navigate'){event.respondWith(fetch(event.request).catch(()=>caches.match('/')));return;}
event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request)));
});`);
