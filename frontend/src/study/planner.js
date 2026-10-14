import {Temporal} from '@js-temporal/polyfill';
export function offlinePlan(tasks,events,settings,now=Date.now()){
 const {start,tz,start_hour=17,end_hour=21,daily_minutes=120}=settings;
 if(+end_hour<=+start_hour)throw new Error('End hour must follow start hour.');
 const days=[],slots=[],warnings=[];
 for(let i=0;i<7;i++){
  const d=Temporal.PlainDate.from(start).add({days:i});
  const advanced=settings.studentSettings;
  const config=advanced?.custom_days?advanced.days[d.dayOfWeek-1]:{enabled:true,start_hour:+start_hour,end_hour:+end_hour,daily_minutes:+daily_minutes};
  days.push({date:d.toString(),minutes:0,capacity:config.enabled?config.daily_minutes:0,sessions:[]});
  if(!config.enabled)continue;
  const at=h=>Number(d.toZonedDateTime({timeZone:tz,plainTime:Temporal.PlainTime.from({hour:+h})}).epochMilliseconds);
  const stop=at(config.end_hour);
  const busy=[...events];
  for(const c of advanced?.classes||[]){if(c.weekday!==d.dayOfWeek-1||d.toString()<c.first_date||d.toString()>c.last_date)continue;const when=t=>d.toZonedDateTime({timeZone:tz,plainTime:Temporal.PlainTime.from(t)}).toInstant().toString();busy.push({start:when(c.start_time),end:when(c.end_time)});}
  for(let cursor=at(config.start_hour);cursor+1800000<=stop;cursor+=1800000){if(cursor>=now&&!busy.some(e=>cursor<Date.parse(e.end)&&cursor+1800000>Date.parse(e.start)))slots.push({index:i,begin:cursor,end:cursor+1800000});}
 }
 for(const t of tasks.filter(t=>!t.done).sort((a,b)=>Date.parse(a.due)-Date.parse(b.due))){let remaining=t.minutes;const due=Date.parse(t.due);if(due<=now){warnings.push({title:t.title,reason:'Overdue',minutes:remaining});continue;}
  for(const slot of slots){if(remaining<=0)break;const d=days[slot.index];const amount=Math.min(30,remaining,d.capacity-d.minutes,(slot.end-slot.begin)/60000);const finish=slot.begin+amount*60000;if(amount<=0||finish>due)continue;d.sessions.push({task_id:t.id,title:t.title,course:t.course,start:new Date(slot.begin).toISOString(),end:new Date(finish).toISOString(),minutes:amount});d.minutes+=amount;remaining-=amount;slot.begin=finish;}
  if(remaining)warnings.push({title:t.title,reason:'Not enough time before the deadline or within this week',minutes:remaining});
 }
 return {days,warnings,timezone:tz,scheduled_minutes:days.reduce((s,d)=>s+d.minutes,0)};
}
