import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = 'instance/piracy_shield.db'
password_hash = generate_password_hash('admin123')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update gopika to admin
    cursor.execute("UPDATE users SET username='admin', password=?, name='System Admin' WHERE username='gopika'", (password_hash,))
    
    if cursor.rowcount == 0:
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username='admin'")
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password=?, name='System Admin' WHERE username='admin'", (password_hash,))
            print("Updated existing admin password.")
        else:
            # Create admin
            cursor.execute("INSERT INTO users (username, email, password, name, role, status) VALUES ('admin', 'admin@piracyshield.com', ?, 'System Admin', 'admin', 'active')", (password_hash,))
            print("Created new admin user.")
    else:
        print("Renamed 'gopika' to 'admin' and updated password.")
    
    conn.commit()
    conn.close()
    print("Success.")
except Exception as e:
    print(f"Error: {e}")
