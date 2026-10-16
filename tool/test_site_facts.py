#!/usr/bin/env python3
"""官网页面的防回归门禁 —— 跑法：`python3 tool/test_site_facts.py`

守三条线，每一条都对应一个**已经真实发生过**的问题：

| 线 | 抓什么 | 真实事故 |
|---|---|---|
| 事实线 | 官网写死的数字与 Dart 源码不一致 | 62 vs 72（Guideline 2.3）|
| 链接线 | 商店链接会丢失 app id / 假跳转 | `href="#get"` 假跳转；裸链接落到商店首页 |
| 合规线 | 儿童定位 / 儿童专用表述 | 全年龄红线被破坏 |

## ⚠️ 为什么判据要「执行脚本读最终产物」

第一版判据是 `content.count('72')` —— 这类「存在性」判据对「哪一处写错」零判别力：
9 处里改对 8 处照样绿。定稿后每条断言都读 `site_facts.render()` 的输出，
也就是**真正会部署上去的那份 HTML**。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import site_facts  # noqa: E402

SITE = site_facts.SITE_ROOT
INDEX = SITE / "index.html"

_fails: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if ok:
        print(f"  ✅ {label}")
    else:
        print(f"  ❌ {label}")
        if detail:
            for line in detail.splitlines():
                print(f"       {line}")
        _fails.append(label)


def main() -> int:
    facts = site_facts.all_facts()
    total, free = facts["sketchTotal"], facts["sketchFree"]
    print(f"\n=== 事实派生（源：children_drawing Dart 源码）===")
    for k, v in facts.items():
        print(f"  {k:14} = {v}")

    raw = INDEX.read_text(encoding="utf-8")
    # 🔴 判据读的是 render() 之后的产物 —— 和部署上线的完全一致
    html = site_facts.render(raw)

    print(f"\n=== 1. 事实线：线稿数量 ===")
    # 找出所有「N 张 / N 枚 / N 款」形态的数字
    found = sorted({int(m) for m in re.findall(r"(\d+)\s*(?:张|款)", html)})
    stale = [n for n in found if n not in (total, free, 16)]
    hint = "把字面量换成 {sketchTotal} / {sketchFree}，由 site_facts.py 部署时替换"
    check(
        not stale,
        f"页面里出现的线稿数量只有 {total}（总数）或 {free}（免费）",
        f"出现写死的其它数字：{stale}\n"
        f"  → 这些数字没有从 Dart 源码派生，加素材后不会自动更新。\n"
        f"  → 修法：{hint}",
    )

    old = re.findall(r"\b62\b", html)
    check(not old, "不存在历史漂移值 62", f"仍有 {len(old)} 处")

    check(
        f"{total} 张" in html,
        f"页面确实写出了总数 {total} 张",
        f"没找到「{total} 张」—— 占位符可能没被替换（未替换的占位符："
        f"{site_facts.unfilled_placeholders(raw)}）",
    )
    check(
        not site_facts.unfilled_placeholders(raw),
        "所有 {key} 占位符都已被替换",
        f"漏替换：{site_facts.unfilled_placeholders(raw)}",
    )

    print(f"\n=== 2. 事实线：笔刷与颜色 ===")
    check(
        f"{facts['brushCount']} 种笔" in html,
        f"页面写出的笔刷种数 = {facts['brushCount']}",
        f"没找到「{facts['brushCount']} 种笔」",
    )
    check(
        f"{facts['colorCount']} 色" in html,
        f"页面写出的颜色数 = {facts['colorCount']}",
        f"没找到「{facts['colorCount']} 色」",
    )

    print(f"\n=== 3. 链接线：商店跳转 ===")
    # 3a 假跳转
    fake = re.findall(r'href="#get"', html)
    check(
        not fake,
        "没有指向锚点的假下载按钮",
        f"仍有 {len(fake)} 处 href=\"#get\" —— 下载按钮必须跳真实商店",
    )
    # 3b 商店链接必须带国家码（实测：不带会丢失 app id）
    store_links = re.findall(r'href="(https://(?:apps|itunes)\.apple\.com/[^"]+)"', html)
    check(bool(store_links), "页面上有商店链接")
    naked = [u for u in store_links if not re.match(
        r"https://(?:apps|itunes)\.apple\.com/[a-z]{2}/app/", u)]
    check(
        not naked,
        "所有商店链接都带国家码前缀",
        f"这些链接会 302 到商店首页并**丢失 app id**（2026-10-16 实测）：\n"
        + "\n".join(f"  {u}" for u in naked),
    )
    # 3c app id 正确
    wrong_id = [u for u in store_links if "1501497099" not in u]
    check(
        not wrong_id,
        "商店链接的 app id 正确 (1501497099)",
        "\n".join(f"  {u}" for u in wrong_id),
    )
    # 3d 支持页也查一遍 —— 它是 supportUrl，审核员会点
    sup = SITE / "support" / "index.html"
    if sup.exists():
        s_html = sup.read_text(encoding="utf-8")
        s_links = re.findall(
            r'href="(https://(?:apps|itunes)\.apple\.com/[^"]+)"', s_html)
        s_naked = [u for u in s_links if not re.match(
            r"https://(?:apps|itunes)\.apple\.com/[a-z]{2}/app/", u)]
        check(
            not s_naked,
            "支持页的商店链接也带国家码",
            "\n".join(f"  {u}" for u in s_naked),
        )

    print(f"\n=== 4. 链接线：站内链接绝对化 ===")
    # 跨目录链接在无尾斜杠 URL 下会解析到域外
    # ⚠️ 只看 **另一个属性里嵌的 URL**（如 og:image、canonical）：
    #    href/src 必须以 / 开头才是站内绝对路径；资源类（assets/…、style.css）
    #    是同目录相对路径，README 明确允许。
    rel = []
    for attr, url in re.findall(r'(href|src)="([^"]+)"', html):
        if url.startswith(("/", "#", "mailto:", "http://", "https://")):
            continue
        if url.startswith("../") or url.startswith("./"):
            rel.append(f"{attr}=\"{url}\"  ← 会解析到域外")
    check(
        not rel,
        "跨目录链接用站点根绝对路径",
        "\n".join(f"  {u}" for u in rel)
        + "\n  → 用户从 /terms（无尾斜杠）进入时 ../ 会解析到域外",
    )

    print(f"\n=== 5. 合规线：全年龄 ===")
    # 儿童定位词。⚠️ 只查 HTML 可见文本，不查注释 ——
    # 注释里写「禁止儿童定位」是维护者看的，不该被判违规。
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    red = ["儿童专用", "儿童 App", "儿童app", "儿童绘画 App", "kids app", "Kids App",
           "for kids", "亲子", "兒童專用", "子供向け", "어린이 전용"]
    hit = [w for w in red if w.lower() in body.lower()]
    check(
        not hit,
        "无儿童定位表述（全年龄红线）",
        f"命中：{hit}\n  → 本产品是全年龄绘画工具，"
        f"儿童定位会被判 Kids 类目倾向并影响年龄分级审核。",
    )

    print(f"\n=== 6. 交付完整性 ===")
    # 所有 <img src> 必须真实存在（官网禁 CSS 伪造 UI，也禁死图）
    missing = []
    for src in re.findall(r'<img[^>]+src="([^"]+)"', html):
        if src.startswith(("http://", "https://", "data:")):
            continue
        if not (SITE / src).exists():
            missing.append(src)
    check(not missing, "所有图片文件真实存在", "\n".join(f"  {m}" for m in missing))

    print(f"\n{'=' * 56}")
    if _fails:
        print(f"❌ {len(_fails)} 条门禁未通过：")
        for f in _fails:
            print(f"   - {f}")
        return 1
    print("✅ 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
