import {read,write,locked,download} from './storage';
import {offlinePlan} from './planner';
let current=null;
export const signal=()=>window.dispatchEvent(new Event('hub-offline-change'));
const key=user=>user+':offline';
export async function network(path,options={}){
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);
 try{const response=await fetch('/api'+path,{...options,signal:controller.signal,headers:{'X-Requested-With':'StudentHub',...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...options.headers}});if(!response.ok){const body=await response.json().catch(()=>({detail:'Request failed.'}));const error=new Error(typeof body.detail==='string'?body.detail:body.detail?.map(e=>e.msg).join('; ')||'Request failed.');error.status=response.status;throw error;}return await response.json();}finally{clearTimeout(timeout);}
}
export async function offlineStatus(){return current?await read('kv',key(current)):null;}
export async function enableOffline(){
 if(!current||!navigator.onLine)throw new Error('Sign in online before enabling offline access.');
 if(!('serviceWorker' in navigator)||!navigator.locks)throw new Error('Offline access needs a recent browser with service workers and Web Locks.');
 if((await offlineStatus())?.enabled)return;
 const user=current;
 const [tasks,events,preferences]=await Promise.all([network('/tasks'),network('/events'),network('/preferences')]);
 await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
 await locked(()=>write('kv',key(user),{enabled:true,tasks,events,preferences,queue:[],error:'',lastSync:new Date().toISOString()}));
 await write('kv','active-offline-user',user);signal();
}
export async function syncNow(){
 if(!current||!navigator.onLine||!(await offlineStatus())?.enabled)return;
 const account=current;
 return locked(async()=>{
  let state=await read('kv',key(account));if(!state?.enabled)return;
  try{
   const me=await network('/me');if(me.username!==account)throw new Error('Sign in to '+account+' to sync this device.');
   while(state.queue.length){
    const operation=state.queue[0];const result=await network('/sync',{method:'POST',body:JSON.stringify(operation.request)});
    state.queue.shift();
    if(operation.request.action==='create'){
     const before=operation.localId,after=result.task.id;
     state.tasks=state.tasks.map(t=>t.id===before?{...t,id:after,source:result.task.source,external_id:result.task.external_id}:t);
     for(const later of state.queue){if(later.request.task_id===before)later.request.task_id=after;}
    }
    await write('kv',key(account),state);
   }
   const [tasks,events,preferences]=await Promise.all([network('/tasks'),network('/events'),network('/preferences')]);
   state={...state,tasks,events,preferences,error:'',lastSync:new Date().toISOString()};
  }catch(e){state.error=e.status===401?'Sign in again online to sync. Your pending changes are kept.':e.message;}
  await write('kv',key(account),state);signal();
 });
}
export async function discardPending(){if(!current)return;await locked(async()=>{const s=await offlineStatus();if(s){s.queue=[];s.error='';await write('kv',key(current),s);}});await syncNow();}
export async function exportPending(){const s=await offlineStatus();download(new Blob([JSON.stringify(s,null,2)],{type:'application/json'}),'student-hub-offline-backup.json');}
function validateTask(t){if(!t.title?.trim()||t.title.length>200||!t.course?.trim()||t.course.length>100||!Number.isInteger(t.minutes)||t.minutes<15||t.minutes>2400||!Number.isFinite(Date.parse(t.due)))throw new Error('Check the deadline title, course, date, and effort (15–2400 minutes).');}
export async function api(path,options={}){
 const method=options.method||'GET';
 if(path==='/me'){
  if(navigator.onLine){try{if(await read('kv','pending-logout')){await network('/auth/logout',{method:'POST'});await write('kv','pending-logout',false);}const u=await network(path);current=u.username;return u;}catch(e){if(e.status)throw e;}}
  const user=await read('kv','active-offline-user');if(user&&(await read('kv',key(user)))?.enabled){current=user;return {username:user};}throw new Error('Sign in online first and enable offline access.');
 }
 if(path==='/auth/login'||path==='/auth/register'){
  const u=await network(path,options);current=u.username;await write('kv','pending-logout',false);
  await write('kv','active-offline-user',(await offlineStatus())?.enabled?current:null);return u;
 }
 if(path==='/auth/logout'){
  if(navigator.onLine){await network(path,options);}else await write('kv','pending-logout',true);
  await write('kv','active-offline-user',null);current=null;return {ok:true};
 }
 const state=await offlineStatus();
 if(state?.enabled){
  if(method==='GET'&&['/tasks','/events','/preferences'].includes(path))return path==='/tasks'?[...state.tasks].sort((a,b)=>Date.parse(a.due)-Date.parse(b.due)):state[path.slice(1)];
  if(path.startsWith('/plan?')){const settings=Object.fromEntries(new URLSearchParams(path.split('?')[1]));return offlinePlan(state.tasks,state.events,settings);}
  if(path==='/preferences/plan-seen')return locked(async()=>{const s=await offlineStatus();s.preferences.plan_seen=true;await write('kv',key(current),s);return s.preferences;});
  if((path.startsWith('/tasks')&&method!=='GET')||(path==='/preferences'&&method==='PUT')){
   const result=await locked(async()=>{
    const s=await offlineStatus();const operation={operation_id:crypto.randomUUID(),account:current};let result,localId;
    if(path==='/preferences'){
     const values=JSON.parse(options.body);const {tz,start_hour,end_hour,daily_minutes}=values;
     new Intl.DateTimeFormat('en',{timeZone:tz});if(!Number.isInteger(start_hour)||start_hour<0||start_hour>22||!Number.isInteger(end_hour)||end_hour>23||end_hour<=start_hour||!Number.isInteger(daily_minutes)||daily_minutes<30||daily_minutes>720)throw new Error('Choose valid study hours and a daily budget between 30 and 720 minutes.');
     operation.action='preferences';operation.preferences={tz,start_hour,end_hour,daily_minutes};operation.base_preferences=s.preferences;
     s.preferences={...s.preferences,...operation.preferences,saved:true};result=s.preferences;
    }else{
     const id=path==='/tasks'?null:Number(path.split('/').at(-1));const previous=s.tasks.find(t=>t.id===id);
     if(method==='POST'){
      const data=JSON.parse(options.body);validateTask(data);localId=-(crypto.getRandomValues(new Uint32Array(1))[0]*1000000+Math.floor(Math.random()*1000000));result={...data,id:localId,due:new Date(data.due).toISOString(),source:'manual',external_id:null};
      operation.action='create';operation.task=result;s.tasks.push(result);
     }else{
      if(!previous)throw new Error('This deadline is unavailable on this device.');operation.task_id=id;operation.base=previous;
      if(method==='DELETE'){operation.action='delete';s.tasks=s.tasks.filter(t=>t.id!==id);result={ok:true};}
      else{const data=JSON.parse(options.body);validateTask(data);result={...previous,...data,due:new Date(data.due).toISOString()};operation.action='update';operation.task=result;s.tasks=s.tasks.map(t=>t.id===id?result:t);}
     }
    }
    s.queue.push({request:operation,localId});await write('kv',key(current),s);signal();return result;
   });

   await syncNow();return result;
  }
  if(!navigator.onLine)throw new Error('This action needs internet. Your downloaded materials, deadlines, plan, and timer are available offline.');
  if(state.queue.length)throw new Error('Sync or resolve pending changes before importing or changing calendar commitments.');
  const result=await network(path,options);if(method!=='GET')await syncNow();return result;
 }
 return network(path,options);
}
window.addEventListener('online',()=>syncNow().catch(()=>{}));
