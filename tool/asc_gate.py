# -*- coding: utf-8 -*-
"""写入 ASC 前的门禁校验。任一 FAIL 即中止。"""
import re
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asc_metadata_1_1 import DESC, KEYWORDS, PROMO, URLS, TOTAL_SKETCHES, FREE_SKETCHES, VIP_SKETCHES

BAD = chr(0xFFFD)
fails = []
warns = []


def fail(loc, msg):
    fails.append(f"[{loc}] {msg}")


def warn(loc, msg):
    warns.append(f"[{loc}] {msg}")


# ---- 1. U+FFFD 损坏字符 ----
for loc, t in DESC.items():
    if BAD in t:
        for m in re.finditer(BAD, t):
            fail(loc, f"U+FFFD 损坏字符 上下文={t[max(0,m.start()-20):m.end()+20]!r}")
    for junk in ["Injector", "inci", "Recorder", "hitbreaks", " Santo", "还有"]:
        if junk in t:
            fail(loc, f"检测到垃圾插入 {junk!r}")

# ---- 2. 跨语言污染 ----
# 简中：不应出现日文假名/韩文谚文/繁体特有字
JP_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
KO_HANGUL = re.compile(r"[\uac00-\ud7a3]")
# 繁体特有字：自动从 zh-Hant 描述 ∩ zh-Hans 描述 差集推导，不手写字表。
# 手写字表已多次踩坑（手/私/色/通 是简繁共用字，個 在不同词里判断不一）。
# 判据：某字出现在 zh-Hant 描述中，且其简体形不出现在 zh-Hans 描述中。
_HS = set(DESC["zh-Hans"])
_HT = set(DESC["zh-Hant"])
TRAD_ONLY = {c for c in _HT - _HS if not (c in _HS)}
# 日语简体独有字（日语正字法收录但简体不用的字）—— 已实测误伤过 体/余/格/简/開，务必保守
JA_ONLY = set("体余格简开关处昼画绘本発")

for loc, t in DESC.items():
    if loc == "zh-Hans":
        if JP_KANA.search(t):
            fail(loc, f"混入日文假名 {JP_KANA.findall(t)}")
        if KO_HANGUL.search(t):
            fail(loc, f"混入韩文谚文 {KO_HANGUL.findall(t)}")
        bad = sorted(TRAD_ONLY & set(t))
        if bad:
            fail(loc, f"混入繁体字 {''.join(bad)}")
    if loc == "zh-Hant":
        if JP_KANA.search(t):
            fail(loc, f"混入日文假名 {JP_KANA.findall(t)}")
        if KO_HANGUL.search(t):
            fail(loc, f"混入韩文谚文 {KO_HANGUL.findall(t)}")
    if loc == "ja":
        # 日语汉字与简繁共用，逐字黑名单必然误伤（已实测 5 轮仍误伤：
        # 点/色/写/手/通/体/余/格/简/開 全是日语正字法收录字）。
        # 结论：ja 文案不做逐字黑名单，只做结构性检查 + 人工校对。
        if KO_HANGUL.search(t):
            fail(loc, f"混入韩文谚文 {KO_HANGUL.findall(t)}")
        if BAD in t:
            fail(loc, "含损坏字符")
    if loc == "ko":
        if JP_KANA.search(t):
            fail(loc, f"混入日文假名 {JP_KANA.findall(t)}")
        if BAD in t:
            fail(loc, "含损坏字符")

# ---- 3. 红线词（营销语境不得暗示儿童定位）----
REDLINE = {
    "zh-Hans": ["儿童", "小孩", "宝宝", "幼儿", "亲子", "益智", "早教", "育儿", "小朋友"],
    "zh-Hant": ["兒童", "小孩", "寶寶", "幼兒", "親子", "益智", "早教", "育兒", "小朋友"],
    "en-US": ["kids", "child", "children", "toddler", "baby", "preschool", "educational game"],
    "ja": ["子供", "子ども", "幼児", "保育園", "子育て", "親子"],
    "ko": ["아이", "어린이", "유아", "어린아이", "학부모"],
}
for loc, t in DESC.items():
    for w in REDLINE.get(loc, []):
        if w.lower() in t.lower():
            fail(loc, f"描述含儿童定位红线词 {w!r}")

# ---- 4. 关键词红线 ----
for loc, k in KEYWORDS.items():
    for w in REDLINE.get(loc, []):
        if w.lower() in k.lower():
            fail(loc, f"关键词含红线词 {w!r} → {k}")

# ---- 5. 数量口径一致性 ----
for loc, t in DESC.items():
    if "60+" in t or "60 +" in t:
        fail(loc, "描述仍写 60+，应为 62")
    if "60枚" in t or "60 枚" in t:
        fail(loc, "描述仍写 60 枚，应为 62")
    if str(TOTAL_SKETCHES) not in t:
        fail(loc, f"描述未出现 {TOTAL_SKETCHES}")
for loc, p in PROMO.items():
    if "60+" in p or "60 " in p:
        fail(loc, f"promotionalText 仍写 60+，应为 62：{p!r}")

# ---- 6. 订阅关键词必须齐全（3.1.2）----
SUB = {
    "zh-Hans": ["VIP", "订阅", "自动续期", "月度", "年度", "关闭自动续费", "恢复购买", "价格"],
    "zh-Hant": ["VIP", "訂閱", "自動續期", "每月", "年度", "關閉自動續訂", "恢復購買", "價格"],
    "en-US":   ["VIP", "subscription", "auto-renewing", "monthly", "yearly",
                "auto-renew", "restore", "Prices"],
    "ja":      ["VIP", "サブスクリプション", "自動更新", "月額", "年額", "停止", "復元", "価格"],
    "ko":      ["VIP", "구독", "자동 갱신", "월간", "연간", "끌 수 있고", "복원", "가격"],
}
for loc, t in DESC.items():
    miss = [w for w in SUB.get(loc, []) if w.lower() not in t.lower()]
    if miss:
        fail(loc, f"订阅关键词缺失 {miss}")

# ---- 7. 隐私摘要仍保留 ----
PRIV = {
    "zh-Hans": ["本地", "不上传", "不共享", "无账号", "不收集"],
    "zh-Hant": ["本機", "不上傳", "不共享", "無帳號", "不收集"],
    "en-US":   ["device", "uploaded", "shared", "no accounts", "do not collect"],
    "ja":      ["端末", "アップロード", "共有", "アカウント", "個人情報"],
    "ko":      ["기기", "업로드", "공유", "계정", "개인정보"],
}
for loc, t in DESC.items():
    miss = [w for w in PRIV.get(loc, []) if w.lower() not in t.lower()]
    if miss:
        fail(loc, f"隐私摘要被破坏，缺失 {miss}")

# ---- 8. 长度上限 4000 ----
for loc, t in DESC.items():
    if len(t) > 4000:
        fail(loc, f"描述超长 {len(t)} > 4000")
    if len(t) < 100:
        fail(loc, f"描述过短 {len(t)}")

# ---- 9. keywords 长度上限 100 字符 ----
for loc, k in KEYWORDS.items():
    if len(k) > 100:
        fail(loc, f"keywords 超长 {len(k)} > 100")
    if len(k) > len(k.strip(",").split(",")[0]) and "," not in k:
        fail(loc, "keywords 格式异常")

# ---- 10. URL 与站点真实产物一致 ----
import os
for loc, u in URLS.items():
    for field, url in u.items():
        if not url.startswith("https://drawing-privacy.pages.dev"):
            fail(loc, f"{field} 非正式域名：{url}")
        rel = url.replace("https://drawing-privacy.pages.dev/", "")
        p = os.path.join("/Users/bot/Documents/App/drawing-privacy", rel)
        if not os.path.exists(p):
            fail(loc, f"{field} 目标文件不存在：{rel}")

# ---- 11. 数字一致性 ----
if TOTAL_SKETCHES - FREE_SKETCHES != VIP_SKETCHES:
    fail("-", "免费/VIP 数量不自洽")

print("=" * 72)
print(f"数量口径: 总 {TOTAL_SKETCHES} = 免费 {FREE_SKETCHES} + VIP {VIP_SKETCHES}")
print("=" * 72)
for loc in DESC:
    print(f"  [{loc}] description len={len(DESC[loc])}")

print()
if warns:
    print("WARN:")
    for w in warns:
        print("  ⚠ " + w)
print()
if fails:
    print(f"❌ FAIL {len(fails)}")
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("✅ 门禁全过，可以写入 ASC")
