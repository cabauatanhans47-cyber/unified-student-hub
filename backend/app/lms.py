"""Admin-allowlisted LMS integrations. Tokens are used only for this request."""
import os
from urllib.parse import urlsplit
from datetime import datetime, timezone
import httpx
from .importers import candidate

def base_url(value):
    p = urlsplit(value)
    allowed = {x.strip().lower() for x in os.getenv('LMS_ALLOWED_HOSTS', '').split(',') if x.strip()}
    if p.scheme != 'https' or p.username or p.password or p.port not in (None,443) or p.query or p.fragment or p.hostname not in allowed:
        raise ValueError('This LMS host is not enabled. Ask the server owner to set LMS_ALLOWED_HOSTS to your school’s exact hostname.')
    return value.rstrip('/')

async def preview(provider, base, token, course_ids):
    base = base_url(base)
    rows, warnings = [], []
    async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False) as client:
        if provider == 'canvas':
            for course in course_ids:
                # Sequential, bounded pagination using the fixed trusted endpoint.
                for page in range(1,21):
                    res = await client.get(f'{base}/api/v1/courses/{course}/assignments', headers={'Authorization': f'Bearer {token}'}, params={'per_page':100,'page':page,'include[]':'submission'})
                    res.raise_for_status(); values = res.json()
                    if not isinstance(values, list): raise ValueError('Unexpected Canvas response')
                    for a in values:
                        if a.get('due_at') and not (a.get('submission') or {}).get('submitted_at'):
                            rows.append(candidate(a['name'], datetime.fromisoformat(a['due_at'].replace('Z','+00:00')), f'Course {course}', 'canvas', f'{base}:{course}:{a["id"]}'))
                    if len(values) < 100: break
                else: warnings.append(f'Course {course}: page limit reached. Narrow the import.')
        else:
            params = {'wstoken':token, 'wsfunction':'core_calendar_get_calendar_events', 'moodlewsrestformat':'json', 'options[userevents]':1,'options[siteevents]':0, 'options[timestart]':int(datetime.now(timezone.utc).timestamp()), 'options[timeend]':int(datetime.now(timezone.utc).timestamp()) + 180*86400}
            for index, course in enumerate(course_ids): params[f'events[courseids][{index}]'] = course
            res = await client.post(f'{base}/webservice/rest/server.php', data=params)
            res.raise_for_status(); data = res.json()
            if 'exception' in data: raise ValueError('Moodle rejected the request. Check your token and enabled web-service functions.')
            for e in data.get('events', []):
                # Only due/close action events are deadlines, not lecture start events.
                if e.get('eventtype') not in ('due','close'): continue
                if e.get('timestart'):
                    rows.append(candidate(e['name'], datetime.fromtimestamp(e['timestart'], timezone.utc), f'Course {e.get("courseid", "Moodle")}', 'moodle', f'{base}:{e["id"]}'))
            warnings.append('Moodle imports due/close calendar events for the next 180 days. Your school must enable core_calendar_get_calendar_events for your token.')
    if len(rows) > 500: warnings.append('Preview limited to 500 deadlines. Import fewer courses at a time.')
    return {'tasks': rows[:500], 'events': [], 'warnings': warnings}
