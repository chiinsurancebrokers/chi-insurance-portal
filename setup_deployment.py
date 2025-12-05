#!/usr/bin/env python3
"""
Create initial user accounts for deployment
"""
import bcrypt
import os

print("=" * 60)
print("CREATE TEST USER FOR DEPLOYMENT")
print("=" * 60)

email = input("\nEnter email for test user: ")
password = input("Enter password: ")

# Hash password
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print("\nAdd this to your Supabase SQL editor:")
print("-" * 60)
print(f"""
-- Create user for testing
INSERT INTO users (client_id, email, password_hash, is_active, created_date)
VALUES (
    1,  -- Change to actual client_id
    '{email}',
    '{hashed.decode('utf-8')}',
    1,
    NOW()
);
""")
print("-" * 60)
print("\nDone!")
