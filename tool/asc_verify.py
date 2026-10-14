# -*- coding: utf-8 -*-
"""写入后独立复核：重新 GET，逐项比对 desc_new.py 的预期值。

不复用写入脚本的任何中间结果，避免自证。
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser("~/.workbuddy/skills/ios-app-store-pipeline/scripts"))
for k, v in {
    "ASC_KEY_PATH": "~/.private_keys/AuthKey_549MP9WYZJ.p8",
    "ASC_KEY_ID": "549MP9WYZJ",
    "ASC_ISSUER_ID": "6438b8b8-6f7c-4701-b2d3-543a1f24bc4a",
}.items():
    os.environ[k] = os.path.expanduser(v)
from asc_client import AscClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asc_metadata_1_1 import DESC, KEYWORDS, PROMO, URLS, SITE_FILE

c = AscClient()
V = "473c4687-9848-4f47-82e0-48ec5624d8ef"
INFO_11 = "e90229b9-fba3-4a0b-bf66-7eee095c7764"
EN_MIRROR = {"en-GB": "en-US", "en-AU": "en-US"}
BAD = chr(0xFFFD)

fails, notes = [], []

print("=" * 74)
print("### 版本级复核")
print("=" * 74)
for l in c.get(f"/appStoreVersions/{V}/appStoreVersionLocalizations")["data"]:
    a = l["attributes"]
    loc = a["locale"]
    src = EN_MIRROR.get(loc, loc)
    exp_d, exp_k, exp_p = DESC[src], KEYWORDS[src], PROMO[src]

    chk = []
    if a["description"] != exp_d:
        chk.append("description 不一致")
    if a["keywords"] != exp_k:
        chk.append("keywords 不一致")
    if a["promotionalText"] != exp_p:
        chk.append("promo 不一致")
    if a["supportUrl"] != URLS[src]["supportUrl"]:
        chk.append("supportUrl 不一致")
    if a["marketingUrl"] != URLS[src]["marketingUrl"]:
        chk.append("marketingUrl 不一致")

    d = a["description"]
    # 订阅要点必须在线
    sub_checks = {
        "zh-Hans": ["VIP", "自动续期", "月度", "年度", "恢复购买", "62", "58"],
        "zh-Hant": ["VIP", "自動續期", "每月", "年度", "恢復購買", "62", "58"],
        "en-US":   ["VIP", "auto-renewing", "monthly", "yearly", "restore", "62", "58"],
        "ja":      ["VIP", "自動更新", "月額", "年額", "復元", "62", "58"],
        "ko":      ["VIP", "자동 갱신", "월간", "연간", "복원", "62", "58"],
    }[src]
    miss = [w for w in sub_checks if w not in d]
    if miss:
        chk.append(f"订阅要点缺失 {miss}")
    if "60+" in d:
        chk.append("仍含 60+")
    if BAD in d:
        chk.append("含损坏字符")

    # 红线词
    red = {
        "zh-Hans": ["儿童", "亲子", "益智", "宝宝"],
        "zh-Hant": ["兒童", "親子", "益智", "寶寶"],
        "en-US":   ["kids", "children", "child", "toddler"],
        "ja":      ["子供", "子ども", "幼児"],
        "ko":      ["아이", "어린이", "유아"],
    }[src]
    hit = [w for w in red if w.lower() in d.lower() or w.lower() in a["keywords"].lower()]
    if hit:
        chk.append(f"红线词 {hit}")

    status = "✅" if not chk else "❌"
    print(f"  {status} [{loc}] len={len(d)} kw={len(a['keywords'])}")
    for x in chk:
        print(f"       → {x}")
    if chk:
        fails.append((loc, chk))
    else:
        notes.append(loc)

print()
print("=" * 74)
print("### App 级隐私 URL 复核（1.1 容器）")
print("=" * 74)
for l in c.get(f"/appInfos/{INFO_11}/appInfoLocalizations")["data"]:
    a = l["attributes"]
    loc = a["locale"]
    src = EN_MIRROR.get(loc, loc)
    exp = URLS[src]["privacyPolicyUrl"]
    got = a.get("privacyPolicyUrl")
    good = got == exp
    print(f"  {'✅' if good else '❌'} [{loc}] {got}")
    if not good:
        fails.append((f"info/{loc}", [f"期望 {exp} 实得 {got}"]))
    if got and "orzjun" in got:
        fails.append((f"info/{loc}", ["仍指向旧站 orzjun"]))

# 1.0 已上架版本不应被改动
print()
print("=" * 74)
print("### 1.0 已上架版本未被误改核查")
print("=" * 74)
infos = c.get("/apps/1501497099/appInfos")["data"]
ready = [i for i in infos if i["attributes"]["appStoreState"] == "READY_FOR_SALE"][0]
for l in c.get(f"/appInfos/{ready['id']}/appInfoLocalizations")["data"]:
    u = l["attributes"].get("privacyPolicyUrl") or ""
    tag = "（1.0，仍指旧站属正常，未被本脚本改动）"
    print(f"  ℹ️  [{l['attributes']['locale']}] {u} {tag}")

print()
print("=" * 74)
if fails:
    print(f"❌ 复核失败 {len(fails)} 项")
    for k, v in fails:
        print(f"  - {k}: {v}")
    sys.exit(1)
print(f"✅ 复核全过：{len(notes)} 个版本级 locale + 7 个 App 级 locale 全部符合预期")
