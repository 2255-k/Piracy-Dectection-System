from app import app, db, User

with app.app_context():
    # Check if 'admin' exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("Updating existing admin user...")
        admin.set_password('admin123')
        admin.name = 'System Admin'
    else:
        # Check if 'gopika' exists to rename it
        gopika = User.query.filter_by(username='gopika').first()
        if gopika:
            print("Renaming 'gopika' to 'admin' and updating password...")
            gopika.username = 'admin'
            gopika.name = 'System Admin'
            gopika.set_password('admin123')
        else:
            print("Creating new 'admin' user...")
            admin = User(username='admin', email='admin@piracyshield.com', name='System Admin', role='admin', status='active')
            admin.set_password('admin123')
            db.session.add(admin)
    
    db.session.commit()
    print("Admin password changed successfully to 'admin123' for user 'admin'.")
