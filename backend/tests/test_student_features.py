from datetime import date,datetime,timezone
import pytest
from sqlalchemy import select
from app.models import RecoveryKey, AuthThrottle
from app.student_features import class_events,StudentSettingsInput,shared_throttle
from app.planner import plan_week
from test_hub import client,register,task

def test_weekly_settings_and_account_isolation(client):
    register(client)
    settings=client.get('/api/student-settings').json()
    settings['custom_days']=True
    settings['days'][1]['enabled']=False
    settings['classes']=[dict(id='lab',title='Lab',weekday=0,start_time='17:00',end_time='18:00',first_date='2030-01-01',last_date='2030-06-30')]
    assert client.put('/api/student-settings',json=settings).status_code==200
    assert client.get('/api/student-settings').json()==settings
    settings['days'][0]['end_hour']=1
    assert client.put('/api/student-settings',json=settings).status_code==422
    client.post('/api/auth/logout');register(client,'another')
    other=client.get('/api/student-settings').json()
    assert not other['custom_days'] and not other['classes']

def test_per_day_schedule_excludes_classes_and_disabled_days():
    advanced=StudentSettingsInput().model_dump(mode='json');advanced['custom_days']=True
    for d in advanced['days']:d['enabled']=False
    advanced['days'][0].update(enabled=True,start_hour=17,end_hour=20,daily_minutes=120)
    advanced['classes']=[dict(id='lab',title='Lab',weekday=0,start_time='17:00',end_time='18:00',first_date='2030-01-01',last_date='2030-01-31')]
    start=date(2030,1,7)
    events=class_events(advanced,start,'Asia/Manila')
    assert len(events)==1
    t=task();t.update(due='2030-01-08T23:59:00+08:00',minutes=180)
    p=plan_week([t],events,start,'Asia/Manila',now=datetime(2030,1,7,tzinfo=timezone.utc),day_settings=advanced['days'])
    assert p['scheduled_minutes']==120 and p['warnings'][0]['minutes']==60
    assert p['days'][0]['sessions'][0]['start']=='2030-01-07T18:00:00+08:00'
    assert all(d['minutes']==0 for d in p['days'][1:])
    assert class_events(advanced,date(2030,2,4),'Asia/Manila')==[]

def test_recovery_is_single_use_and_revokes_sessions(client):
    register(client)
    cookie=client.cookies.get('hub_session')
    assert client.post('/api/account/recovery',json={'password':'wrong'}).status_code==401
    r=client.post('/api/account/recovery',json={'password':'strong-password-123'})
    assert r.status_code==200
    code=r.json()['recovery_code']
    assert client.get('/api/account/recovery').json()=={'enabled':True}
    client.cookies.clear()  # Keep the server session alive to verify reset revokes it.
    payload={'username':'student','recovery_code':code,'password':'new-strong-password-456'}
    assert client.post('/api/auth/recover',json={**payload,'recovery_code':'x'*43}).status_code==400
    assert client.post('/api/auth/recover',json=payload).status_code==200
    assert client.post('/api/auth/recover',json=payload).status_code==400
    client.cookies.set('hub_session',cookie)
    assert client.get('/api/tasks').status_code==401
    client.cookies.clear()
    assert client.post('/api/auth/login',json={'username':'student','password':'strong-password-123'}).status_code==401
    assert client.post('/api/auth/login',json={'username':'student','password':payload['password']}).status_code==200
    assert client.get('/api/account/recovery').json()=={'enabled':False}

def test_export_no_secrets_and_delete_only_current_account(client):
    register(client,'keeper');client.post('/api/tasks',json=task());client.post('/api/auth/logout')
    register(client)
    client.post('/api/tasks',json=task())
    settings=client.get('/api/student-settings').json()
    client.put('/api/student-settings',json=settings)
    client.post('/api/account/recovery',json={'password':'strong-password-123'})
    export=client.get('/api/account/export').json()
    assert len(export['tasks'])==1 and 'password' not in str(export) and 'recovery_code' not in str(export)
    assert client.request('DELETE','/api/account',json={'password':'wrong'}).status_code==401
    assert client.request('DELETE','/api/account',json={'password':'strong-password-123'}).status_code==200
    assert client.get('/api/me').status_code==401
    assert client.post('/api/auth/login',json={'username':'student','password':'strong-password-123'}).status_code==401
    assert client.post('/api/auth/login',json={'username':'keeper','password':'strong-password-123'}).status_code==200
    assert len(client.get('/api/tasks').json())==1

def test_missing_vercel_database_does_not_accept_accounts(client,monkeypatch):
    monkeypatch.setenv('VERCEL','1');monkeypatch.delenv('DATABASE_URL',raising=False)
    response=client.post('/api/auth/register',json={'username':'student','password':'strong-password-123'})
    assert response.status_code==503
    assert 'DATABASE_URL' in response.json()['detail']

def test_throttle_survives_process_memory_reset(client):
    from app.main import failures
    for _ in range(20):
        response=client.post('/api/auth/login',json={'username':'student','password':'strong-password-123'})
        assert response.status_code==401
        failures.clear()
    assert client.post('/api/auth/login',json={'username':'student','password':'strong-password-123'}).status_code==429
