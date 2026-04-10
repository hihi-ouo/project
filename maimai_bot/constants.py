SCORE_COEFFICIENT = [
    [80,  0.136, "A"],
    [90,  0.152, "AA"],
    [94,  0.168, "AAA"],
    [97,  0.2,   "S"],
    [98,  0.203, "S+"],
    [99,  0.208, "SS"],
    [99.5,0.211, "SS+"],
    [100, 0.216, "SSS"],
    [100.5,0.224,"SSS+"],
]

RANK_ICONS = {
    "SSS+": "music_icon_sssp",
    "SSS":  "music_icon_sss",
    "SS+":  "music_icon_ssp",
    "SS":   "music_icon_ss",
    "S+":   "music_icon_sp",
    "S":    "music_icon_s",
    "AAA":  "music_icon_aaa",
    "AA":   "music_icon_aa",
    "A":    "music_icon_a",
}

DIFF_COLORS = {
    "basic":    "#45c147",
    "advanced": "#ffa500",
    "expert":   "#ff6496",
    "master":   "#b450ff",
    "remaster": "#deb4ff",
}

LOGIN_URL = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login?"
    "site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/"
    "maimai-mobile/&back_url=https://maimai.sega.com/"
)

HEADERS = {"User-Agent": "hihiouo"}
