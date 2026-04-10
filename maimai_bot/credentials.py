from cryptography.fernet import Fernet
import json
import os


# =====================
# 金鑰與加密
# =====================
class CredentialManager:
    KEY_FILE = "secret.key"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        self.fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if os.path.exists(self.KEY_FILE):
            with open(self.KEY_FILE, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(self.KEY_FILE, "wb") as f:
            f.write(key)
        return key

    def _encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        return self.fernet.decrypt(text.encode()).decode()

    def save(self, user_id: int, segaid: str, password: str):
        data = self._load_file()
        data[str(user_id)] = {
            "segaid":   self._encrypt(segaid),
            "password": self._encrypt(password)
        }
        self._save_file(data)

    def load(self, user_id: int):
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return None
        return {
            "segaid":   self._decrypt(entry["segaid"]),
            "password": self._decrypt(entry["password"])
        }

    def delete(self, user_id: int):
        data = self._load_file()
        data.pop(str(user_id), None)
        self._save_file(data)

    def _load_file(self) -> dict:
        if not os.path.exists(self.CREDENTIALS_FILE):
            return {}
        with open(self.CREDENTIALS_FILE, "r") as f:
            return json.load(f)

    def _save_file(self, data: dict):
        with open(self.CREDENTIALS_FILE, "w") as f:
            json.dump(data, f)

    def save_background(self, user_id: int, bg_path: str):
        data = self._load_file()
        if str(user_id) not in data:
            data[str(user_id)] = {}
        data[str(user_id)]["bg_path"] = bg_path
        self._save_file(data)

    def load_background(self, user_id: int) -> str:
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return "bg_vertical.jpg"
        return entry.get("bg_path", "bg_vertical.jpg")
