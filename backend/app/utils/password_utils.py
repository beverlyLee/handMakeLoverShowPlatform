import hashlib
import secrets
import re

def hash_password_md5(password: str) -> str:
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def hash_password_sha256(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    
    password_salt = password + salt
    password_hash = hashlib.sha256(password_salt.encode('utf-8')).hexdigest()
    
    return password_hash, salt

def hash_password(password: str, salt: str = None) -> tuple:
    return hash_password_sha256(password, salt)

def verify_password(password: str, stored_hash: str, stored_salt: str = None) -> bool:
    if stored_salt:
        computed_hash, _ = hash_password_sha256(password, stored_salt)
        if computed_hash == stored_hash:
            return True
    
    md5_hash = hash_password_md5(password)
    if md5_hash == stored_hash:
        return True
    
    return False

def generate_password_hash(password: str) -> dict:
    password_hash, salt = hash_password_sha256(password)
    return {
        'password_hash': password_hash,
        'password_salt': salt
    }

def generate_password_hash_md5(password: str) -> dict:
    return {
        'password_hash': hash_password_md5(password),
        'password_salt': None
    }

def validate_password_strength(password: str) -> tuple:
    if len(password) < 6:
        return False, '密码长度不能少于6位'
    
    if not re.search(r'[a-zA-Z]', password):
        return False, '密码必须包含字母'
    
    if not re.search(r'[0-9]', password):
        return False, '密码必须包含数字'
    
    return True, None
