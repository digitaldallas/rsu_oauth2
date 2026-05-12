"""
Demonstrates how to use RunSignUpOAuth2 + RSU to call the RunSignUp API.

First run  — no tokens stored yet:
    The browser opens for the user to log in and authorize the app.
    Tokens are saved to client_config.json automatically.

Subsequent runs — tokens already stored:
    The access token is reused (or silently refreshed if expired).
    No browser interaction is needed.
"""

from rsu_oauth2 import RunSignUpOAuth2
from rsu_api import RSU

# ── Step 1: create the OAuth2 handler ────────────────────────────────────────
# Reads client_id, client_secret, and any previously stored tokens from
# client_config.json in the current directory.
oauth = RunSignUpOAuth2(config_path="client_config.json")

# ── Step 2: ensure we have a valid token ─────────────────────────────────────
if not oauth.refresh_token:
    # First run: open the browser and complete the authorization code flow.
    # The user logs in on runsignup.com and clicks "Authorize".
    # The access + refresh tokens are saved to client_config.json when done.
    print("No stored token found — starting browser authorization flow...")
    oauth.run_initial_auth_flow(open_browser=True)
else:
    # Subsequent runs: get_auth_headers() auto-refreshes the access token
    # using the stored refresh token if it has expired. No browser needed.
    print("Stored token found — using existing credentials (auto-refresh if expired).")

# ── Step 3: create the API client ────────────────────────────────────────────
# Pass in the oauth instance so every request automatically carries
# the correct "Authorization: Bearer <token>" header.
rsu = RSU(oauth=oauth)

# ── Step 4: make API calls ────────────────────────────────────────────────────
event = 1131860
race  = 117812

print(f"\nFetching participants for race={race}, event={event} ...")
regs = rsu.participants(race, event)
print(regs)
