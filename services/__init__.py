import re
import os
import json
import asyncio
import nest_asyncio
from telethon import TelegramClient, types
from telethon.tl.functions.messages import ReportRequest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Initialize nest_asyncio to allow nested event loops (important for Flask/Telethon)
nest_asyncio.apply()

# --- Detection Logic ---
class PiracyDetector:
    def __init__(self):
        self.model = self._train_model()
        self.piracy_keywords = [
            "cam", "camrip", "hdrip", "webrip", "dvdrip", "bdrip",
            "x264", "x265", "hevc", "1080p", "720p", "480p", "4k",
            "leaked", "download", "link", "torrent", "magnet",
            "full movie", "watch online", "free", "bluray", "web-dl",
            "telegram", "channel", "join", "premium", "vip",
            # Multi-language/Regional Keywords (Feature #3)
            "dubbed", "hindi", "tamil", "telugu", "malayalam", "kannada",
            "isaimini", "tamilrockers", "tamilyogi", "filmyzilla", "pagalworld",
            "movierulz", "todaypk", "9xmovies", "khatrimaza"
        ]
        self.video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv']
        self.archive_extensions = ['.torrent', '.zip', '.rar', '.7z']

    def _train_model(self):
        # ... (rest of the code remains the same internally)
        data = [
            ("Download Avengers Endgame full movie HD 1080p", 1),
            ("Watch Spider-Man No Way Home online free", 1),
            ("Leaked version of Dune 2021 CAMRip", 1),
            ("CAMRip available now download link", 1),
            ("Free download link Oppenheimer 2023", 1),
            ("Avengers.Endgame.2019.1080p.BluRay.x264", 1),
            ("Dune 2021 full movie telegram channel", 1),
            ("Join premium channel for latest movies", 1),
            ("Spider-Man 2023 WEB-DL 720p mkv file", 1),
            ("Latest movie releases free download", 1),
            ("Barbie 2023 HDRip 480p download", 1),
            ("Movie torrent magnet link available", 1),
            ("Full HD movie collection free", 1),
            ("Watch before removed premium content", 1),
            ("Latest Hollywood movies leaked", 1),
            ("Tamil movie download link here", 1),
            ("Hindi dubbed version leaked", 1),
            ("Watch Leo tamil movie online", 1),
            ("Here is the project report", 0),
            ("Meeting minutes attached", 0),
            ("Family vacation photos", 0),
            ("Official trailer released", 0),
            ("Join our study group", 0),
            ("Movie review and discussion", 0),
            ("Book your tickets now", 0),
            ("Box office collection update", 0),
            ("Actor interview video", 0),
            ("Behind the scenes documentary", 0),
            ("Official announcement from studio", 0),
            ("Cinema hall timings", 0),
            ("Movie news and updates", 0),
            ("Legitimate streaming platform", 0),
            ("Working on my presentation", 0)
        ]
        X, y = zip(*data)
        model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB())
        model.fit(X, y)
        return model

    def _check_movie_context(self, text, movie_name):
        text_lower = text.lower()
        movie_lower = movie_name.lower()
        movie_pattern = r'\b' + re.escape(movie_lower) + r'\b'
        
        if not re.search(movie_pattern, text_lower):
            return False, 0
        
        context_window = 50
        matches = list(re.finditer(movie_pattern, text_lower))
        
        for match in matches:
            start = max(0, match.start() - context_window)
            end = min(len(text_lower), match.end() + context_window)
            context = text_lower[start:end]
            piracy_indicators = ['download', 'free', 'link', 'watch', 'leaked', 'rip', '1080p', '720p', 'torrent', 'magnet', 'print']
            if any(indicator in context for indicator in piracy_indicators):
                return True, 50
        return True, 30

    def _parse_file_size(self, size):
        if isinstance(size, (int, float)): return size
        if not isinstance(size, str): return 0
        size = size.upper().strip()
        if not size: return 0
        multiplier = 1
        if 'GB' in size: multiplier = 1024 * 1024 * 1024; size = size.replace('GB', '')
        elif 'MB' in size: multiplier = 1024 * 1024; size = size.replace('MB', '')
        elif 'KB' in size: multiplier = 1024; size = size.replace('KB', '')
        elif 'B' in size: size = size.replace('B', '')
        try: return float(size.strip()) * multiplier
        except ValueError: return 0

    def check_rules(self, message, movie_name, custom_rules=None):
        text = (message.get('text', '') + " " + message.get('caption', '') + " " + message.get('file_name', '')).lower()
        flags, score = [], 0
        has_movie, movie_score = self._check_movie_context(text, movie_name)
        if has_movie:
            score += movie_score
            flags.append(f"Movie '{movie_name}' context match" if movie_score >= 50 else f"Movie '{movie_name}' mentioned")
        
        # 1. Built-in Keywords (Always check these)
        found_builtin = [kw for kw in self.piracy_keywords if kw in text]
        if found_builtin:
            score += 10 * len(found_builtin)
            flags.append(f"Keywords: {', '.join(found_builtin[:3])}")

        # 2. Dynamic Rule Engine Support (Feature #12)
        if custom_rules and isinstance(custom_rules, dict):
            for pattern, weight in custom_rules.items():
                if pattern.lower() in text:
                    score += weight
                    flags.append(f"Custom Rule: {pattern}")

        file_name = message.get('file_name', '').lower()
        if any(file_name.endswith(ext) for ext in self.video_extensions):
            score += 25 if has_movie else 10
            flags.append("Video file with movie name" if has_movie else "Video file detected")
        
        if any(file_name.endswith(ext) for ext in self.archive_extensions):
            score += 30 if has_movie else 15
            flags.append("Torrent/Archive with movie name" if has_movie else "Suspicious archive")
        
        file_size = message.get('file_size_bytes') or self._parse_file_size(message.get('file_size', 0))
        if file_size > 500 * 1024 * 1024 and has_movie and any(file_name.endswith(ext) for ext in self.video_extensions):
            score += 15
            flags.append("Large video file")

        return score, flags

    def predict_ml(self, message):
        text = (message.get('text', '') + " " + message.get('caption', '')).lower()
        if not text.strip(): return 0
        try: return self.model.predict_proba([text])[0][1] * 100
        except: return 0

    def analyze(self, messages, movie_name, custom_rules=None):
        results = []
        for msg in messages:
            rule_score, flags = self.check_rules(msg, movie_name, custom_rules)
            ml_score = self.predict_ml(msg)
            final_score = min((rule_score * 0.6) + (ml_score * 0.4), 100)
            if final_score > 25 and flags:
                results.append({
                    "id": msg['id'], "chat_id": msg.get('chat_id'), "chat_username": msg.get('chat_username'),
                    "group_name": msg.get('group_name', 'Unknown Group'), "text": msg.get('text', ''),
                    "file_name": msg.get('file_name', ''), "score": round(final_score, 2),
                    "reasons": flags, "ml_confidence": round(ml_score, 2), "link": msg.get('link', '#')
                })
        return sorted(results, key=lambda x: x['score'], reverse=True)

# --- Telegram Service ---
SESSION_NAME = 'telegram_session'

def get_credentials():
    try:
        from models import TelegramAuth
        auth = TelegramAuth.query.first()
        if auth: return auth.api_id, auth.api_hash
    except: pass
    try:
        with open("telegram_creds.txt", "r") as f:
            lines = f.readlines()
            if len(lines) >= 2: return lines[0].strip(), lines[1].strip()
    except: pass
    return None, None

async def search_telegram(query, limit=50):
    if not os.path.exists(f"{SESSION_NAME}.session"): return []
    api_id, api_hash = get_credentials()
    if not api_id or not api_hash: return []
    
    try:
        # Added robust connection parameters for Live Mode search
        client = TelegramClient(SESSION_NAME, api_id, api_hash,
                                connection_retries=3,
                                request_retries=2,
                                timeout=15)
        async with client:
            results = []
            async for message in client.iter_messages(None, search=query, limit=limit):
                chat_title = getattr(message.chat, 'title', 'Private Chat') if message.chat else "Unknown"
                file_name = message.file.name or "Unknown File" if message.file else ""
                file_size = f"{message.file.size / 1024 / 1024:.2f} MB" if message.file else ""
                chat_username = getattr(message.chat, 'username', None)
                results.append({
                    "id": message.id, "chat_id": message.chat_id, "chat_username": chat_username,
                    "group_name": chat_title, "text": message.text or "", "caption": message.text or "",
                    "file_name": file_name, "file_size": file_size, "file_size_bytes": message.file.size if message.file else 0,
                    "link": f"https://t.me/{chat_username}/{message.id}" if chat_username else "#"
                })
            return results
    except Exception as e:
        print(f"SEARCH ERROR: {str(e)}")
        return []

async def report_message(chat_id, message_id, chat_username=None):
    api_id, api_hash = get_credentials()
    if not api_id or not api_hash or not os.path.exists(f"{SESSION_NAME}.session"):
        return False, "Session/Credentials not found"
    
    # Check if this is a simulated ID (from app.py simulation)
    # Simulator uses randint(10**5, 10**6) for msg and 10**6, 10**7 for chat
    try:
        c_id = int(chat_id)
        if 10**5 <= c_id <= 10**7:
            # Short delay to mimic API call
            await asyncio.sleep(0.5)
            return True, "Simulated report successful (Simulator Mode)"
    except: pass

    try:
        # Added timeout and retries for better robustness
        client = TelegramClient(SESSION_NAME, api_id, api_hash, 
                                connection_retries=2, 
                                request_retries=1, 
                                timeout=10)
        async with client:
            entity = await client.get_entity(chat_username or int(chat_id))
            # Use proper Telethon ReportReason for live mode
            await client(ReportRequest(peer=entity, id=[int(message_id)], reason=types.InputReportReasonCopyright(), message="Piracy Violation"))
            return True, "Reported to Telegram"
    except Exception as e: 
        return False, f"Connection Failed: {str(e)}"

def run_search(query):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(search_telegram(query))

def run_report(chat_id, message_id, chat_username=None):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(report_message(chat_id, message_id, chat_username))
