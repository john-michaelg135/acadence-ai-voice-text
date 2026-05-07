import os
import secrets
import string
import datetime
import bcrypt
import re
import base64
import sys
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables from .env file
if getattr(sys, 'frozen', False):
    _env_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), '.env')
else:
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

if os.path.exists(_env_path):
    load_dotenv(_env_path)

def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates strong password requirements and returns ALL unmet rules at once.
    Requirements: 8+ chars, uppercase, lowercase, digit, special character.
    """
    errors = []
    if len(password) < 8:
        errors.append("  • At least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("  • At least one uppercase letter (A–Z)")
    if not re.search(r'[a-z]', password):
        errors.append("  • At least one lowercase letter (a–z)")
    if not re.search(r'[0-9]', password):
        errors.append("  • At least one number (0–9)")
    if not re.search(r'[!@#$%^&\*\(\)_\+\-\=\[\]\{\};:\'"<>\.\/\\?|]', password):
        errors.append("  • At least one special character  (!@#$% etc.)")

    if errors:
        return False, "Password must include:\n" + "\n".join(errors)
    return True, "Strong password."

def generate_system_password(length=12) -> str:
    """Generates a secure temporary and random system password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_system_password_expiration():
    """Returns the expiration date (14 days from now) for system-generated passwords."""
    return datetime.datetime.now() + datetime.timedelta(days=14)

def generate_otp() -> str:
    """Generates a 6-digit OTP for account recovery."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

# --- Reversible AES-256 for PII (Emails) ---

def _get_master_secret() -> bytes:
    """
    Retrieves the master secret from environment variables.
    Falls back to generating a new one if not set (for backwards compatibility during migration).
    IMPORTANT: In production, this MUST be set via environment variable.
    """
    master_secret = os.getenv('ENCRYPTION_MASTER_SECRET')
    if not master_secret:
        # Generate a secure default (this should be replaced with env var in production)
        import hashlib
        default_secret = hashlib.sha256(b'AcadenceSecretKey_2026').digest()[:32]
        return default_secret
    return master_secret.encode() if isinstance(master_secret, str) else master_secret

def get_aes_gcm(salt: Optional[bytes] = None) -> tuple[AESGCM, bytes]:
    """
    Derives a 256-bit key from the master secret and returns an AESGCM instance.
    Uses per-operation random salt for enhanced security.
    """
    if salt is None:
        salt = os.urandom(16)  # Generate random salt per operation
    
    master_secret = _get_master_secret()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits for AES-256
        salt=salt,
        iterations=480000,  # OWASP 2023 recommendation (increased from 100k)
    )
    key = kdf.derive(master_secret)
    return AESGCM(key), salt

def encrypt_data(data: str) -> str:
    """
    Encrypts string data using AES-256 GCM with random salt.
    Format: base64(salt + nonce + ciphertext)
    """
    if not data:
        return ""
    
    try:
        gcm, salt = get_aes_gcm()
        nonce = os.urandom(12)  # Recommended nonce size for GCM
        encrypted = gcm.encrypt(nonce, data.encode('utf-8'), None)
        # Return salt + nonce + ciphertext, base64 encoded
        payload = salt + nonce + encrypted
        return base64.b64encode(payload).decode('utf-8')
    except Exception as e:
        import logging
        logging.error(f"Encryption failed: {e}", exc_info=True)
        return ""

def decrypt_data(encrypted_b64: str) -> str:
    """
    Decrypts string data using AES-256 GCM.
    Handles both old format (hardcoded salt) and new format (random salt).
    """
    if not encrypted_b64:
        return ""
    try:
        decoded = base64.b64decode(encrypted_b64)
        
        # New format: 16-byte salt + 12-byte nonce + ciphertext
        if len(decoded) >= 28:
            salt = decoded[:16]
            nonce = decoded[16:28]
            ciphertext = decoded[28:]
        else:
            # This handles backwards compatibility
            nonce = decoded[:12]
            ciphertext = decoded[12:]
            # Try with old hardcoded salt first
            import hashlib
            salt = hashlib.sha256(b'AcadenceAppSalt_2026').digest()[:16]
        
        gcm, _ = get_aes_gcm(salt)
        decrypted = gcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
    except Exception as e:
        import logging
        logging.error(f"Decryption failed: {e}", exc_info=True)
        return ""
