"""Angel SmartAPI authentication with non-sensitive failure categories."""
import os

class AngelAuthenticationError(RuntimeError):
    def __init__(self, category: str):
        self.category = category
        super().__init__(category)

def connect_from_environment():
    try:
        from SmartApi import SmartConnect
        import pyotp
    except ModuleNotFoundError as exc:
        # Only disclose a known module name; never leak paths or exception text.
        known = {
            "SmartApi", "pyotp", "logzero", "websocket", "Crypto",
            "jwt", "pycryptodome", "six", "requests", "dateutil",
            "numpy", "pandas", "websocket_client", "smartapi"
        }
        missing = (exc.name or "").split(".")[0]
        label = missing if missing in known else "OTHER"
        raise AngelAuthenticationError("MISSING_MODULE_" + label) from None
    except ImportError:
        raise AngelAuthenticationError("SDK_IMPORT_ERROR") from None
    names = ("ANGEL_API_KEY", "ANGEL_CLIENT_CODE", "ANGEL_PIN", "ANGEL_TOTP_SECRET")
    if any(not os.getenv(name, "").strip() for name in names):
        raise AngelAuthenticationError("MISSING_CONFIGURATION")
    api_key, client_code, pin, secret = (os.environ[name].strip() for name in names)
    try:
        totp = pyotp.TOTP(secret.replace(" ", "")).now()
    except Exception:
        raise AngelAuthenticationError("TOTP_GENERATION_ERROR") from None
    try:
        smart = SmartConnect(api_key)
        response = smart.generateSession(client_code, pin, totp)
    except Exception:
        raise AngelAuthenticationError("NETWORK_OR_SDK_ERROR") from None
    if not isinstance(response, dict):
        raise AngelAuthenticationError("UNEXPECTED_API_RESPONSE")
    if response.get("status") is False or not response.get("data"):
        # Only disclose the provider's short error code, never its message,
        # tokens, headers, user data, or full response.
        code = str(response.get("errorcode") or "").strip()
        safe_codes = {"AG8001", "AG8002", "AG8003", "AG8004", "AG8005"}
        category = "API_REJECTED_" + code if code in safe_codes else "API_REJECTED"
        raise AngelAuthenticationError(category)
    return smart
