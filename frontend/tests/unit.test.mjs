import test from 'node:test';
import assert from 'node:assert/strict';
import {newTimer,advanceTimer} from '../src/study/timer.js';
import {offlinePlan} from '../src/study/planner.js';
test('timer moves through rests and cycles and stops after final study',()=>{
 const t={...newTimer({study:1,rest:1,cycles:2}),status:'running',endAt:60000};
 assert.equal(advanceTimer(t,59999).remaining,1);
 assert.equal(advanceTimer(t,60000).phase,'rest');
 assert.equal(advanceTimer(t,120000).cycle,2);
 assert.equal(advanceTimer(t,180000).status,'complete');
 assert.equal(advanceTimer(t,999999).remaining,0);
});
test('paused timer does not consume time; resumed timer uses remaining duration',()=>{
 const t={...newTimer(),status:'paused',remaining:12500};
 assert.deepEqual(advanceTimer(t,9999999),t);
 assert.equal(advanceTimer({...t,status:'running',endAt:112500},105000).remaining,7500);
});
test('offline plan respects busy time, deadlines, budgets and completion',()=>{
 const tasks=[{id:1,title:'Soon',course:'CPE',due:'2030-01-01T19:00:00Z',minutes:45,done:false},{id:2,title:'Later',course:'CPE',due:'2030-01-03T00:00:00Z',minutes:60,done:false},{id:3,title:'Done',due:'2030-01-02T00:00:00Z',minutes:100,done:true}];
 const p=offlinePlan(tasks,[{start:'2030-01-01T17:00:00Z',end:'2030-01-01T17:30:00Z'}],{start:'2030-01-01',tz:'UTC',start_hour:17,end_hour:19,daily_minutes:60},Date.parse('2030-01-01T00:00:00Z'));
 assert.equal(p.scheduled_minutes,105);assert.equal(p.days[0].minutes,60);assert.equal(p.days[0].sessions[0].start,'2030-01-01T17:30:00.000Z');assert.equal(p.days[0].sessions[1].minutes,15);assert.equal(p.warnings.length,0);
});
test('offline plan handles DST in UTC and reports overdue and insufficient time',()=>{
 const p=offlinePlan([{id:1,title:'Reading',due:'2030-03-10T09:00:00Z',minutes:180,done:false},{id:2,title:'Old',due:'2029-01-01T00:00:00Z',minutes:30,done:false}],[],{start:'2030-03-10',tz:'America/New_York',start_hour:1,end_hour:4,daily_minutes:180},Date.parse('2030-03-10T00:00:00Z'));
 assert.equal(p.days[0].minutes,120);assert.equal(p.warnings.length,2);assert.equal(p.warnings[1].minutes,60);
});
