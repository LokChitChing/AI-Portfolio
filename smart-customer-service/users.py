"""
用户认证模块 (AuthHandler)
使用 AES 加密 Token 实现登录鉴权
"""

import hashlib
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class AuthHandler:
    """
    处理用户登录、Token 生成与验证
    """
    
    def __init__(self, secret_key: str = None):
        # 默认密钥（生产环境应从环境变量读取）
        self.secret_key = secret_key or "default-secret-key-change-in-production"
        # 模拟用户数据库（实际应查询数据库）
        self.users_db = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "role": "admin"
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """SHA256 哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_aes_key(self) -> bytes:
        """从 secret_key 派生 AES 密钥（32字节）"""
        return hashlib.sha256(self.secret_key.encode()).digest()
    
    def _encrypt_token(self, data: Dict) -> str:
        """AES-GCM 加密 Token"""
        key = self._generate_aes_key()
        iv = secrets.token_bytes(12)  # GCM 推荐12字节IV
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        plaintext = json.dumps(data).encode()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        # 组合 iv + ciphertext + tag
        token_data = iv + ciphertext + encryptor.tag
        return base64.urlsafe_b64encode(token_data).decode()
    
    def _decrypt_token(self, token: str) -> Optional[Dict]:
        """AES-GCM 解密 Token"""
        try:
            key = self._generate_aes_key()
            token_data = base64.urlsafe_b64decode(token)
            iv = token_data[:12]
            ciphertext = token_data[12:-16]
            tag = token_data[-16:]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return json.loads(plaintext.decode())
        except Exception:
            return None
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        用户登录，成功返回 Token，失败返回 None
        """
        user = self.users_db.get(username)
        if not user:
            return None
        if user["password_hash"] != self._hash_password(password):
            return None
        
        # 生成 Token（包含用户名、角色、过期时间）
        payload = {
            "username": username,
            "role": user["role"],
            "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        return self._encrypt_token(payload)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证 Token，有效则返回 payload，无效返回 None
        """
        payload = self._decrypt_token(token)
        if not payload:
            return None
        # 检查是否过期
        exp = datetime.fromisoformat(payload.get("exp", ""))
        if exp < datetime.utcnow():
            return None
        return payload