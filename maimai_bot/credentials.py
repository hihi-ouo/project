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
            with open(self.KEY_FILE, "rb") as f: # 用rb而不是r是因為要讀取的內容是bytes，同理下面的wb也是
                return f.read()
        key = Fernet.generate_key()
        with open(self.KEY_FILE, "wb") as f:
            f.write(key)
        return key

    # fernet的encrypt()和decrypt()分別用來加密和解密文字，encode()是將string轉成bytes，decode()則是反過來
    # 這裡要轉成bytes是因為fernet只接受bytes的輸入，decode()轉回string則是要存入json檔
    def _encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        return self.fernet.decrypt(text.encode()).decode()

    # 直接由bot.py那邊(/login)呼叫，加密好使用者的帳密後用_save_file()儲存
    def save(self, user_id: int, segaid: str, password: str):
        data = self._load_file()
        data[str(user_id)] = {
            "segaid":   self._encrypt(segaid),
            "password": self._encrypt(password)
        }
        self._save_file(data)

    # 直接由bot.py那邊(/rating)呼叫，用user_id尋找儲存的帳密，若是沒有則回傳None(沒有登入)，有的話則解密後回傳
    def load(self, user_id: int):
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return None
        return {
            "segaid":   self._decrypt(entry["segaid"]),
            "password": self._decrypt(entry["password"])
        }

    # 直接由bot.py那邊(/logout)呼叫，刪除使用者的帳密
    def delete(self, user_id: int):
        data = self._load_file()
        data.pop(str(user_id), None)
        self._save_file(data)

    # 打開credentials.json
    def _load_file(self) -> dict:
        if not os.path.exists(self.CREDENTIALS_FILE):
            return {}
        with open(self.CREDENTIALS_FILE, "r") as f:
            return json.load(f)
        
    # 儲存credentials.json
    def _save_file(self, data: dict):
        with open(self.CREDENTIALS_FILE, "w") as f:
            json.dump(data, f)

    # 將使用者的user_id底下新增一個bg_path的欄位來儲存自訂背景圖片的路徑
    def save_background(self, user_id: int, bg_path: str):
        data = self._load_file()
        if str(user_id) not in data:
            data[str(user_id)] = {}
        data[str(user_id)]["bg_path"] = bg_path
        self._save_file(data)

    # 讀取使用者的自訂背景圖片路徑(若沒有則抓預設路徑)
    def load_background(self, user_id: int) -> str:
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return "bg_vertical.jpg"
        return entry.get("bg_path", "bg_vertical.jpg")
