import os
from cryptography.fernet import Fernet

_fernet_instance = None

def get_fernet():
    global _fernet_instance
    if _fernet_instance is None:
        key = os.getenv("TERRAVYN_ENCRYPTION_KEY")
        if not key:
            raise ValueError("TERRAVYN_ENCRYPTION_KEY environment variable is not set.")
        _fernet_instance = Fernet(key.encode())
    return _fernet_instance

def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return encrypted_value
    try:
        f = get_fernet()
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # Return as is or handle error, but usually we just raise or log
        # If it fails to decrypt, it might be plain text (e.g. from before encryption was added)
        # or it might be corrupted. 
        return encrypted_value
