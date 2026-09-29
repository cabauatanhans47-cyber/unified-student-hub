"""Deterministic earliest-deadline-first planning in a student's local timezone."""
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo

def stamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None: raise ValueError('An explicit timezone is required')
    return dt

def plan_week(tasks, events, start, tz, start_hour=17, end_hour=21, daily_minutes=120, now=None):
    zone = ZoneInfo(tz)
    now = now or datetime.now(timezone.utc)
    days, slots, warnings = [], [], []
    busy = [(stamp(e['start']), stamp(e['end'])) for e in events]
    for offset in range(7):
        day = start + timedelta(days=offset)
        days.append({'date': day.isoformat(), 'minutes': 0, 'capacity': daily_minutes, 'sessions': []})
        # Iterate in UTC so DST transitions never duplicate or invent time.
        cursor = datetime.combine(day, time(start_hour), zone).astimezone(timezone.utc)
        stop = datetime.combine(day, time(end_hour), zone).astimezone(timezone.utc)
        while cursor + timedelta(minutes=30) <= stop:
            end = cursor + timedelta(minutes=30)
            if cursor >= now and not any(cursor < b and end > a for a,b in busy):
                slots.append((offset, cursor, end))
            cursor = end
    for task in sorted((t for t in tasks if not t['done']), key=lambda t: stamp(t['due'])):
        due, remaining = stamp(task['due']), task['minutes']
        if due <= now:
            warnings.append({'title': task['title'], 'reason': 'Overdue', 'minutes': remaining})
            continue
        for i, (index, begin, end) in enumerate(slots):
            if remaining <= 0: break
            day = days[index]
            amount = min(30, remaining, day['capacity'] - day['minutes'], int((end-begin).total_seconds()//60))
            finish = begin + timedelta(minutes=amount)
            if amount <= 0 or begin >= end or finish > end or finish > due: continue
            day['sessions'].append({'task_id': task['id'], 'title': task['title'], 'course': task['course'], 'start': begin.astimezone(zone).isoformat(), 'end': finish.astimezone(zone).isoformat(), 'minutes': amount})
            day['minutes'] += amount
            remaining -= amount
            slots[i] = (index, finish, end)
        if remaining:
            warnings.append({'title': task['title'], 'reason': 'Not enough time before the deadline or within this week', 'minutes': remaining})
    return {'days': days, 'warnings': warnings, 'scheduled_minutes': sum(d['minutes'] for d in days), 'timezone': tz}
