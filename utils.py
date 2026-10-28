from functools import wraps
from flask import session, redirect, url_for, flash, request
import time

# Simple in-memory rate limit storage
RATE_LIMIT_STORAGE = {}

def rate_limit(limit=5, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            uid = session.get('user_id', request.remote_addr)
            now = time.time()
            
            if uid not in RATE_LIMIT_STORAGE:
                RATE_LIMIT_STORAGE[uid] = []
                
            RATE_LIMIT_STORAGE[uid] = [t for t in RATE_LIMIT_STORAGE[uid] if now - t < window]
            
            if len(RATE_LIMIT_STORAGE[uid]) >= limit:
                flash(f"Rate limit exceeded. Please wait {window} seconds.", "warning")
                return redirect(request.referrer or url_for('index'))
                
            RATE_LIMIT_STORAGE[uid].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
