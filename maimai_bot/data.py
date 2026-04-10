from bisect import bisect_right
from constants import SCORE_COEFFICIENT
import requests
import json
import os


# =====================
# 資料管理
# =====================
class MaimaiData:
    def __init__(self):
        self.level_map = {}
        self._load_dxdata()

    # 抓取DXrating的json檔
    def _load_dxdata(self):
        if not os.path.exists("dxdata.json"):  # 判斷是否抓取過(檢測資料夾中的dxdata.json是否存在)
            print("下載 dxdata.json...")
            response = requests.get(
                "https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json"
            )
            dx_data = response.json() #將request接受到的內容解析成字典/列表的方式存進dx_data
            with open("dxdata.json", "w", encoding="utf-8") as f:
                json.dump(dx_data, f, ensure_ascii=False, indent=2)
                # open() 裡面的"w"對應寫入(也會覆蓋)，"r"對應讀取
                # dump會將字典的內容轉成json，load則是反過來
                # ensure_ascii = False 是因為有日文字體，indent則是行距，不影響程式本身但方便查看dxdata.json的內容

        with open("dxdata.json", "r", encoding="utf-8") as f:
            dx_data = json.load(f)

        for song in dx_data["songs"]:
            title = song["title"]
            image_name = song["imageName"]
            for sheet in song["sheets"]:
                chart_type = "DX" if sheet["type"] == "dx" else "STANDARD"
                difficulty = sheet["difficulty"]
                self.level_map[(title, chart_type, difficulty)] = [
                    sheet["internalLevelValue"],
                    image_name,
                ]
        # 將原本dxdata大量的資訊只保留
        # 標題(title), 歌曲圖片url(image_name), 新/舊歌(chart_type), 歌曲難度(expert/master之類的)(difficulty), 確切定數(internalLevelValue)
        # 並存在level_map裡面(前三者當作key, 後兩者是value)

    # 根據已知的歌曲名稱等資訊回傳確切定數和圖片url(方便抓取縮圖)
    def get_level_and_image(self, title, kind, difficulty):
        entry = self.level_map.get((title, kind, difficulty))
        if entry:
            return entry[0], entry[1]
        return None, None

    @staticmethod #靜態方法，不會有self參數所以也不能修改物件和類別的狀態，通常用在傳入參數運算
    # 這邊便是只傳入score和level來計算這首歌玩家獲得的rating
    def calc_rating(score, level):
        idx = bisect_right(SCORE_COEFFICIENT, score, key=lambda x: x[0])
        # 使用二分搜確認score是在甚麼區間並回傳idx(像是99.38就在99到99.5之間)
        if idx == 0:
            return 0, "B"
        # 雖然說maimai裡面還有C和D的分數線，不過通常這些分數並不會進入b35或n15，所以統一不做計算(回傳0)
        coefficient = SCORE_COEFFICIENT[idx - 1][1]
        score_level = SCORE_COEFFICIENT[idx - 1][2]
        base = 100.5 if idx == len(SCORE_COEFFICIENT) else score
        return int(base * coefficient * level), score_level
        # maimai rating的計算方式是將score(例:99.38) * 係數(寫在SCORE_COEFFICIENT裡) * 確切定數(例:13.8)
        # 然而若是score超過100.5就統一以100.5計算(最高可以到101，也就是理論值)
