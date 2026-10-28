import sqlite3
import os

db_path = 'instance/piracy_shield.db'
if not os.path.exists(db_path):
    # Try alternate path
    db_path = 'piracy_shield.db'

print(f"Using DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        print("Users table not found!")
    else:
        # Check current users
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        print(f"Initial Users: {users}")
        
        # We need a proper hash for 'admin123'. 
        # Since I can't easily generate it here without werkzeug (which failed in the previous script due to some reason),
        # I'll use a hardcoded hash for 'admin123' generated with generate_password_hash.
        # pbkdf2:sha256:600000$z6Fq9W8G2m5X$47... (Wait, I should use a real one)
        
        # Re-running the python script but maybe the error is in app.py import?
        # Let's try to just update the username and let app.py handle the password later if it's new.
        # Actually, let's fix the python script by avoiding `from app import app`.
        
        print("Done.")
    conn.close()
except Exception as e:
    print(f"SQLite Error: {e}")
