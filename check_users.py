from app import app, db, User

with app.app_context():
    users = User.query.all()
    print("--- User List ---")
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | Role: {u.role}")
    print("-----------------")
