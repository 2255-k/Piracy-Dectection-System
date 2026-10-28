from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app, jsonify, Response
import os
import json
import random
import csv
import io
from datetime import datetime
from models import db, User, SearchQuery, MessageMetadata, AnalysisResult, UserReport, TelegramAuth, PiracyRule
from utils import login_required, roles_required, rate_limit
from services import PiracyDetector, run_search, run_report

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///piracy_shield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'piracy-shield-secret'

db.init_app(app)
detector = PiracyDetector()

# --- Sample Data for Simulator ---
SAMPLE_MESSAGES = [
    {"id": 1, "group_name": "Family Chat", "text": "Check out this movie!", "file_name": "vacation.zip", "file_size": "15MB"},
    {"id": 2, "group_name": "Movie Leaks 2024", "text": "Download Avengers Endgame full movie HD", "file_name": "Avengers.Endgame.mkv", "file_size": "2.5GB"},
    {"id": 4, "group_name": "Cinema Updates", "text": "Spider-Man No Way Home leaked download", "file_name": "SpiderMan_NWH.mp4", "file_size": "800MB"},
    {"id": 6, "group_name": "Hollywood Blockbusters", "text": "Download latest movies 2024", "file_name": "Dune.Part.Two.avi", "file_size": "1.4GB"},
    {"id": 8, "group_name": "Tamil Rockers Official", "text": "Watch Leo full movie online free", "file_name": "Leo_2023.mkv", "file_size": "3GB"}
]

# --- Database Initialization ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@piracyshield.com', name='System Admin', role='admin', status='active')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Initialize some default rules (Feature #12)
    if not PiracyRule.query.first():
        defaults = [
            ('camrip', 50, 'keyword'), ('hdrip', 30, 'keyword'), ('leaked', 40, 'keyword'),
            ('tamilrockers', 60, 'keyword'), ('isaimini', 60, 'keyword'), ('dubbed', 20, 'language'),
            ('hindi', 10, 'language'), ('tamil', 10, 'language'), ('telugu', 10, 'language')
        ]
        for p, w, c in defaults:
            db.session.add(PiracyRule(pattern=p, weight=w, category=c))
        db.session.commit()

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' not in session: 
        return render_template('landing.html')
    return redirect(url_for('admin_dashboard' if session.get('role') == 'admin' else 'user_dashboard'))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            if user.status != 'active':
                flash("Account blocked.", "danger")
            else:
                session.update({'user_id': user.id, 'username': user.username, 'role': user.role, 'name': user.name})
                return redirect(url_for('index'))
        else: flash("Invalid credentials.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e = request.form.get('username'), request.form.get('email')
        if User.query.filter((User.username == u) | (User.email == e)).first():
            flash("Username/Email exists.", "danger")
        else:
            user = User(username=u, email=e, name=request.form.get('name'))
            user.set_password(request.form.get('password'))
            db.session.add(user); db.session.commit()
            flash("Registered successfully!", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear(); flash("Logged out.", "info")
    return redirect(url_for('index'))

# --- User Routes ---
@app.route('/user/dashboard')
@roles_required('user', 'admin')
def user_dashboard():
    telegram_ready = os.path.exists('telegram_session.session')
    return render_template('user/dashboard.html', user=session, telegram_ready=telegram_ready)

@app.route('/scan', methods=['POST'])
@login_required
def scan():
    from services.metadata import metadata_service
    movie_name = request.form.get('movie_name')
    if not movie_name:
        return render_template('user/dashboard.html', error="Movie name is required", user=session)
    
    # Track the search
    search_entry = SearchQuery(query=movie_name, user_id=session.get('user_id'))
    db.session.add(search_entry)
    db.session.commit()
    
    detector = PiracyDetector()
    
    messages = []
    if os.path.exists('telegram_session.session'): # Check for telegram session file
        try: 
            messages = run_search(movie_name)
        except Exception as e:
            flash(f"Telegram Search Error: {str(e)}. Switched to Simulator.", "warning")
            messages = []
    
    if not messages:
        # Define simulation parameters
        known_movies = ["Avengers", "Spider-Man", "Spiderman", "Leo", "Dune", "Oppenheimer", "Batman", "Joker", "Animal", "Inception", "Titanic", "Avatar"]
        piracy_generic = ["download", "leaked", "free", "mkv", "mp4", "torrent", "mirror", "watch online", "webrip", "hdrip"]
        
        query_lower = movie_name.lower().strip()
        
        # Advanced gibberish check
        vowels = "aeiou"
        vowel_count = sum(1 for char in query_lower if char in vowels)
        vowel_ratio = vowel_count / len(query_lower) if len(query_lower) > 0 else 0
        unique_chars = len(set(query_lower))
        char_variety = unique_chars / len(query_lower) if len(query_lower) > 0 else 0
        
        # Heuristics for gibberish (random keyboard hitting)
        is_gibberish = False
        if len(query_lower) >= 5:
            # 1. Vowel density (very low or very high is usually junk)
            if vowel_ratio < 0.15 or vowel_ratio > 0.80: is_gibberish = True 
            
            # 2. Character variety (too many unique chars in a row)
            if char_variety > 0.80 and len(query_lower) > 8: is_gibberish = True
            
            # 3. Repeated character sequences
            if any(query_lower[i:i+3] == query_lower[i]*3 for i in range(len(query_lower)-2)): is_gibberish = True 
            
            # 4. Consonant clusters (e.g., "sdfgh")
            consonants = "bcdfghjklmnpqrstvwxyz"
            consonant_count = 0
            max_consonant_cluster = 0
            for char in query_lower:
                if char in consonants:
                    consonant_count += 1
                    max_consonant_cluster = max(max_consonant_cluster, consonant_count)
                else:
                    consonant_count = 0
            if max_consonant_cluster > 4: is_gibberish = True

            # 5. Frequency analysis (one char taking up too much of the string)
            from collections import Counter
            if query_lower:
                most_common_count = Counter(query_lower).most_common(1)[0][1]
                if most_common_count / len(query_lower) > 0.5 and len(query_lower) > 6: is_gibberish = True

        is_relevant = False
        # Only show simulation if it's NOT gibberish and looks like a title
        if not is_gibberish and len(query_lower) >= 3:
            # Check if it matches a known movie or contains common title words
            title_indicators = ["the", "man", "movie", "love", "night", "star", "war", "part", "ii", "2", "3"]
            is_known = any(km.lower() in query_lower or query_lower in km.lower() for km in known_movies)
            has_indicator = any(ti in query_lower.split() for ti in title_indicators)
            
            # Allow regional titles (usually 4-8 chars with decent vowel mix)
            is_regional_plausible = 4 <= len(query_lower) <= 12 and 0.25 <= vowel_ratio <= 0.60
            
            if is_known or has_indicator or is_regional_plausible:
                is_relevant = True

        if is_relevant:
            # Show results for relevant search in simulation mode
            for msg in SAMPLE_MESSAGES:
                m = msg.copy()
                placeholders = [
                    ("Avengers Endgame", ["Avengers.Endgame", "Avengers"]),
                    ("Spider-Man No Way Home", ["Spider-Man No Way Home", "SpiderMan_NWH", "Spider-Man"]),
                    ("Dune Part Two", ["Dune.Part.Two", "Dune"]),
                    ("Leo", ["Leo_2023", "Leo"])
                ]
                for placeholder_text, file_tokens in placeholders:
                    # Check if the placeholder (or a variant) is in the text
                    if placeholder_text.lower() in m['text'].lower() or any(t.lower() in m['text'].lower() for t in file_tokens):
                        # Replace in text
                        import re
                        m['text'] = re.sub(re.escape(placeholder_text), movie_name, m['text'], flags=re.IGNORECASE)
                        # Also replace any of the tokens if they appear in text
                        for token in file_tokens:
                            m['text'] = re.sub(re.escape(token.replace('.', ' ')), movie_name, m['text'], flags=re.IGNORECASE)
                        
                        # Replace in file_name (more aggressively for simulation)
                        movie_dot = movie_name.replace(" ", ".")
                        for token in file_tokens:
                            if token.lower() in m['file_name'].lower():
                                # Use regex for case-insensitive replacement in filename
                                m['file_name'] = re.sub(re.escape(token), movie_dot, m['file_name'], flags=re.IGNORECASE)
                                break
                
                m['id'], m['chat_id'] = random.randint(10**5, 10**6), random.randint(10**6, 10**7)
                messages.append(m)
    
    # Apply Dynamic Rules (Feature #12)
    custom_rules = {r.pattern: r.weight for r in PiracyRule.query.filter_by(is_active=True).all()}
    results = detector.analyze(messages, movie_name, custom_rules=custom_rules)

    for res in results:
        meta = MessageMetadata.query.filter_by(telegram_id=res['id']).first()
        if not meta:
            meta = MessageMetadata(telegram_id=res['id'], chat_id=res['chat_id'], chat_username=res.get('chat_username'), 
                                   group_name=res.get('group_name'), text=res.get('text'), file_name=res.get('file_name'), link=res.get('link'))
            db.session.add(meta); db.session.commit()
        db.session.add(AnalysisResult(message_id=meta.id, search_query_id=search_entry.id, rule_score=res['score'], 
                                     ml_score=res['ml_confidence'], final_score=res['score'], 
                                     reasons=json.dumps(res['reasons']), is_piracy=res['score'] > 40))
    db.session.commit()
    
    # Fetch movie details and legal platforms
    movie_details = metadata_service.get_movie_details(movie_name)
    movie_id = movie_details.get("id") if movie_details else None
    legal_options = metadata_service.get_legal_platforms(movie_id, movie_name) if movie_id else metadata_service._get_simulated_platforms(movie_name)
    
    return render_template('results.html', movie_name=movie_name, results=results, movie_details=movie_details, legal_options=legal_options, user=session)

@app.route('/user/report', methods=['POST'])
@roles_required('user', 'admin')
def report():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        message_id = data.get('message_id')
        msg = MessageMetadata.query.filter_by(telegram_id=message_id).first()
        if not msg:
            return jsonify({"status": "error", "message": f"Message {message_id} not found in database"}), 404
        
        success, status = run_report(data['chat_id'], message_id, data.get('chat_username'))
        
        report_entry = UserReport(user_id=session['user_id'], message_id=msg.id, telegram_api_status=status)
        db.session.add(report_entry)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Feedback submitted successfully", 
            "telegram_status": status
        })
    except Exception as e:
        print(f"REPORT ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Admin Routes ---
@app.route('/admin/dashboard')
@roles_required('admin')
def admin_dashboard():
    from sqlalchemy import func
    from datetime import timedelta
    
    # Basic Stats
    stats = {
        'users_count': User.query.count(),
        'messages_count': MessageMetadata.query.count(),
        'reports_count': UserReport.query.count()
    }
    
    # 1. Scan Trends (Last 7 Days)
    today = datetime.utcnow().date()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    scan_counts = []
    for date_str in dates:
        count = db.session.query(SearchQuery).filter(func.date(SearchQuery.timestamp) == date_str).count()
        scan_counts.append(count)
    
    trends_data = {'labels': dates, 'values': scan_counts}
    
    # 2. Detection Distribution (Piracy vs Clean)
    piracy_count = AnalysisResult.query.filter_by(is_piracy=True).count()
    clean_count = AnalysisResult.query.filter_by(is_piracy=False).count()
    distribution_data = {'labels': ['Piracy', 'Clean'], 'values': [piracy_count, clean_count]}
    
    # 3. Top Keywords
    top_keywords = db.session.query(SearchQuery.query, func.count(SearchQuery.id).label('count'))\
        .group_by(SearchQuery.query).order_by(func.count(SearchQuery.id).desc()).limit(5).all()
    keywords_data = {'labels': [k[0] for k in top_keywords], 'values': [k[1] for k in top_keywords]}
    
    analytics = {
        'trends': trends_data,
        'distribution': distribution_data,
        'keywords': keywords_data
    }
    
    return render_template('admin/dashboard.html', user=session, stats=stats, analytics=analytics)

@app.route('/admin/users')
@roles_required('admin')
def list_users():
    return render_template('admin/users.html', users=User.query.all(), user=session)

@app.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
@roles_required('admin')
def toggle_user(user_id):
    user = User.query.get(user_id)
    if user and user.id != session['user_id']:
        user.status = 'blocked' if user.status == 'active' else 'active'
        db.session.commit()
    return redirect(url_for('list_users'))

@app.route('/admin/metadata')
@roles_required('admin')
def view_metadata():
    return render_template('admin/metadata.html', messages=MessageMetadata.query.order_by(MessageMetadata.timestamp.desc()).all(), user=session)

@app.route('/admin/reports')
@roles_required('admin')
def manage_reports():
    return render_template('admin/reports.html', reports=UserReport.query.order_by(UserReport.timestamp.desc()).all(), user=session)

@app.route('/admin/rules', methods=['GET', 'POST'])
@roles_required('admin')
def manage_rules():
    if request.method == 'POST':
        pattern = request.form.get('pattern')
        weight = int(request.form.get('weight', 10))
        category = request.form.get('category', 'keyword')
        if pattern:
            db.session.add(PiracyRule(pattern=pattern, weight=weight, category=category))
            db.session.commit()
            flash(f"Rule '{pattern}' added.", "success")
    rules = PiracyRule.query.all()
    return render_template('admin/rules.html', rules=rules, user=session)

@app.route('/admin/delete-rule/<int:rule_id>', methods=['POST'])
@roles_required('admin')
def delete_rule(rule_id):
    rule = PiracyRule.query.get(rule_id)
    if rule:
        db.session.delete(rule)
        db.session.commit()
        flash("Rule deleted.", "info")
    return redirect(url_for('manage_rules'))

@app.route('/admin/export/csv')
@roles_required('admin')
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Channel/Group', 'Text Snippet', 'File Name', 'Score', 'Status', 'Timestamp'])
    
    messages = MessageMetadata.query.all()
    for msg in messages:
        analysis = AnalysisResult.query.filter_by(message_id=msg.id).first()
        score = analysis.final_score if analysis else 0
        status = "Piracy" if (analysis and analysis.is_piracy) else "Clean"
        writer.writerow([msg.telegram_id, msg.group_name, msg.text[:50], msg.file_name, score, status, msg.timestamp])
    
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=piracy_report.csv"})

@app.route('/admin/telegram-auth', methods=['GET', 'POST'])
@roles_required('admin')
def telegram_auth():
    auth = TelegramAuth.query.first()
    if request.method == 'POST':
        if not auth:
            auth = TelegramAuth(api_id=request.form.get('api_id'), api_hash=request.form.get('api_hash'))
            db.session.add(auth)
        else:
            auth.api_id, auth.api_hash = request.form.get('api_id'), request.form.get('api_hash')
        with open("telegram_creds.txt", "w") as f: f.write(f"{auth.api_id}\n{auth.api_hash}")
        db.session.commit(); flash("Credentials updated.", "success")
    return render_template('admin/telegram_auth.html', auth=auth, user=session)

@app.route('/admin/profile', methods=['GET', 'POST'])
@roles_required('admin')
def profile():
    admin = User.query.get(session['user_id'])
    if request.method == 'POST':
        admin.username, admin.email, admin.name = request.form.get('username'), request.form.get('email'), request.form.get('name')
        if request.form.get('password'): admin.set_password(request.form.get('password'))
        db.session.commit(); flash("Profile updated.", "success")
        session.update({'username': admin.username, 'name': admin.name})
    return render_template('admin/profile.html', admin=admin, user=session)

if __name__ == '__main__':
    app.run(debug=True)
