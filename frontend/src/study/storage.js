let connection;
export function database(){
 return connection ||= new Promise((resolve,reject)=>{const r=indexedDB.open('student-hub-device-v1',1);r.onupgradeneeded=()=>{for(const name of ['kv','materials'])r.result.createObjectStore(name,{keyPath:'key'});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(new Error('Device storage is unavailable. Enable browser storage or download your work.'));});
}
export async function read(store,key){const db=await database();return new Promise((resolve,reject)=>{const t=db.transaction(store);const r=t.objectStore(store).get(key);r.onsuccess=()=>resolve(r.result?.value);r.onerror=()=>reject(r.error);});}
export async function write(store,key,value){const db=await database();return new Promise((resolve,reject)=>{const t=db.transaction(store,'readwrite');t.objectStore(store).put({key,value});t.oncomplete=()=>resolve(value);t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error||new Error('Storage is full. Download a backup and free space.'));});}
export async function remove(store,key){const db=await database();return new Promise((resolve,reject)=>{const t=db.transaction(store,'readwrite');t.objectStore(store).delete(key);t.oncomplete=()=>resolve();t.onerror=()=>reject(t.error);});}
export async function list(store,prefix){const db=await database();return new Promise((resolve,reject)=>{const r=db.transaction(store).objectStore(store).getAll();r.onsuccess=()=>resolve(r.result.filter(x=>x.key.startsWith(prefix)).map(x=>x.value));r.onerror=()=>reject(r.error);});}
export function download(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);}
export function locked(fn){if(!navigator.locks)throw new Error('This browser needs Web Locks for safe offline editing. Use a recent browser.');return navigator.locks.request('student-hub-device-write',fn);}
