import hashlib, os, secrets, time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from icalendar import Calendar, Event
import httpx
from .models import Base, engine, db, User, LoginSession, Task, BusyEvent
from .planner import plan_week, stamp
from . import importers, lms

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield
app = FastAPI(title='Unified Student Hub API', version='0.1.0', lifespan=lifespan)
hasher = PasswordHasher()
DUMMY_HASH = hasher.hash('not-a-real-user-password')
failures = defaultdict(deque)

def digest(token): return hashlib.sha256(token.encode()).hexdigest()
def user(request: Request, s: Session = Depends(db)):
    value = request.cookies.get('hub_session', '')
    record = s.get(LoginSession, digest(value)) if value else None
    if not record or record.expires < time.time(): raise HTTPException(401, 'Sign in to continue.')
    return record.user_id

@app.middleware('http')
async def guard(request, call_next):
    if request.method in ('POST','PUT','PATCH','DELETE') and request.url.path.startswith('/api/'):
        if request.headers.get('x-requested-with') != 'StudentHub':
            return Response('Missing request verification header', status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path.startswith('/api/'): response.headers['Cache-Control'] = 'no-store'
    return response

class Credentials(BaseModel):
    username: str = Field(min_length=3,max_length=40,pattern=r'^[A-Za-z0-9_-]+$')
    password: str = Field(min_length=12,max_length=128)

def throttle(request):
    address = request.client.host if request.client else 'unknown'
    q = failures[address]
    now = time.monotonic()
    while q and q[0] < now - 300: q.popleft()
    if len(q) >= 20: raise HTTPException(429, 'Too many attempts. Wait five minutes.')
    q.append(now)
    if len(failures) > 10000:
        for k in list(failures):
            if not failures[k] or failures[k][-1] < now - 300: del failures[k]

def login_cookie(response, s, uid):
    s.execute(delete(LoginSession).where(LoginSession.expires < int(time.time())))
    token = secrets.token_urlsafe(32)
    s.add(LoginSession(token=digest(token),user_id=uid,expires=int(time.time())+7*86400)); s.commit()
    response.set_cookie('hub_session',token,httponly=True,samesite='lax',secure=os.getenv('COOKIE_SECURE','false').lower()=='true',max_age=7*86400,path='/')

@app.post('/api/auth/register')
def register(body: Credentials, request: Request, response: Response, s: Session=Depends(db)):
    throttle(request)
    if os.getenv('ALLOW_REGISTRATION','true').lower() != 'true': raise HTTPException(403,'Registration is closed.')
    u = User(username=body.username.lower(),password=hasher.hash(body.password)); s.add(u)
    try: s.commit()
    except IntegrityError: s.rollback(); raise HTTPException(409,'That username is unavailable.')
    login_cookie(response,s,u.id)
    return {'username':u.username}

@app.post('/api/auth/login')
def login(body: Credentials, request: Request, response: Response, s: Session=Depends(db)):
    throttle(request)
    u = s.scalar(select(User).where(User.username==body.username.lower()))
    try: hasher.verify(u.password if u else DUMMY_HASH,body.password)
    except (VerifyMismatchError,InvalidHashError): raise HTTPException(401,'Incorrect username or password.')
    if not u: raise HTTPException(401,'Incorrect username or password.')
    login_cookie(response,s,u.id)
    return {'username':u.username}

@app.post('/api/auth/logout')
def logout(request: Request, response: Response, s: Session=Depends(db)):
    s.execute(delete(LoginSession).where(LoginSession.token==digest(request.cookies.get('hub_session','')))); s.commit()
    response.delete_cookie('hub_session',path='/')
    return {'ok':True}
@app.get('/api/me')
def me(uid=Depends(user), s: Session=Depends(db)): return {'username':s.get(User,uid).username}

class TaskInput(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    course: str = Field(default='General',min_length=1,max_length=100)
    due: str
    minutes: int = Field(default=60,ge=15,le=2400)
    done: bool = False
    source: Literal['manual','syllabus','calendar','canvas','moodle'] = 'manual'
    external_id: str | None = Field(default=None,max_length=64)
    @field_validator('title','course')
    @classmethod
    def clean(cls,v):
        if not v.strip(): raise ValueError('Cannot be blank')
        return v.strip()
    @field_validator('due')
    @classmethod
    def valid_due(cls,v): return stamp(v).astimezone(timezone.utc).isoformat()
class EventInput(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    start: str
    end: str
    external_id: str = Field(min_length=1,max_length=64)
    @field_validator('start','end')
    @classmethod
    def valid_time(cls,v): return stamp(v).astimezone(timezone.utc).isoformat()
class ImportInput(BaseModel):
    tasks: list[TaskInput] = Field(default_factory=list,max_length=500)
    events: list[EventInput] = Field(default_factory=list,max_length=500)
class LMSInput(BaseModel):
    provider: Literal['canvas','moodle']
    base_url: str = Field(max_length=300)
    token: str = Field(min_length=1,max_length=4000)
    course_ids: list[int] = Field(min_length=1,max_length=10)
    @field_validator('course_ids')
    @classmethod
    def positive(cls,v):
        if any(x<=0 for x in v): raise ValueError('Course IDs must be positive')
        return list(dict.fromkeys(v))

def task_dict(t): return {k:getattr(t,k) for k in ('id','title','course','due','minutes','done','source','external_id')}
def event_dict(e): return {k:getattr(e,k) for k in ('id','title','start','end','external_id')}
def own(s,model,id,uid):
    obj=s.scalar(select(model).where(model.id==id,model.user_id==uid))
    if not obj: raise HTTPException(404,'Item not found.')
    return obj

def limit(s,model,uid,extra=1):
    if s.scalar(select(func.count()).select_from(model).where(model.user_id==uid))+extra>3000:
        raise HTTPException(400,'Limit of 3,000 items reached. Remove old items first.')

@app.get('/api/tasks')
def tasks(uid=Depends(user),s:Session=Depends(db)):
    return [task_dict(t) for t in s.scalars(select(Task).where(Task.user_id==uid).order_by(Task.due))]
@app.post('/api/tasks',status_code=201)
def add_task(body:TaskInput,uid=Depends(user),s:Session=Depends(db)):
    limit(s,Task,uid)
    data=body.model_dump(); data.update(source='manual',external_id=None)
    t=Task(user_id=uid,**data); s.add(t); s.commit(); return task_dict(t)
@app.put('/api/tasks/{id}')
def edit_task(id:int,body:TaskInput,uid=Depends(user),s:Session=Depends(db)):
    t=own(s,Task,id,uid)
    for k,v in body.model_dump(exclude={'source','external_id'}).items(): setattr(t,k,v)
    s.commit(); return task_dict(t)
@app.delete('/api/tasks/{id}')
def delete_task(id:int,uid=Depends(user),s:Session=Depends(db)):
    s.delete(own(s,Task,id,uid)); s.commit(); return {'ok':True}
@app.get('/api/events')
def events(uid=Depends(user),s:Session=Depends(db)):
    return [event_dict(e) for e in s.scalars(select(BusyEvent).where(BusyEvent.user_id==uid))]
@app.delete('/api/events/{id}')
def delete_event(id:int,uid=Depends(user),s:Session=Depends(db)):
    s.delete(own(s,BusyEvent,id,uid)); s.commit(); return {'ok':True}

def valid_zone(tz):
    try: ZoneInfo(tz)
    except (ZoneInfoNotFoundError,ValueError): raise HTTPException(422,'Unknown timezone. Use an IANA name such as Asia/Manila.')
    return tz

@app.post('/api/import/file')
async def preview_file(file:UploadFile=File(...),tz:str='Asia/Manila',mode:Literal['busy','deadlines']='busy',uid=Depends(user)):
    valid_zone(tz)
    data=await file.read(2*1024*1024+1)
    if len(data)>2*1024*1024: raise HTTPException(413,'Maximum file size is 2 MB.')
    name=file.filename or ''
    if not name.lower().endswith(('.pdf','.txt','.ics')): raise HTTPException(400,'Choose a PDF, TXT, or ICS file.')
    try:
        return importers.calendar(data,tz,mode=='deadlines') if name.lower().endswith('.ics') else importers.syllabus(data,name,tz)
    except Exception:
        raise HTTPException(400,'Could not parse this file. Use an unlocked text PDF (50 pages max), UTF-8 text, or a valid ICS export.')
@app.post('/api/import/lms')
async def preview_lms(body:LMSInput,uid=Depends(user)):
    try: return await lms.preview(body.provider,body.base_url,body.token,body.course_ids)
    except ValueError as e: raise HTTPException(400,str(e))
    except (httpx.HTTPError,KeyError,TypeError): raise HTTPException(400,'LMS request failed. Check the hostname, course IDs, token permissions, and school availability.')
@app.post('/api/import/confirm')
def confirm_import(body:ImportInput,uid=Depends(user),s:Session=Depends(db)):
    limit(s,Task,uid,len(body.tasks)); limit(s,BusyEvent,uid,len(body.events))
    added=updated=0
    for value in body.tasks:
        data=value.model_dump()
        if not value.external_id: data['external_id']=importers.key(value.source,f'{value.title}:{value.due}')
        existing=s.scalar(select(Task).where(Task.user_id==uid,Task.external_id==data['external_id']))
        if existing:
            # Sync dates/titles, but retain the student's effort estimate and completion.
            for k in ('title','course','due'): setattr(existing,k,data[k])
            updated+=1
        else: s.add(Task(user_id=uid,**data)); added+=1
        s.flush()
    for value in body.events:
        if stamp(value.end)<=stamp(value.start): raise HTTPException(422,'Calendar end must follow start.')
        existing=s.scalar(select(BusyEvent).where(BusyEvent.user_id==uid,BusyEvent.external_id==value.external_id))
        if existing:
            for k,v in value.model_dump().items(): setattr(existing,k,v)
            updated+=1
        else: s.add(BusyEvent(user_id=uid,**value.model_dump())); added+=1
        s.flush()
    s.commit(); return {'added':added,'updated':updated}

@app.get('/api/plan')
def plan(start:date,tz:str='Asia/Manila',start_hour:int=Query(17,ge=0,le=22),end_hour:int=Query(21,ge=1,le=23),daily_minutes:int=Query(120,ge=30,le=720),uid=Depends(user),s:Session=Depends(db)):
    valid_zone(tz)
    if end_hour<=start_hour: raise HTTPException(422,'End hour must follow start hour.')
    return plan_week(tasks(uid,s),events(uid,s),start,tz,start_hour,end_hour,daily_minutes)
@app.get('/api/export/calendar')
def export(uid=Depends(user),s:Session=Depends(db)):
    cal=Calendar(); cal.add('prodid','-//Unified Student Hub//EN'); cal.add('version','2.0')
    for t in s.scalars(select(Task).where(Task.user_id==uid,Task.done==False)):
        e=Event(); e.add('uid',f'task-{t.id}@student-hub'); e.add('dtstamp',datetime.now(timezone.utc)); e.add('dtstart',stamp(t.due)); e.add('summary',f'{t.course}: {t.title}'); e.add('description',f'Deadline. Estimated effort: {t.minutes} minutes.'); cal.add_component(e)
    return Response(cal.to_ical(),media_type='text/calendar',headers={'Content-Disposition':'attachment; filename="student-hub-deadlines.ics"'})
@app.get('/api/health')
def health(): return {'status':'ok'}

frontend=Path(os.getenv('FRONTEND_DIST',str(Path(__file__).resolve().parents[2]/'frontend'/'dist')))
if frontend.is_dir():
    app.mount('/assets',StaticFiles(directory=frontend/'assets'),name='assets')
    @app.get('/')
    def index(): return FileResponse(frontend/'index.html')
    @app.get('/favicon.svg')
    def favicon(): return FileResponse(frontend/'favicon.svg')
