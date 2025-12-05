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

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(100))
    address = Column(String(500))
    postal_code = Column(String(20))
    city = Column(String(100))
    tax_id = Column(String(50))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    policies = relationship("Policy", back_populates="client")

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    policy_number = Column(String(100))
    provider = Column(String(200))
    policy_type = Column(String(100))
    license_plate = Column(String(20))
    vehicle_model = Column(String(100))
    vehicle_year = Column(Integer)
    premium = Column(Float)
    start_date = Column(Date)
    expiration_date = Column(Date)
    status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.ACTIVE)
    payment_code = Column(String(100))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    client = relationship("Client", back_populates="policies")
    payments = relationship("Payment", back_populates="policy")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date)
    due_date = Column(Date)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(100))
    notes = Column(String(500))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    policy = relationship("Policy", back_populates="payments")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    policy_id = Column(Integer, ForeignKey('policies.id'))
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    document_type = Column(String(100))
    upload_date = Column(DateTime, default=datetime.now)

# Database connection - USE ENVIRONMENT VARIABLE!
def get_database_url():
    """Get database URL from environment or default to SQLite"""
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Railway/Heroku use postgres:// but SQLAlchemy needs postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    
    # Fallback to SQLite for local development
    return 'sqlite:///data/database/chi_insurance.db'

def get_engine():
    return create_engine(get_database_url())

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
