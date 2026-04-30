import hashlib
import secrets

def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    
    password_salt = password + salt
    password_hash = hashlib.sha256(password_salt.encode('utf-8')).hexdigest()
    
    return password_hash, salt

def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    computed_hash, _ = hash_password(password, stored_salt)
    return computed_hash == stored_hash

def generate_password_hash(password: str) -> dict:
    password_hash, salt = hash_password(password)
    return {
        'password_hash': password_hash,
        'password_salt': salt
    }
