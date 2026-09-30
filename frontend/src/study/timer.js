export const timerDefaults={study:25,rest:5,cycles:4};
export function newTimer(config=timerDefaults){return {config,phase:'study',cycle:1,status:'ready',remaining:config.study*60000,endAt:null};}
export function advanceTimer(timer,now=Date.now()){
 let t={...timer};if(t.status!=='running')return t;
 while(now>=t.endAt){
  if(t.phase==='study'&&t.cycle>=t.config.cycles)return {...t,status:'complete',remaining:0,endAt:null};
  if(t.phase==='study'){t.phase='rest';t.remaining=t.config.rest*60000;}
  else {t.phase='study';t.cycle++;t.remaining=t.config.study*60000;}
  t.endAt+=t.remaining;
 }
 return {...t,remaining:Math.max(0,t.endAt-now)};
}
