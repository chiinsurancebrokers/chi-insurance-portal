#!/usr/bin/env python3
from src.database.models import Base, get_engine, EmailQueue

engine = get_engine()
Base.metadata.create_all(engine)
print("✓ Created email_queue table")
