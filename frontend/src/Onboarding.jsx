import React from 'react';
import {Check, Plus, CalendarDays, Clock3} from 'lucide-react';

export default function Onboarding({hasTasks, saved, planSeen, hasSamples, working, onAdd, onSamples, onRemoveSamples, onPlan}) {
  const steps = [
    {done: hasTasks, title: 'Add a deadline', text: 'Start with real coursework or try the samples below.', action: onAdd, icon: Plus},
    {done: saved, title: 'Save your study hours', text: 'Choose when you can study and your daily time budget.', action: onPlan, icon: Clock3},
    {done: saved && planSeen, title: 'Review your weekly plan', text: 'Open Weekly plan to see your blocks and any workload warnings.', action: onPlan, icon: CalendarDays},
  ];
  const completed = steps.filter(step=>step.done).length;
  return <section className="onboarding panel" aria-labelledby="onboarding-title">
    <div className="onboarding-heading"><div><span className="eyebrow">GET STARTED</span><h2 id="onboarding-title">{completed===3?'You’re ready to plan your week.':'Your first plan, in three steps.'}</h2></div><span className="onboarding-progress" aria-label={`${completed} of 3 steps complete`}>{completed}/3 complete</span></div>
    {completed<3&&<ol className="onboarding-steps">{steps.map(({done,title,text,action,icon:Icon},i)=><li key={title}>
      <span className={'step-number '+(done?'step-done':'')}>{done?<Check size={17} aria-label="Complete"/>:i+1}</span>
      <div><button className="step-action" onClick={action} disabled={working}>{title}<Icon size={15} aria-hidden="true"/></button><p>{text}</p></div>
    </li>)}</ol>}
    <div className="sample-actions"><p>{hasSamples?'Sample deadlines are practice items in your private account. Remove them when you’re ready.':'Try three clearly labeled practice deadlines dated for the coming week. Remove them together anytime.'}</p><button className="secondary" disabled={working} onClick={hasSamples?onRemoveSamples:onSamples}>{hasSamples?'Remove sample deadlines':'Try sample deadlines'}</button></div>
  </section>;
}
