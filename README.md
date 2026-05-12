# RunSignUp OAuth2 API Client

A Python library for authenticating with the [RunSignUp API](https://runsignup.com/API) using the OAuth2 Authorization Code flow. Once a user authorizes the application, all subsequent API calls are handled automatically — including silent token refresh — with no further user interaction required.

---

## Files

| File | Purpose |
|---|---|
| `rsu_oauth2.py` | `RunSignUpOAuth2` class — handles the full OAuth2 lifecycle |
| `rsu_api.py` | `RSU` class — typed wrappers around RunSignUp REST endpoints |
| `client_config_sample.json` | A sample of how credentials and tokens are stored |
| `rsu_api_oauth2_test.py` | End-to-end usage example |

---

## Requirements

```bash
pip install requests
```

No other third-party packages are needed. The OAuth2 flow itself uses only Python's standard library (`urllib`, `http.server`, `webbrowser`).

---

## Configuration — `client_config.json`

All settings live in `client_config.json`. The file is created once during client registration and updated automatically each time tokens are issued or refreshed.

```json
{
    "client_id":        "276",
    "client_secret":    "<your client secret>",
    "redirect_uri":     "http://localhost:8080/callback",
    "scope":            "rsu_api_read rsu_api_write",
    "use_pkce":         false,
    "use_test_env":     false,
    "authorization_url": "https://runsignup.com/Profile/OAuth2/RequestGrant",
    "token_url":         "https://runsignup.com/rest/v2/auth/auth-code-redemption.json",
    "refresh_url":       "https://runsignup.com/rest/v2/auth/refresh-token.json",
    "access_token":     "",
    "refresh_token":    "",
    "token_type":       "Bearer",
    "token_expires_at": 0
}
```

### Key settings

| Setting | Description |
|---|---|
| `client_id` / `client_secret` | Issued when you register your app at [runsignup.com](https://runsignup.com/Profile/OAuth2/DeveloperGuide) |
| `redirect_uri` | Must exactly match what is registered for your client. The built-in callback server listens on this port. |
| `scope` | `rsu_api_read`, `rsu_api_write`, or both space-separated |
| `use_pkce` | Set `true` to enable PKCE (S256) — recommended for public clients |
| `use_test_env` | Set `true` to target `test.runsignup.com` instead of production |
| `access_token` | Written automatically after authorization — do not edit manually |
| `refresh_token` | Written automatically after authorization — do not edit manually |
| `token_expires_at` | Unix timestamp when the access token expires — managed automatically |

> **Security note:** `client_config.json` contains your client secret and live tokens. Add it to `.gitignore` and do not commit it to source control.

---

## Token lifetimes

| Token | Lifetime | Notes |
|---|---|---|
| Access token | 1 month (2,592,000 s) | Auto-refreshed transparently when expired |
| Refresh token | 20 years | Stored in `client_config.json`; survives access token expiry |
| Authorization code | 5 minutes | Exchanged immediately by the callback server |

---

## How it works

### First run — browser authorization required

```
┌─────────────────┐        ┌───────────────────┐        ┌──────────────────┐
│  Your script    │        │  runsignup.com    │        │  Local server    │
│                 │        │                   │        │  :8080/callback  │
│ build_auth_url()│───────>│  Login page       │        │                  │
│                 │        │  ↓ user logs in   │        │                  │
│                 │        │  ↓ clicks Authorize│       │                  │
│                 │        │  redirect 302 ────│───────>│  capture code    │
│ exchange_code() │<───────│───────────────────│────────│                  │
│                 │        │                   │        │                  │
│ save to config  │        │                   │        │                  │
└─────────────────┘        └───────────────────┘        └──────────────────┘
```

### Subsequent runs — fully automatic

```
Your script
  └─ get_auth_headers()
       └─ is_token_expired()?
            ├─ No  → return stored "Authorization: Bearer <token>"
            └─ Yes → refresh_access_token()
                       └─ POST /rest/v2/auth/refresh-token.json
                            └─ save new token → return header
```

---

## Usage

### Minimal example

```python
from rsu_oauth2 import RunSignUpOAuth2
from rsu_api import RSU

oauth = RunSignUpOAuth2()               # load config

if not oauth.refresh_token:             # first run only
    oauth.run_initial_auth_flow()       # opens browser, saves tokens

rsu = RSU(oauth=oauth)                  # create API client

print(rsu.participants(117812, 1131860))
```

### Checking what's already stored

```python
oauth = RunSignUpOAuth2()

print("Has refresh token:", bool(oauth.refresh_token))
print("Token expired:    ", oauth.is_token_expired())
print("Expires at:       ", oauth.token_expires_at)   # Unix timestamp
```

### Forcing a token refresh manually

```python
oauth = RunSignUpOAuth2()
oauth.refresh_access_token()           # exchanges refresh token for a new access token
```

### Getting auth headers for direct `requests` calls

```python
import requests
from rsu_oauth2 import RunSignUpOAuth2

oauth = RunSignUpOAuth2()
headers = oauth.get_auth_headers()     # {"Authorization": "Bearer eyJ..."}

r = requests.get(
    "https://runsignup.com/rest/race/117812",
    params={"format": "json"},
    headers=headers,
)
print(r.json())
```

### Using PKCE (enhanced security)

Set `"use_pkce": true` in `client_config.json` before running the initial auth flow. The S256 method is used automatically — no code changes needed.

---

## Available API methods (`RSU` class)

| Method | Description |
|---|---|
| `rsu.race(race_id)` | Race details |
| `rsu.participants(race_id, event_id)` | Event registrations (includes add-ons) |
| `rsu.volunteers(race_id)` | Race volunteers |
| `rsu.donations(race_id)` | Race donations |
| `rsu.members(club_id)` | Club members (default club `742`) |

All methods call the internal `rsu.get(endpoint, params)` which automatically attaches the OAuth2 `Authorization` header and refreshes the token if needed.

---

## Running the tests

### Unit tests (no network, no browser)

```bash
python -m unittest test_rsu_oauth2 -v
```

52 tests covering config loading, URL construction, PKCE math, token exchange, token refresh, expiry logic, auto-refresh, header format, config persistence, and error handling.

### Live integration tests (browser required)

```powershell
# PowerShell
$env:RSU_INTEGRATION=1; python -m unittest test_rsu_oauth2.TestLiveOAuth2 -v
```

```bash
# bash
RSU_INTEGRATION=1 python -m unittest test_rsu_oauth2.TestLiveOAuth2 -v
```

The four live tests exercise the complete real-world flow against the RunSignUp servers.

---

## Reference

- [RunSignUp OAuth2 Developer Guide](https://runsignup.com/Profile/OAuth2/DeveloperGuide)
- [RunSignUp OAuth2 OpenAPI Specification](https://runsignup.com/API/OAuth2/openapi-spec.json)
- [RunSignUp API Overview](https://runsignup.com/API/DocOverview)
