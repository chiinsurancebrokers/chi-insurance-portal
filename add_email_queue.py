with open('src/database/models.py', 'r') as f:
    content = f.read()

# Add after PolicyStatus enum
email_queue_model = '''
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
'''

# Insert after PolicyStatus
insertion_point = content.find('class Client(Base):')
content = content[:insertion_point] + email_queue_model + '\n' + content[insertion_point:]

with open('src/database/models.py', 'w') as f:
    f.write(content)

print("✓ Added EmailQueue model")
