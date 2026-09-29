"""Bounded, review-first importers. No imported file is retained."""
import hashlib, io, re
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from icalendar import Calendar
from pypdf import PdfReader

def key(source, value): return hashlib.sha256(f'{source}:{value}'.encode()).hexdigest()
def candidate(title, due, course, source, external):
    return {'title': title[:200] or 'Untitled deadline', 'course': course[:100] or 'General', 'due': due.isoformat(), 'minutes': 60, 'done': False, 'source': source, 'external_id': key(source, external)}

def syllabus(data, filename, tz):
    if filename.lower().endswith('.pdf'):
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted: raise ValueError('Please unlock this PDF before importing it.')
        if len(reader.pages) > 50: raise ValueError('Use a PDF with at most 50 pages.')
        text = '\n'.join((p.extract_text() or '') for p in reader.pages)
    else: text = data.decode('utf-8-sig')
    rows = []
    pattern = r'\b(\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
    for line in text.splitlines():
        hit = re.search(pattern, line, flags=re.I)
        if not hit: continue
        value = hit.group(1)
        try:
            day = datetime.strptime(value, '%Y-%m-%d').date() if value[0].isdigit() else datetime.strptime(value.replace(',', ''), '%B %d %Y').date()
        except ValueError: continue
        title = (line[:hit.start()] + line[hit.end():]).strip(' \t:-–—|')
        due = datetime.combine(day, time(23,59), ZoneInfo(tz))
        rows.append(candidate(title, due, 'Syllabus', 'syllabus', f'{line.strip()}'))
        if len(rows) >= 500: break
    warnings = ['Only dates with an explicit year (YYYY-MM-DD or Month DD, YYYY) are extracted. Times default to 23:59 in your timezone. Check every title and date; tables may parse imperfectly. Scans need OCR before upload.']
    if not rows: warnings.append('No supported dates found. Use a text-based PDF or enter the deadline manually.')
    return {'tasks': rows, 'events': [], 'warnings': warnings}

def calendar(data, tz, as_deadlines=False):
    cal = Calendar.from_ical(data)
    tasks, events, warnings = [], [], []
    zone = ZoneInfo(tz)
    def aware(value):
        if isinstance(value, datetime): return value if value.tzinfo else value.replace(tzinfo=zone)
        return datetime.combine(value, time.min, zone)
    for event in cal.walk('VEVENT'):
        if len(tasks) + len(events) >= 500:
            warnings.append('Only the first 500 events were loaded. Split large exports.'); break
        if event.get('RRULE') or event.get('RECURRENCE-ID') or event.get('RDATE'):
            warnings.append(f"Skipped recurring event: {str(event.get('SUMMARY', 'Untitled'))[:100]}. Export individual occurrences instead."); continue
        if str(event.get('STATUS', '')).upper() == 'CANCELLED': continue
        if not event.get('DTSTART'): continue
        raw = event.decoded('DTSTART'); start = aware(raw)
        end = aware(event.decoded('DTEND')) if event.get('DTEND') else start + (event.decoded('DURATION') if event.get('DURATION') else timedelta(minutes=60) if isinstance(raw, datetime) else timedelta(days=1))
        title = str(event.get('SUMMARY', 'Calendar event'))[:200]
        identity = str(event.get('UID', f'{title}:{start.isoformat()}'))
        if as_deadlines:
            due = start if isinstance(raw, datetime) else datetime.combine(raw, time(23,59), zone)
            tasks.append(candidate(title, due, 'Calendar', 'calendar', identity))
        elif str(event.get('TRANSP', '')).upper() != 'TRANSPARENT' and end > start:
            events.append({'title': title, 'start': start.isoformat(), 'end': end.isoformat(), 'external_id': key('calendar-busy', identity)})
    return {'tasks': tasks, 'events': events, 'warnings': warnings}
