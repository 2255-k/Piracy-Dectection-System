import os
from app import app, db, User

def update_admin():
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        try:
            # Check for existing users
            users = User.query.all()
            print(f"Found {len(users)} users.")
            for u in users:
                print(f"User: {u.username} (ID: {u.id}, Role: {u.role})")
            
            # Target action
            target_username = 'admin'
            old_username = 'gopika'
            
            admin_user = User.query.filter_by(username=target_username).first()
            if not admin_user:
                gopika = User.query.filter_by(username=old_username).first()
                if gopika:
                    print(f"Renaming '{old_username}' to '{target_username}'...")
                    gopika.username = target_username
                    gopika.name = 'System Admin'
                    gopika.set_password('admin123')
                    admin_user = gopika
                else:
                    print(f"Creating new '{target_username}' user...")
                    admin_user = User(username=target_username, email='admin@piracyshield.com', name='System Admin', role='admin', status='active')
                    admin_user.set_password('admin123')
                    db.session.add(admin_user)
            else:
                print(f"User '{target_username}' already exists. Updating password...")
                admin_user.set_password('admin123')
                admin_user.name = 'System Admin'
            
            db.session.commit()
            print("Successfully updated admin credentials.")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    update_admin()
