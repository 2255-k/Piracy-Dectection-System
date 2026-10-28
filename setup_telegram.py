from telethon import TelegramClient
import asyncio
import os

# You must get these from https://my.telegram.org
# I will use placeholders. The user must replace them or enter them when prompted.
API_ID = 'YOUR_API_ID' 
API_HASH = 'YOUR_API_HASH'
SESSION_NAME = 'telegram_session'

async def setup():
    print("To use real Telegram, you need an API ID and API Hash from https://my.telegram.org")
    print("1. Log in with your phone number.")
    print("2. Click 'API development tools'.")
    print("3. Create a new app (any name works).")
    print("4. Copy 'App api_id' (it's a number) and 'App api_hash' (it's a long string).")
    print("-" * 50)

    while True:
        api_id_str = input("Enter your API ID: ").strip()
        if api_id_str.isdigit():
            api_id = int(api_id_str)
            break
        print("Error: API ID must be a number. Please try again.")

    api_hash = input("Enter your API Hash: ").strip()
    
    print("-" * 50)
    print(f"Connecting with API ID: {api_id}")
    
    try:
        client = TelegramClient(SESSION_NAME, api_id, api_hash)
        await client.start()
    except Exception as e:
        print(f"\nError connecting to Telegram: {e}")
        print("Please check your API ID and Hash and try again.")
        return

    # Save creds for the app to use
    with open("telegram_creds.txt", "w") as f:
        f.write(f"{api_id}\n{api_hash}")
    
    print("\nSuccessfully logged in!")
    print(f"Session file '{SESSION_NAME}.session' created.")
    print("You can now run 'python app.py' to use the web interface.")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(setup())
