import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Boolean, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def normalize_database_url(value):

    for prefix in ('postgres://', 'postgresql://'):
        if value.startswith(prefix):
            return 'postgresql+psycopg://' + value[len(prefix):]
    return value

database_url = normalize_database_url(os.getenv('DATABASE_URL', 'sqlite:///./hub.db'))
engine = create_engine(database_url, pool_pre_ping=True,
                       **({'connect_args': {'check_same_thread': False}} if database_url.startswith('sqlite:') else {}))
SessionLocal = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(Text)
class LoginSession(Base):
    __tablename__ = 'sessions'
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    expires: Mapped[int] = mapped_column(Integer)
class StudyPreferences(Base):
    __tablename__ = 'study_preferences'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    tz: Mapped[str] = mapped_column(String(100), default='Asia/Manila')
    start_hour: Mapped[int] = mapped_column(Integer, default=17)
    end_hour: Mapped[int] = mapped_column(Integer, default=21)
    daily_minutes: Mapped[int] = mapped_column(Integer, default=120)
    plan_seen: Mapped[bool] = mapped_column(Boolean, default=False)
class SyncReceipt(Base):
    __tablename__ = 'sync_receipts'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(Text)

class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (UniqueConstraint('user_id', 'external_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    course: Mapped[str] = mapped_column(String(100), default='General')
    due: Mapped[str] = mapped_column(String(40))
    minutes: Mapped[int] = mapped_column(Integer, default=60)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(32), default='manual')
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
class BusyEvent(Base):
    __tablename__ = 'events'
    __table_args__ = (UniqueConstraint('user_id', 'external_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start: Mapped[str] = mapped_column(String(40))
    end: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str] = mapped_column(String(64))
def db():
    with SessionLocal() as s: yield s
