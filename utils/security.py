import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import string
import datetime

# A fixed salt for key derivation in this demonstration, normally this should be securely stored or random per user.
# In a real app, this should be an environment variable.
MASTER_SECRET = b'AcadenceSecretKey_2026'
SALT = b'AcadenceAppSalt_2026'

def get_aes_gcm():
    """Derives a 256-bit key from the master secret and returns an AESGCM instance."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits for AES-256
        salt=SALT,
        iterations=100000,
    )
    key = kdf.derive(MASTER_SECRET)
    return AESGCM(key)

def encrypt_data(data: str) -> str:
    """Encrypts string data using AES-256 GCM."""
    if not data:
        return ""
    gcm = get_aes_gcm()
    nonce = os.urandom(12)  # Recommended nonce size for GCM
    encrypted = gcm.encrypt(nonce, data.encode('utf-8'), None)
    # Return nonce + ciphertext, base64 encoded
    return base64.b64encode(nonce + encrypted).decode('utf-8')

def decrypt_data(encrypted_b64: str) -> str:
    """Decrypts string data using AES-256 GCM."""
    if not encrypted_b64:
        return ""
    try:
        decoded = base64.b64decode(encrypted_b64)
        nonce = decoded[:12]
        ciphertext = decoded[12:]
        gcm = get_aes_gcm()
        decrypted = gcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return ""

def generate_system_password(length=12) -> str:
    """Generates a secure temporary and random system password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def verify_password(plain_password: str, encrypted_password: str) -> bool:
    """Verifies a plain password against the stored encrypted password (we encrypt it to check equality)."""
    # Wait, AES-256 encryption produces different ciphertexts due to the random nonce.
    # To verify passwords properly, we should decrypt the stored one and compare.
    decrypted = decrypt_data(encrypted_password)
    return decrypted == plain_password

def get_system_password_expiration():
    """Returns the expiration date (14 days from now) for system-generated passwords."""
    return datetime.datetime.now() + datetime.timedelta(days=14)

def generate_otp() -> str:
    """Generates a 6-digit OTP for account recovery."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))
