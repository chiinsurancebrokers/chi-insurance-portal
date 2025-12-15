import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class PaymentStatus(enum.Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    OVERDUE = "OVERDUE"

class PolicyStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class EmailStatus(enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"

class EmailQueue(Base):
    __tablename__ = 'email_queue'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)
    recipient_email = Column(String(200), nullable=False)
    subject = Column(String(500))
    body_html = Column(String(10000))
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.QUEUED)
    sent_at = Column(DateTime)
    error_message = Column(String(1000))
    created_date = Column(DateTime, default=datetime.now)
    
    client = relationship('Client')
    policy = relationship('Policy')
    payment = relationship('Payment')

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    address = Column(String(300))
    postal_code = Column(String(20))
    city = Column(String(100))
    tax_id = Column(String(50))
    created_date = Column(DateTime, default=datetime.now)
    
    policies = relationship('Policy', back_populates='client', cascade='all, delete-orphan')

class Policy(Base):
    __tablename__ = 'policies'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    policy_type = Column(String(100), nullable=False)
    provider = Column(String(100))
    license_plate = Column(String(20))
    premium = Column(Float)
    start_date = Column(Date)
    expiration_date = Column(Date)
    status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.ACTIVE)
    created_date = Column(DateTime, default=datetime.now)
    
    client = relationship('Client', back_populates='policies')
    payments = relationship('Payment', back_populates='policy', cascade='all, delete-orphan')

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    notes = Column(String(500))
    created_date = Column(DateTime, default=datetime.now)
    
    policy = relationship('Policy', back_populates='payments')

def get_database_url():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    return 'sqlite:///data/database/chi_insurance.db'

# Create engine ONCE at module level
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_recycle=3600
        )
    return _engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
