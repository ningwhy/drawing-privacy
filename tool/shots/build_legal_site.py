#!/usr/bin/env python3
"""从 ARB 生成五语种法律静态站（support URL + privacy policy URL）。

## 为什么需要它

ASC 上当前的两个 URL 都是**审核阻塞项**，且都不是"填一下就好"：

1. `supportUrl` = `https://www.facebook.com/Jingqi-103004027902475`
   实测 302 跳到 `facebook.com/login/?next=...` —— 审核员在沙盒里
   大概率看不到任何内容。Guideline 3.1.2（应用内必须提供可用的联系渠道）。
2. `privacyPolicyUrl` = `https://s.orzjun.com/.../service_protocol.html`
   **字段非空，但内容是「服务协议」**，正文写着
   「用户账号、密码和安全性」——本 App 根本没有账号系统。
   声明与实际不符，比留空更糟。

而 App 内已有完整的五语种法律正文（`legal_page.dart` + ARB），
所以正确做法是：**把同一份正文发布成公开网页**，URL 指向它。
一份内容源（ARB），三处消费：App 内页、隐私政策 URL、支持页。

## 用法

```bash
python3 tool/shots/build_legal_site.py --out marketing/site
```

产出：

```
marketing/site/index.html              支持页（五语种切换）
marketing/site/privacy/<lang>.html     隐私政策
marketing/site/terms/<lang>.html       服务条款
```
"""

import argparse
import html
import json
import pathlib
import re
import sys

# ARB 文件名后缀 → URL 路径段 / html lang 属性
LOCALE_MAP = {
    "en": ("en", "English"),
    "zh_Hans": ("zh-Hans", "简体中文"),
    "zh_Hant": ("zh-Hant", "繁體中文"),
    "ja": ("ja", "日本語"),
    "ko": ("ko", "한국어"),
}

APP_NAME = {
    "en": "Drawing Board",
    "zh-Hans": "简笔画涂鸦板",
    "zh-Hant": "簡筆畫塗鴉板",
    "ja": "おえかきボード",
    "ko": "그림판",
}

# 各语种「回到支持页」的文案
BACK_TO_SUPPORT = {
    "en": "Support",
    "zh-Hans": "支持",
    "zh-Hant": "支援",
    "ja": "サポート",
    "ko": "지원",
}

SUPPORT_HTML = {
    "en": """<h1>Support</h1>
<p>Thank you for using Drawing Board. We reply to every message within 15 business days.</p>
<h2>Before you write</h2>
<ul>
  <li><b>Photos not appearing?</b> Open the app once, then grant photo access in
      Settings &rsaquo; Privacy &rsaquo; Photos. The permission is requested only when you tap it.</li>
  <li><b>VIP not restored?</b> Tap the VIP button, then use Restore Purchases. Purchases are
      tied to your Apple Account, not to this device.</li>
  <li><b>Your artwork missing?</b> Artwork is stored only on this device. Uninstalling the app
      deletes it, so export anything you want to keep.</li>
</ul>
<h2>Contact</h2>
<p>Use the contact form on the App Store product page. Please include your device model,
iOS version, and the steps that reproduce the problem. If the issue involves a purchase,
include the order ID.</p>
<h2>Legal</h2>
<ul>
  <li><a href="privacy/{lang}.html">Privacy Policy</a></li>
  <li><a href="terms/{lang}.html">Terms of Service</a></li>
</ul>""",
    "zh-Hans": """<h1>支持</h1>
<p>感谢使用简笔画涂鸦板。我们会在 15 个工作日内回复每一条反馈。</p>
<h2>发消息之前</h2>
<ul>
  <li><b>照片选不上？</b> 打开一次 App，再去「设置 › 隐私 › 照片」里授权。
      权限只在你点击时才会申请。</li>
  <li><b>VIP 没恢复？</b> 点 VIP 按钮，选「恢复购买」。购买记录绑定的是你的 Apple 账户，
      而不是这台设备。</li>
  <li><b>作品不见了？</b> 作品只存在本机，卸载 App 会一并删除，
      想保留的请先导出。</li>
</ul>
<h2>联系方式</h2>
<p>请通过 App Store 商品页的联系入口提交反馈，附上设备型号、iOS 版本，
以及复现问题的步骤。如果涉及购买，请附上订单号。</p>
<h2>法律条款</h2>
<ul>
  <li><a href="privacy/{lang}.html">隐私政策</a></li>
  <li><a href="terms/{lang}.html">服务条款</a></li>
</ul>""",
    "zh-Hant": """<h1>支援</h1>
<p>感謝使用簡筆畫塗鴉板。我們會在 15 個工作天內回覆每一則訊息。</p>
<h2>傳訊息之前</h2>
<ul>
  <li><b>照片選不上？</b> 開啟一次 App，再到「設定 › 隱私 › 照片」授權。
      權限只在你點擊時才會詢問。</li>
  <li><b>VIP 沒恢復？</b> 點 VIP 按鈕，選「恢復購買」。購買紀錄綁定的是你的 Apple 帳號，
      而非這台裝置。</li>
  <li><b>作品不見了？</b> 作品只存在本機，移除 App 會一併刪除，
      想保留的請先匯出。</li>
</ul>
<h2>聯絡方式</h2>
<p>請透過 App Store 商品頁的聯絡入口提交回饋，並附上裝置型號、iOS 版本，
以及重現問題的步驟。若涉及購買，請附上訂單編號。</p>
<h2>法律條款</h2>
<ul>
  <li><a href="privacy/{lang}.html">隱私權政策</a></li>
  <li><a href="terms/{lang}.html">服務條款</a></li>
</ul>""",
    "ja": """<h1>サポート</h1>
<p>おえかきボードをご利用いただきありがとうございます。すべてのご連絡に 15 営業日以内にご返信します。</p>
<h2>お問い合わせの前に</h2>
<ul>
  <li><b>写真を選べない場合</b>：一度アプリを開き、「設定 › プライバシー › 写真」で許可してください。
      権限はタップした時点でしか要求されません。</li>
  <li><b>VIP が復元されない場合</b>：VIP ボタンをタップし「購入を復元」を選んでください。
      購入は端末ではなく Apple アカウントに紐づいています。</li>
  <li><b>作品が見つからない場合</b>：作品は端末内にのみ保存されます。
      アプリを削除すると同時に消えるため、残したいものは先に書き出してください。</li>
</ul>
<h2>お問い合わせ</h2>
<p>App Store の作品ページからご連絡ください。機種、iOS のバージョン、
再現手順をお添えください。購入に関する問題の場合は注文番号もお願いします。</p>
<h2>法的情報</h2>
<ul>
  <li><a href="privacy/{lang}.html">プライバシーポリシー</a></li>
  <li><a href="terms/{lang}.html">利用規約</a></li>
</ul>""",
    "ko": """<h1>지원</h1>
<p>그림판을 이용해 주셔서 감사합니다. 모든 문의는 영업일 기준 15일 이내에 답변드립니다.</p>
<h2>문의하기 전에</h2>
<ul>
  <li><b>사진을 선택할 수 없나요?</b> 앱을 한 번 연 뒤
      「설정 › 개인정보 › 사진」에서 권한을 허용해 주세요.
      권한은 탭하는 시점에만 요청됩니다.</li>
  <li><b>VIP가 복원되지 않나요?</b> VIP 버튼을 누른 뒤 「구매 복원」을 선택하세요.
      구매는 이 기기가 아닌 Apple 계정에 연결됩니다.</li>
  <li><b>작품이 사라졌나요?</b> 작품은 이 기기에만 저장됩니다.
      앱을 삭제하면 함께 삭제되므로 보관할 작품은 먼저 내보내세요.</li>
</ul>
<h2>연락처</h2>
<p>App Store 상품 페이지의 연락 양식을 이용해 주세요. 기기 모델, iOS 버전,
문제가 발생하는 절차를 함께 적어 주세요. 구매 관련 문의는 주문 번호도 필요합니다.</p>
<h2>법적 고지</h2>
<ul>
  <li><a href="privacy/{lang}.html">개인정보 처리방침</a></li>
  <li><a href="terms/{lang}.html">이용약관</a></li>
</ul>""",
}

CSS = """
:root {
  --ink: #2b2118;
  --muted: #6b5d4d;
  --line: #e6dccd;
  --accent: #e8622d;
  --bg: #fffaf1;
  --card: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #f0e8dc; --muted: #b3a595; --line: #3a3129;
    --accent: #ff8a52; --bg: #1a1611; --card: #241f19;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0 20px 72px;
  background: var(--bg); color: var(--ink);
  font: 17px/1.78 -apple-system, "PingFang SC", "Hiragino Sans",
        "Noto Sans KR", system-ui, sans-serif;
}
.wrap { max-width: 720px; margin: 0 auto; }
header {
  padding: 44px 0 22px; border-bottom: 2px solid var(--line); margin-bottom: 34px;
}
h1 { font-size: 32px; line-height: 1.25; margin: 0 0 10px; letter-spacing: -0.01em; }
h2 { font-size: 20px; margin: 38px 0 12px; color: var(--accent); }
p  { margin: 0 0 16px; }
ul { margin: 0 0 16px; padding-left: 22px; }
li { margin-bottom: 10px; }
b { font-weight: 700; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid currentColor; }
a:hover { opacity: .72; }
nav.langs {
  display: flex; flex-wrap: wrap; gap: 8px; margin: 20px 0 0;
}
nav.langs a {
  border: 1px solid var(--line); background: var(--card);
  padding: 6px 14px; border-radius: 999px; font-size: 15px;
  border-bottom-width: 1px;
}
nav.langs a[aria-current="page"] {
  background: var(--accent); color: #fff; border-color: var(--accent);
}
footer {
  margin-top: 56px; padding-top: 22px; border-top: 1px solid var(--line);
  color: var(--muted); font-size: 14px;
}
footer a { border-bottom: none; }
@media (max-width: 480px) { h1 { font-size: 26px; } body { font-size: 16px; } }
"""


def load_arb(arb_dir: pathlib.Path, suffix: str) -> dict:
    return json.loads((arb_dir / f"app_{suffix}.arb").read_text(encoding="utf-8"))


def para_list(arb: dict, prefix: str, count: int) -> list[str]:
    """取 {prefix}1..N，去掉空值，保持 ARB 里的顺序。"""
    out = []
    for i in range(1, count + 1):
        v = arb.get(f"{prefix}{i}")
        if not isinstance(v, str) or not v.strip():
            raise SystemExit(f"缺少段落 {prefix}{i}（ARB 里查不到或为空）")
        out.append(v)
    return out


def md_inline(text: str) -> str:
    """ARB 段落里可能有编号列表（1. / 2. / 3. 各占一行），拆成 ul。"""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(lines) > 1 and all(re.match(r"^\d+\.", ln) for ln in lines):
        items = "".join(f"<li>{html.escape(re.sub(r'^\\d+\\.\\s*', '', ln))}</li>"
                        for ln in lines)
        return f"<ol>{items}</ol>"
    return "".join(f"<p>{html.escape(ln)}</p>" for ln in lines)


def page(title: str, body: str, lang: str, path_prefix: str) -> str:
    name = APP_NAME[lang]
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · {html.escape(name)}</title>
<meta name="robots" content="index, follow">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>{html.escape(title)}</h1>
  <p style="color:var(--muted);margin:0">{html.escape(name)}</p>
  <nav class="langs">
    {"".join(f'<a href="../../{path_prefix}/{s}.html" aria-current="{"page" if s == lang else "false"}">{html.escape(nm)}</a>' for s, nm in LOCALE_MAP.values())}
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <a href="../index.html">{html.escape(BACK_TO_SUPPORT[lang])}</a>
</footer>
</div>
</body>
</html>
"""


def scan_corruption(out: pathlib.Path) -> list[str]:
    """扫出损坏字节 / 未替换占位符。

    ⚠️ 这道门禁是被真实事故逼出来的：韩文支持页里出现过
      `구매는 기기␦␦␦ 아닌` —— U+FFFD 替换字符（原文是 3 个损坏字节）。
      肉眼扫 HTML 很难发现（渲染出来仍是「几乎正确的韩文」），
      但提交给 Apple 后就是审核退回/法务风险。

    返回问题列表（空 = 干净）。
    """
    problems: list[str] = []
    for p in sorted(out.rglob("*.html")):
        raw = p.read_bytes()
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            problems.append(f"{p.relative_to(out)}: 非法 UTF-8 字节 ({e})")
            continue
        for i, line in enumerate(s.splitlines(), 1):
            if "�" in line:
                problems.append(
                    f"{p.relative_to(out)}:{i}: U+FFFD 替换字符 → {line.strip()[:90]}")
            for m in re.findall(r"\{[a-z_]+\}", line):
                problems.append(f"{p.relative_to(out)}:{i}: 未替换占位 {m}")
    return problems


def build(out: pathlib.Path, arb_dir: pathlib.Path) -> None:
    (out / "privacy").mkdir(parents=True, exist_ok=True)
    (out / "terms").mkdir(parents=True, exist_ok=True)

    for suffix, (lang, native) in LOCALE_MAP.items():
        arb = load_arb(arb_dir, suffix)

        # ---- 隐私政策 ----
        parts = [md_inline(arb["privacyPreamble"])]
        for i in range(1, 9):
            parts.append(f"<h2>{html.escape(arb[f'privacyH{i}'])}</h2>")
            parts.append(md_inline(arb[f"privacyP{i}"]))
        (out / "privacy" / f"{lang}.html").write_text(
            page(arb["privacyTitle"], "\n".join(parts), lang, "privacy"),
            encoding="utf-8")

        # ---- 服务条款 ----
        parts = [md_inline(arb["termsPreamble"])]
        for i in range(1, 6):
            parts.append(f"<h2>{html.escape(arb[f'termsH{i}'])}</h2>")
            parts.append(md_inline(arb[f"termsP{i}"]))
        (out / "terms" / f"{lang}.html").write_text(
            page(arb["termsTitle"], "\n".join(parts), lang, "terms"),
            encoding="utf-8")

        # ---- 支持页 ----
        body = SUPPORT_HTML[lang].format(lang=lang)
        nav = "".join(
            f'<a href="{lang}.html" aria-current="page">{html.escape(nm)}</a>'
            for s, nm in LOCALE_MAP.values())
        doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(SUPPORT_TITLE[lang])} · {html.escape(APP_NAME[lang])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>{html.escape(SUPPORT_TITLE[lang])}</h1>
  <p style="color:var(--muted);margin:0">{html.escape(APP_NAME[lang])}</p>
  <nav class="langs">{nav}</nav>
</header>
<main>
{body}
</main>
<footer>&copy; 2026 {html.escape(APP_NAME[lang])}</footer>
</div>
</body>
</html>
"""
        (out / f"{lang}.html").write_text(doc, encoding="utf-8")

    # ---- 默认首页：按 Accept-Language 跳对应语言；否则列全部 ----
    links = "".join(
        f'<li><a href="{lang}.html">{html.escape(native)}</a></li>'
        for lang, native in LOCALE_MAP.values())
    (out / "index.html").write_text(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(APP_NAME["en"])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header><h1>{html.escape(APP_NAME["en"])}</h1></header>
<main>
<h2>Support</h2>
<ul>{links}</ul>
</main>
</div>
</body>
</html>
""", encoding="utf-8")

    # ---- 交付前自检：损坏字节 / 未替换占位必须为 0 ----
    problems = scan_corruption(out)
    if problems:
        print("❌ 静态站自检未通过：", file=sys.stderr)
        for p in problems:
            print(f"   {p}", file=sys.stderr)
        raise SystemExit(1)

    print(f"✅ 静态站已生成（自检通过）：{out}")
    for p in sorted(out.rglob("*.html")):
        print(f"   {p.relative_to(out)}  ({p.stat().st_size} B)")


SUPPORT_TITLE = {
    "en": "Support",
    "zh-Hans": "支持",
    "zh-Hant": "支援",
    "ja": "サポート",
    "ko": "지원",
}


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="marketing/site")
    ap.add_argument("--arb", default="l10n")
    a = ap.parse_args()
    build(root / a.out, root / a.arb)


if __name__ == "__main__":
    main()