"""Angel authentication using the same environment-variable names as RVOL Scanner.

Never print credentials, TOTP values, tokens, or full API error responses.
"""
import os

def connect_from_environment():
    from SmartApi import SmartConnect
    import pyotp
    names = ("ANGEL_API_KEY", "ANGEL_CLIENT_CODE", "ANGEL_PIN", "ANGEL_TOTP_SECRET")
    missing = [name for name in names if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError("Missing required environment configuration: " + ", ".join(missing))
    api_key, client_code, pin, secret = (os.environ[name].strip() for name in names)
    smart = SmartConnect(api_key)
    try:
        response = smart.generateSession(client_code, pin, pyotp.TOTP(secret.replace(" ", "")).now())
    except Exception as exc:
        raise RuntimeError("Angel authentication request failed; check configuration and network") from None
    if not isinstance(response, dict) or response.get("status") is False or not response.get("data"):
        raise RuntimeError("Angel authentication was rejected; verify credentials and API permissions")
    return smart
