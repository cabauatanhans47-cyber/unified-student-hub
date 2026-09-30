import {Temporal} from '@js-temporal/polyfill';
export function offlinePlan(tasks,events,settings,now=Date.now()){
 const {start,tz,start_hour=17,end_hour=21,daily_minutes=120}=settings;
 if(+end_hour<=+start_hour)throw new Error('End hour must follow start hour.');
 const days=[],slots=[],warnings=[];
 for(let i=0;i<7;i++){
  const d=Temporal.PlainDate.from(start).add({days:i});
  days.push({date:d.toString(),minutes:0,capacity:+daily_minutes,sessions:[]});
  const at=h=>Number(d.toZonedDateTime({timeZone:tz,plainTime:Temporal.PlainTime.from({hour:+h})}).epochMilliseconds);
  const stop=at(end_hour);
  for(let cursor=at(start_hour);cursor+1800000<=stop;cursor+=1800000){if(cursor>=now&&!events.some(e=>cursor<Date.parse(e.end)&&cursor+1800000>Date.parse(e.start)))slots.push({index:i,begin:cursor,end:cursor+1800000});}
 }
 for(const t of tasks.filter(t=>!t.done).sort((a,b)=>Date.parse(a.due)-Date.parse(b.due))){let remaining=t.minutes;const due=Date.parse(t.due);if(due<=now){warnings.push({title:t.title,reason:'Overdue',minutes:remaining});continue;}
  for(const slot of slots){if(remaining<=0)break;const d=days[slot.index];const amount=Math.min(30,remaining,d.capacity-d.minutes,(slot.end-slot.begin)/60000);const finish=slot.begin+amount*60000;if(amount<=0||finish>due)continue;d.sessions.push({task_id:t.id,title:t.title,course:t.course,start:new Date(slot.begin).toISOString(),end:new Date(finish).toISOString(),minutes:amount});d.minutes+=amount;remaining-=amount;slot.begin=finish;}
  if(remaining)warnings.push({title:t.title,reason:'Not enough time before the deadline or within this week',minutes:remaining});
 }
 return {days,warnings,timezone:tz,scheduled_minutes:days.reduce((s,d)=>s+d.minutes,0)};
}
