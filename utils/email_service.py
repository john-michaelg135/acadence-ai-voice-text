import logging
import re
import secrets
import smtplib
import threading
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys
from dotenv import load_dotenv

# Resolve .env correctly for both script mode and PyInstaller exe
if getattr(sys, 'frozen', False):
    _env_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), '.env')
else:
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path)

APP_NAME = "Acadence AI"
# We're loading these specific variables since they exist in the user's .env screenshot natively
EMAIL_SENDER = os.getenv("SMTP_EMAIL", "")
EMAIL_APP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_DISPLAY_NAME = "Acadence Security"

OTP_TTL_SECONDS  = int(os.getenv('OTP_TTL_SECONDS', '300'))
OTP_LENGTH       = 6
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '5'))
RESEND_COOLDOWN  = int(os.getenv('RESEND_COOLDOWN', '60'))

_store = {}
_resend_timestamps = {}
_lock   = threading.Lock()
_logger = logging.getLogger(__name__)

_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def _credentials():
    sender = EMAIL_SENDER.strip()
    password = EMAIL_APP_PASSWORD.replace(" ", "").strip()
    return sender, password

def _domain_exists(domain: str) -> bool:
    """Lightweight DNS check — verifies the email domain is real and resolvable."""
    import socket
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False
    except Exception:
        return True  # Fail open on unexpected errors

def _validate_email(email: str):
    if not email or not _EMAIL_REGEX.match(email):
        return "Invalid email address format."
    domain = email.split('@')[1]
    if not _domain_exists(domain):
        return f"The email domain '{domain}' does not exist. Please enter a real email address."
    return None

def validate_email_address(email: str) -> tuple[bool, str]:
    """Public validator for signup — checks format and domain existence. Returns (ok, message)."""
    err = _validate_email(email.strip().lower())
    if err:
        return False, err
    return True, "Valid email."

def _now():
    return datetime.now(timezone.utc)

def _cleanup_expired():
    now = _now()
    expired = [k for k, v in _store.items() if v["expires_at"] < now]
    for k in expired:
        del _store[k]

def _build_html(name: str, code: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #F7F4EF;
            margin: 0; padding: 0; }}
    .container {{ max-width: 480px; margin: 40px auto; background: #FFFFFF;
                  border-radius: 16px; overflow: hidden;
                  box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg, #9F8FF3, #897AE0);
               padding: 32px 32px 24px; text-align: center; }}
    .header h1 {{ color: white; margin: 0; font-size: 22px; font-weight: 900; }}
    .header p  {{ color: rgba(255,255,255,0.80); margin: 6px 0 0; font-size: 13px; }}
    .body {{ padding: 32px; }}
    .greeting {{ color: #1A1A1A; font-size: 15px; margin-bottom: 20px; }}
    .code-box {{ background: #F4F5F7; border: 2px solid #9F8FF3;
                 border-radius: 12px; padding: 20px;
                 text-align: center; margin: 24px 0; }}
    .code {{ font-size: 38px; font-weight: 900; letter-spacing: 10px;
             color: #897AE0; font-family: monospace; }}
    .expiry {{ color: #666666; font-size: 12px; margin-top: 8px; }}
    .footer {{ padding: 20px 32px; border-top: 1px solid #E5E7EB;
               color: #AAAAAA; font-size: 11px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{APP_NAME}</h1>
      <p>Account Verification</p>
    </div>
    <div class="body">
      <p class="greeting">Hi <strong>{name}</strong>,</p>
      <p style="color:#666666; font-size:14px;">
        Use the code below to verify your account recovery.
        It expires in <strong>5 minutes</strong>.
      </p>
      <div class="code-box">
        <div class="code">{code}</div>
        <div class="expiry">Expires in 5 minutes</div>
      </div>
    </div>
    <div class="footer">
      {APP_NAME} &middot; This is an automated message, please do not reply.
    </div>
  </div>
</body>
</html>
"""

def verify(email: str, code: str) -> dict:
    import hmac as _hmac
    email = email.strip().lower()
    if err := _validate_email(email):
        return {"ok": False, "reason": err}

    with _lock:
        _cleanup_expired()
        entry = _store.get(email)
        if not entry:
            return {"ok": False, "reason": "No OTP found. Please request a new one."}

        if _now() > entry["expires_at"]:
            _store.pop(email, None)
            return {"ok": False, "reason": "Code expired. Please request a new one."}

        entry["attempts"] += 1
        if entry["attempts"] > OTP_MAX_ATTEMPTS:
            _store.pop(email, None)
            return {"ok": False, "reason": "Too many incorrect attempts. Please request a new code."}

        if not _hmac.compare_digest(code.strip(), entry["code"]):
            remaining = OTP_MAX_ATTEMPTS - entry["attempts"]
            return {"ok": False, "reason": f"Incorrect code. {remaining} attempt{'s' if remaining != 1 else ''} left."}

        entry["verified"] = True
        _store.pop(email, None)
        _resend_timestamps.pop(email, None)

    return {"ok": True}

def send_reset_otp(email: str) -> dict:
    email = email.strip().lower()
    if err := _validate_email(email):
        return {"ok": False, "reason": err}

    sender, password = _credentials()
    if not sender or not password:
        return {"ok": False, "reason": "Email credentials not configured in .env (Check SMTP_EMAIL and SMTP_PASSWORD)."}

    code    = _generate_code()
    expires = _now() + timedelta(seconds=OTP_TTL_SECONDS)

    with _lock:
        _store[email] = {
            "code":       code,
            "expires_at": expires,
            "attempts":   0,
            "verified":   False,
        }
        _resend_timestamps[email] = _now()

    msg            = MIMEMultipart("alternative")
    msg["Subject"] = f"{code} — Your {APP_NAME} Password Reset Code"
    msg["From"]    = f"{EMAIL_DISPLAY_NAME} <{sender}>"
    msg["To"]      = email
    msg.attach(MIMEText(f"Your password reset code is: {code}\nIt expires in 5 minutes.", "plain"))
    msg.attach(MIMEText(_build_html("User", code), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender, password)
            server.sendmail(sender, email, msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
