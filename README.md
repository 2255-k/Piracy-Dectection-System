# Telegram Piracy Detection System

A professional, metadata-driven platform designed to monitor and identify potential copyright infringement within public Telegram channels using Rule-Based Logic and Machine Learning.

## 1. Project Structure (Simplified)
- `app.py`: Main entry point containing all routes and configuration.
- `models.py`: Database schema and models.
- `services.py`: Core logic for Piracy Detection and Telegram API integration.
- `utils.py`: Security and authentication helpers.
- `templates/`: HTML user interfaces.
- `static/`: CSS and visual assets.

## 2. Setup Instructions for Clients

### Step 1: Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Telegram API
To use real scanning, you must get your own API credentials:
1. Go to [https://my.telegram.org](https://my.telegram.org) and log in.
2. Click **API development tools** and create a new application.
3. Run the setup script to link your Telegram account:
   ```bash
   python setup_telegram.py
   ```
4. Enter your `API ID` and `API Hash` when prompted, then follow the login steps.

### Step 3: Run the Application
Start the server:
```bash
python app.py
```
Access the system at `http://127.0.0.1:5000`.

## 3. Master Admin Login
Use the following master credentials to access the Admin Panel:
- **Username**: `gopika`
- **Password**: `gopika@2005`

## 4. Key Features
- **Dynamic Simulator**: Scanner works even without API keys by using a simulator mode.
- **AI Core**: Uses TF-IDF and Naive Bayes to calculate "Suspicion Scores".
- **Rule Engine**: Admins can customize detection keywords and weights via the Control Panel.
- **Multi-Language Detection**: Supports regional content names and pirate keywords in multiple languages (Hindi, Tamil, etc.).
- **Evidence Export**: Generate downloadable CSV reports for legal and compliance teams.
- **Zero-Storage Media**: Only metadata is analyzed; no copyright-infringing files are ever downloaded or stored.
- **Reporting System**: Integrated feature to report piracy directly to Telegram's legal team.

## 5. Security & Privacy
- **Password Hashing**: BCrypt/PBKDF2 encryption for all users.
- **Rate Limiting**: Protects scanning endpoints from abuse.
- **RBAC**: Strict separation between Standard Users and System Administrators.

---
*Disclaimer: This tool is intended for monitoring and identification. Resulting legal actions are the responsibility of the system administrator.*
