"""
One-time Garmin authentication setup.
Run this once to save a session token:

    python3 garmin_setup.py

You will be prompted for a 2FA code sent to your email or authenticator app.
After this runs successfully, sync.py will authenticate silently using the
saved token.
"""

import os
from garminconnect import Garmin
from dotenv import load_dotenv

load_dotenv()

TOKEN_PATH = os.path.join(os.path.dirname(__file__), "data", ".garth")

email    = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

print(f"Logging in to Garmin Connect as {email}...")
print("You will be asked for a 2FA code — check your email or authenticator app.\n")

api = Garmin(email, password, prompt_mfa=lambda: input("Enter 2FA code: "))
api.login()

os.makedirs(TOKEN_PATH, exist_ok=True)
api.client.dump(TOKEN_PATH)
print(f"\nSession saved to {TOKEN_PATH}")
print("You can now run python3 sync.py without needing to re-authenticate.")
