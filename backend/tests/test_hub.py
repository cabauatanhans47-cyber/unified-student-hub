import os
os.environ['DATABASE_URL']='sqlite://'
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, failures
from app.models import Base, db
from app.planner import plan_week, stamp
from app.importers import syllabus, calendar
from app.lms import base_url

@pytest.fixture
def client():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine); factory=sessionmaker(bind=engine)
    def session():
        with factory() as s: yield s
    app.dependency_overrides[db]=session; failures.clear()
    with TestClient(app,headers={'X-Requested-With':'StudentHub'}) as c: yield c
    app.dependency_overrides.clear(); engine.dispose()

def register(c,name='student'):
    r=c.post('/api/auth/register',json={'username':name,'password':'strong-password-123'})
    assert r.status_code==200,r.text
    assert 'HttpOnly' in r.headers['set-cookie']

def task(): return dict(id=1,title='Lab report',course='CPE',due='2030-01-02T21:00:00+08:00',minutes=60,done=False)

def test_accounts_isolate_data_and_sessions(client):
    assert client.get('/api/tasks').status_code==401
    register(client); r=client.post('/api/tasks',json=task()); assert r.status_code==201
    id=r.json()['id']; cookie=client.cookies.get('hub_session')
    client.post('/api/auth/logout'); assert client.get('/api/tasks').status_code==401
    client.cookies.set('hub_session',cookie); assert client.get('/api/tasks').status_code==401
    client.cookies.clear(); register(client,'other')
    assert client.get('/api/tasks').json()==[]
    assert client.put(f'/api/tasks/{id}',json=task()).status_code==404
    assert client.delete(f'/api/tasks/{id}').status_code==404
    assert client.get('/api/export/calendar').status_code==200

def test_csrf_and_date_validation(client):
    register(client)
    assert client.post('/api/tasks',json=task(),headers={'X-Requested-With':''}).status_code==403
    invalid=task();invalid['due']='2030-01-02T21:00:00'
    assert client.post('/api/tasks',json=invalid).status_code==422
    assert client.get('/api/plan',params={'start':'2030-01-01','tz':'invalid'}).status_code==422
    assert client.get('/api/plan',params={'start':'2030-01-01','start_hour':22,'end_hour':17}).status_code==422

def test_preview_confirm_dedup_and_completion_preserved(client):
    register(client)
    r=client.post('/api/import/file',files={'file':('syllabus.txt',b'Lab report - 2030-01-02')})
    assert r.status_code==200,r.text
    data=r.json();assert len(data['tasks'])==1
    assert client.get('/api/tasks').json()==[]
    body={'tasks':data['tasks'],'events':[]}
    assert client.post('/api/import/confirm',json=body).json()['added']==1
    t=client.get('/api/tasks').json()[0];t.update(done=True,minutes=120)
    client.put('/api/tasks/'+str(t['id']),json=t)
    assert client.post('/api/import/confirm',json=body).json()['updated']==1
    rows=client.get('/api/tasks').json();assert len(rows)==1 and rows[0]['done'] and rows[0]['minutes']==120

def test_bad_upload(client):
    register(client)
    assert client.post('/api/import/file',files={'file':('bad.exe',b'x')}).status_code==400
    assert client.post('/api/import/file',files={'file':('bad.pdf',b'not a pdf')}).status_code==400
    assert client.post('/api/import/file',files={'file':('large.txt',b'x'*(2*1024*1024+1))}).status_code==413

def test_busy_time_capacity_and_deadline():
    now=datetime(2030,1,1,tzinfo=timezone.utc)
    busy=[{'start':'2030-01-01T17:00:00+08:00','end':'2030-01-01T18:00:00+08:00'}]
    t=task();t['minutes']=300;t['due']='2030-01-01T20:00:00+08:00'
    p=plan_week([t],busy,date(2030,1,1),'Asia/Manila',17,21,60,now)
    assert p['scheduled_minutes']==60 and p['warnings'][0]['minutes']==240
    sessions=[x for d in p['days'] for x in d['sessions']]
    assert all(stamp(s['start'])>=stamp(busy[0]['end']) and stamp(s['end'])<=stamp(t['due']) for s in sessions)

def test_overdue_and_done_do_not_get_planned():
    t=task();t['due']='2029-12-31T12:00:00Z'
    done=task();done['done']=True
    p=plan_week([t,done],[],date(2030,1,1),'UTC',now=datetime(2030,1,1,tzinfo=timezone.utc))
    assert p['scheduled_minutes']==0 and p['warnings'][0]['reason']=='Overdue'

def test_syllabus_requires_year():
    data=b'Quiz - January 2, 2030\nLab - 2030-01-03\nIgnore 1/4\nBad 2030-99-99'
    result=syllabus(data,'x.txt','Asia/Manila')
    assert len(result['tasks'])==2 and result['tasks'][0]['due']=='2030-01-02T23:59:00+08:00'

def test_ics_timezone_all_day_and_recurring():
    data=b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:one\r\nSUMMARY:Class\r\nDTSTART:20300101T090000Z\r\nDTEND:20300101T100000Z\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:two\r\nSUMMARY:Holiday\r\nDTSTART;VALUE=DATE:20300102\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:three\r\nSUMMARY:Recurring\r\nDTSTART:20300101T090000Z\r\nRRULE:FREQ=WEEKLY\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
    r=calendar(data,'Asia/Manila');assert len(r['events'])==2 and len(r['warnings'])==1
    assert r['events'][1]['end']=='2030-01-03T00:00:00+08:00'
    r=calendar(data,'Asia/Manila',True);assert len(r['tasks'])==2 and r['tasks'][1]['due']=='2030-01-02T23:59:00+08:00'

def test_lms_allowlist(monkeypatch):
    monkeypatch.setenv('LMS_ALLOWED_HOSTS','school.instructure.com')
    assert base_url('https://school.instructure.com/')=='https://school.instructure.com'
    for url in ['http://school.instructure.com','https://evil.com','https://school.instructure.com.evil.com','https://x@school.instructure.com','https://school.instructure.com:8080','http://127.0.0.1']:
        with pytest.raises(ValueError): base_url(url)

def test_invalid_calendar_rolls_back_import(client):
    register(client)
    r=client.post('/api/import/confirm',json={'tasks':[task()],'events':[{'title':'Invalid','start':'2030-01-02T09:00:00Z','end':'2030-01-01T09:00:00Z','external_id':'event'}]})
    assert r.status_code==422 and client.get('/api/tasks').json()==[]

def test_no_overlapping_allocations_with_partial_blocks():
    small=task();small['minutes']=15
    larger=task();larger.update(id=2,minutes=45)
    p=plan_week([small,larger],[],date(2030,1,1),'UTC',17,18,60,datetime(2030,1,1,tzinfo=timezone.utc))
    sessions=p['days'][0]['sessions']
    assert p['scheduled_minutes']==60 and not p['warnings']
    assert sum(s['minutes'] for s in sessions)==60
    for a,b in zip(sessions,sessions[1:]): assert stamp(a['end'])<=stamp(b['start'])

def test_dst_spring_forward_never_invents_time():
    t=task();t.update(minutes=240,due='2030-03-11T00:00:00-04:00')
    p=plan_week([t],[],date(2030,3,10),'America/New_York',1,4,240,datetime(2030,3,10,tzinfo=timezone.utc))
    assert p['scheduled_minutes']==120 and p['warnings'][0]['minutes']==120

def test_calendar_events_are_account_scoped(client):
    register(client)
    event={'title':'Class','start':'2030-01-01T09:00:00Z','end':'2030-01-01T10:00:00Z','external_id':'class-one'}
    assert client.post('/api/import/confirm',json={'events':[event]}).json()['added']==1
    id=client.get('/api/events').json()[0]['id']
    client.post('/api/auth/logout');register(client,'another')
    assert client.get('/api/events').json()==[]
    assert client.delete('/api/events/'+str(id)).status_code==404

def test_lms_adapters_use_transient_credentials_and_fixed_endpoints(monkeypatch):
    import asyncio, httpx
    from app import lms
    monkeypatch.setenv('LMS_ALLOWED_HOSTS','school.example')
    requests=[]
    def handle(request):
        requests.append(request)
        if '/api/v1/' in str(request.url):
            assert request.headers['Authorization']=='Bearer transient-token'
            return httpx.Response(200,json=[{'id':1,'name':'Canvas lab','due_at':'2030-01-02T09:00:00Z','submission':None}])
        assert b'wstoken=transient-token' in request.content
        assert b'events%5Bcourseids%5D%5B0%5D=123' in request.content
        return httpx.Response(200,json={'events':[{'id':2,'name':'Moodle task','eventtype':'due','timestart':1893574800,'courseid':123},{'id':3,'name':'Lecture','eventtype':'open','timestart':1893574800}]})
    original=httpx.AsyncClient
    monkeypatch.setattr(lms.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    for provider in ['canvas','moodle']:
        r=asyncio.run(lms.preview(provider,'https://school.example','transient-token',[123]))
        assert len(r['tasks'])==1 and 'transient-token' not in str(r)
    assert len(requests)==2

def test_text_pdf_preview_extracts_deadline(client):
    from io import BytesIO
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 72 720 Td (Lab report - 2030-01-02) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=BytesIO();writer.write(output)
    register(client)
    r=client.post('/api/import/file',files={'file':('syllabus.pdf',output.getvalue(),'application/pdf')})
    assert r.status_code==200 and r.json()['tasks'][0]['title']=='Lab report'
