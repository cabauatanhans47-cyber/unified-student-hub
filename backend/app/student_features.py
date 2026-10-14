"""Student scheduling, portable account recovery, and account data controls."""
import json, secrets, hashlib, time
from datetime import date, datetime, time as clock, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Literal
from fastapi import Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, delete, case
from sqlalchemy.orm import Session
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from .models import (db, User, LoginSession, Task, BusyEvent, StudyPreferences, SyncReceipt,
                     StudentSettings, RecoveryKey, AuthThrottle)

class DayWindow(BaseModel):
    enabled: bool = True
    start_hour: int = Field(17, ge=0, le=22)
    end_hour: int = Field(21, ge=1, le=23)
    daily_minutes: int = Field(120, ge=30, le=720)
    @model_validator(mode='after')
    def order(self):
        if self.end_hour <= self.start_hour: raise ValueError('Study end must be after start.')
        return self
class WeeklyClass(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    title: str = Field(min_length=1, max_length=120)
    weekday: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    end_time: str = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    first_date: date
    last_date: date
    @model_validator(mode='after')
    def order(self):
        if self.end_time <= self.start_time: raise ValueError('Class end must be after start on the same day.')
        if self.last_date < self.first_date: raise ValueError('Last class date must follow first date.')
        if not self.title.strip(): raise ValueError('Class title cannot be empty.')
        return self
class StudentSettingsInput(BaseModel):
    custom_days: bool = False
    days: list[DayWindow] = Field(default_factory=lambda:[DayWindow() for _ in range(7)],min_length=7,max_length=7)
    classes: list[WeeklyClass] = Field(default_factory=list,max_length=60)
    reminders: bool = False
    reminder_hours: int = Field(24,ge=1,le=168)
    @model_validator(mode='after')
    def ids(self):
        values=[x.id for x in self.classes]
        if len(set(values)) != len(values): raise ValueError('Class IDs must be unique.')
        return self
class PasswordCheck(BaseModel):
    password: str = Field(min_length=1,max_length=128)
class ResetInput(BaseModel):
    username: str = Field(min_length=3,max_length=40,pattern=r'^[A-Za-z0-9_-]+$')
    recovery_code: str = Field(min_length=20,max_length=128)
    password: str = Field(min_length=12,max_length=128)

def settings_for(s,uid):
    record=s.get(StudentSettings,uid)
    return StudentSettingsInput.model_validate_json(record.data).model_dump(mode='json') if record else StudentSettingsInput().model_dump(mode='json')

def class_events(settings,start,tz):
    zone=ZoneInfo(tz); result=[]
    for offset in range(7):
        day=start+timedelta(days=offset)
        for c in settings.get('classes',[]):
            if day.weekday()!=c['weekday'] or not c['first_date']<=day.isoformat()<=c['last_date']: continue
            begin=datetime.combine(day,clock.fromisoformat(c['start_time']),zone)
            end=datetime.combine(day,clock.fromisoformat(c['end_time']),zone)
            result.append({'title':c['title'],'start':begin.isoformat(),'end':end.isoformat()})
    return result

def shared_throttle(s,bucket,maximum=20):
    """Atomic fixed-window counters shared across serverless instances."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    now=int(time.time()); bucket=hashlib.sha256(bucket.encode()).hexdigest()
    insert=pg_insert if s.bind.dialect.name=='postgresql' else sqlite_insert
    stmt=insert(AuthThrottle).values(bucket=bucket,attempts=1,window_start=now)
    expired=AuthThrottle.window_start <= now-300
    stmt=stmt.on_conflict_do_update(index_elements=['bucket'],set_={
        'attempts':case((expired,1),else_=AuthThrottle.attempts+1),
        'window_start':case((expired,now),else_=AuthThrottle.window_start)
    }).returning(AuthThrottle.attempts)
    s.execute(delete(AuthThrottle).where(AuthThrottle.window_start < now-86400))
    count=s.execute(stmt).scalar_one();s.commit()
    if count>maximum: raise HTTPException(429,'Too many attempts. Try again in five minutes.',headers={'Retry-After':'300'})

def install_routes(app,user,hasher):
    def verify(s,uid,password):
        shared_throttle(s,'sensitive:'+str(uid),10)
        value=s.get(User,uid)
        try: hasher.verify(value.password,password)
        except (VerifyMismatchError,InvalidHashError): raise HTTPException(401,'Incorrect password.')
        return value
    @app.get('/api/student-settings')
    def get_settings(uid=Depends(user),s:Session=Depends(db)): return settings_for(s,uid)
    @app.put('/api/student-settings')
    def save_settings(body:StudentSettingsInput,uid=Depends(user),s:Session=Depends(db)):
        # Serialize writers on the account, also protecting against initial row races.
        s.scalar(select(User).where(User.id==uid).with_for_update())
        value=s.get(StudentSettings,uid)
        if value is None: value=StudentSettings(user_id=uid);s.add(value)
        value.data=body.model_dump_json();s.commit();return body.model_dump(mode='json')
    @app.get('/api/account/recovery')
    def recovery_status(uid=Depends(user),s:Session=Depends(db)):
        return {'enabled':s.get(RecoveryKey,uid) is not None}
    @app.post('/api/account/recovery')
    def create_recovery(body:PasswordCheck,uid=Depends(user),s:Session=Depends(db)):
        verify(s,uid,body.password)
        s.scalar(select(User).where(User.id==uid).with_for_update())
        code=secrets.token_urlsafe(32)
        value=s.get(RecoveryKey,uid)
        if value is None:value=RecoveryKey(user_id=uid);s.add(value)
        value.digest=hashlib.sha256(code.encode()).hexdigest();s.commit()
        return {'recovery_code':code}
    @app.post('/api/auth/recover')
    def recover(body:ResetInput,response:Response,s:Session=Depends(db)):
        shared_throttle(s,'recover:'+body.username.lower(),10)
        account=s.scalar(select(User).where(User.username==body.username.lower()).with_for_update())
        value=s.get(RecoveryKey,account.id) if account else None
        candidate=hashlib.sha256(body.recovery_code.strip().encode()).hexdigest()
        if not value or not secrets.compare_digest(value.digest,candidate):
            raise HTTPException(400,'Username or recovery code is incorrect. Codes work once.')
        account.password=hasher.hash(body.password);s.delete(value)
        s.execute(delete(LoginSession).where(LoginSession.user_id==account.id));s.commit()
        response.delete_cookie('hub_session',path='/')
        return {'ok':True}
    @app.get('/api/account/export')
    def export_account(uid=Depends(user),s:Session=Depends(db)):
        def rows(model,fields):
            return [{f:getattr(row,f) for f in fields} for row in s.scalars(select(model).where(model.user_id==uid))]
        pref=s.get(StudyPreferences,uid)
        return {'format':'student-hub-account-v1','exported_at':datetime.now(timezone.utc).isoformat(),
                'username':s.get(User,uid).username,
                'tasks':rows(Task,('id','title','course','due','minutes','done','source','external_id')),
                'events':rows(BusyEvent,('id','title','start','end','external_id')),
                'preferences':{k:getattr(pref,k) for k in ('tz','start_hour','end_hour','daily_minutes','plan_seen')} if pref else None,
                'student_settings':settings_for(s,uid)}
    @app.delete('/api/account')
    def delete_account(body:PasswordCheck,response:Response,uid=Depends(user),s:Session=Depends(db)):
        verify(s,uid,body.password)
        s.scalar(select(User).where(User.id==uid).with_for_update())
        for model in (RecoveryKey,StudentSettings,SyncReceipt,Task,BusyEvent,StudyPreferences,LoginSession):
            s.execute(delete(model).where(model.user_id==uid))
        s.execute(delete(User).where(User.id==uid));s.commit()
        response.delete_cookie('hub_session',path='/');return {'ok':True}
