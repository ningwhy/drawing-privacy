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

## ASC 回填（部署完成后）

正式域名 `https://drawing-privacy.pages.dev`：

| ASC 字段 | 填写 |
|---|---|
| `appInfoLocalizations.supportUrl` | `https://drawing-privacy.pages.dev/zh-Hans.html` |
| `appInfoLocalizations.privacyPolicyUrl` | `https://drawing-privacy.pages.dev/privacy/zh-Hans.html` |
| `appInfoLocalizations.marketingUrl` | `https://drawing-privacy.pages.dev/app/` |
| `appStoreVersionLocalizations.supportUrl` | 同上，按各 locale 换成对应语言页 |

⚠️ 页面内链接一律用**站点根绝对路径**（`/privacy/...`、`/terms/...`、`/`），
不用 `../../` 相对路径 —— 相对路径依赖尾斜杠，用户从 `/terms`（无斜杠）
进来时 `../` 会解析到域外。

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
<p>Email <a href="mailto:{email}">{email}</a>, or use the contact form on the App Store
product page. Please include your device model, iOS version, and the steps that
reproduce the problem. If the issue involves a purchase, include the order ID.</p>
<h2>Frequently asked questions</h2>
<h3>Do I need an account to use Drawing Board?</h3>
<p>No. There is no sign-up and no account. Open the app and start drawing.</p>
<h3>Where is my artwork stored?</h3>
<p>Only on this device. Nothing is uploaded to a server. Uninstalling the app
permanently deletes your artwork, so export anything you want to keep.</p>
<h3>Are my photos uploaded anywhere?</h3>
<p>No. Photo doodling runs entirely on your device, and the photo is never
transmitted or stored by us.</p>
<h3>What does VIP include?</h3>
<p>VIP unlocks every colouring page: 4 line drawings are free, and the remaining
58 come with VIP. Free drawing, photo doodling, wallpapers, and saving to your
gallery are free and unlimited for everyone.</p>
<h3>How do I restore a purchase?</h3>
<p>Tap the VIP button, then use Restore Purchases. Your purchase is tied to your
Apple Account, so it restores on any device you sign in to.</p>
<h3>Which languages are supported?</h3>
<p>The interface is available in English, Simplified Chinese, Traditional Chinese,
Japanese, and Korean.</p>
<h3>Does the app work offline?</h3>
<p>Yes. Colouring, free drawing, photo doodling, and wallpapers all work without a
network connection.</p>
<h2>Legal</h2>
<ul>
  <li><a href="/privacy/{lang}.html">Privacy Policy</a></li>
  <li><a href="/terms/{lang}.html">Terms of Service</a></li>
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
<p>发邮件到 <a href="mailto:{email}">{email}</a>，或通过 App Store 商品页的联系入口提交。
请附上设备型号、iOS 版本，以及复现问题的步骤。如果涉及购买，请附上订单号。</p>
<h2>常见问题</h2>
<h3>需要注册账号吗？</h3>
<p>不需要。没有注册，也没有账号，打开 App 就能直接画。</p>
<h3>我的作品存在哪里？</h3>
<p>只存在这台设备上，不会上传到任何服务器。卸载 App 会永久删除作品，
想保留的请先导出。</p>
<h3>我的照片会被上传吗？</h3>
<p>不会。照片涂鸦完全在本机运行，照片既不传输也不由我们存储。</p>
<h3>VIP 包含哪些内容？</h3>
<p>VIP 解锁全部填色线稿：其中 4 张免费，其余 58 张需要 VIP。
自由画、照片涂鸦、每日壁纸，以及保存到画册，全部免费且不限次数。</p>
<h3>怎么恢复购买？</h3>
<p>点 VIP 按钮，选「恢复购买」。购买绑定的是你的 Apple 账户，
换设备登录同一账户即可恢复。</p>
<h3>支持哪些语言？</h3>
<p>界面支持英文、简体中文、繁體中文、日本語、한국어 五种语言。</p>
<h3>可以离线使用吗？</h3>
<p>可以。填色、自由画、照片涂鸦和壁纸都不需要联网。</p>
<h2>法律条款</h2>
<ul>
  <li><a href="/privacy/{lang}.html">隐私政策</a></li>
  <li><a href="/terms/{lang}.html">服务条款</a></li>
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
<p>寄信到 <a href="mailto:{email}">{email}</a>，或透過 App Store 商品頁的聯絡入口提交。
請附上裝置型號、iOS 版本，以及重現問題的步驟。若涉及購買，請附上訂單編號。</p>
<h2>常見問題</h2>
<h3>需要註冊帳號嗎？</h3>
<p>不需要。沒有註冊，也沒有帳號，開啟 App 就能直接畫。</p>
<h3>我的作品存在哪裡？</h3>
<p>只存在這台裝置上，不會上傳到任何伺服器。移除 App 會永久刪除作品，
想保留的請先匯出。</p>
<h3>我的照片會被上傳嗎？</h3>
<p>不會。照片塗鴉完全在本機執行，照片既不傳輸也不由我們儲存。</p>
<h3>VIP 包含哪些內容？</h3>
<p>VIP 解鎖全部填色線稿：其中 4 張免費，其餘 58 張需要 VIP。
自由畫、照片塗鴉、每日桌布，以及儲存到畫冊，全部免費且不限次數。</p>
<h3>怎麼恢復購買？</h3>
<p>點 VIP 按鈕，選「恢復購買」。購買綁定的是你的 Apple 帳號，
換裝置登入同一帳號即可恢復。</p>
<h3>支援哪些語言？</h3>
<p>介面支援英文、簡體中文、繁體中文、日本語、한국어 五種語言。</p>
<h3>可以離線使用嗎？</h3>
<p>可以。填色、自由畫、照片塗鴉和桌布都不需要連網。</p>
<h2>法律條款</h2>
<ul>
  <li><a href="/privacy/{lang}.html">隱私權政策</a></li>
  <li><a href="/terms/{lang}.html">服務條款</a></li>
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
<p><a href="mailto:{email}">{email}</a> までメールいただくか、App Store の作品ページから
ご連絡ください。機種、iOS のバージョン、再現手順をお添えください。
購入に関する問題の場合は注文番号もお願いします。</p>
<h2>よくある質問</h2>
<h3>アカウント登録は必要ですか？</h3>
<p>不要です。登録もアカウントもありません。アプリを開いてすぐ描けます。</p>
<h3>作品はどこに保存されますか？</h3>
<p>この端末内にのみ保存され、サーバーにはアップロードされません。アプリを削除すると
同時に消えるため、残したいものは先に書き出してください。</p>
<h3>写真はアップロードされますか？</h3>
<p>されません。写真へのドラッグは端末内で処理され、写真は送信も保存もされません。</p>
<h3>VIP には何が含まれますか？</h3>
<p>全ての塗り絵ページが対象です。無料は 4 枚で、残り 58 枚は VIP が必要です。
自由描画・写真へのドラッグ・壁紙・ギャラリーへの保存は、利用 者全員에게無料で回数制限はありません。</p>
<h3>購入の復元はどうしますか？</h3>
<p>VIP ボタンをタップし「購入を復元」を選んでください。購入は Apple アカウントに
紐づいているため、どの端末にログインしても復元されます。</p>
<h3>対応言語は何ですか？</h3>
<p>英語、簡体字中国語、繁体字中国語、日本語、한국어 の 5 言語です。</p>
<h3>オフラインで使えますか？</h3>
<p>はい。塗り絵、自由描画、写真へのドラッグ、壁紙はいずれも通信不要です。</p>
<h2>法的情報</h2>
<ul>
  <li><a href="/privacy/{lang}.html">プライバシーポリシー</a></li>
  <li><a href="/terms/{lang}.html">利用規約</a></li>
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
<p><a href="mailto:{email}">{email}</a> 로 이메일을 보내거나 App Store 상품 페이지의
연락 양식을 이용해 주세요. 기기 모델, iOS 버전, 문제가 발생하는 절차를 함께 적어 주세요.
구매 관련 문의는 주문 번호도 필요합니다.</p>
<h2>자주 묻는 질문</h2>
<h3>계정 가입이 필요한가요?</h3>
<p>필요하지 않습니다. 가입도 계정도 없으며, 앱을 열고 바로 그릴 수 있습니다.</p>
<h3>제 작품은 어디에 저장되나요?</h3>
<p>이 기기에만 저장되며 서버로 업로드되지 않습니다. 앱을 삭제하면 작품도 함께
삭제되므로, 보관할 작품은 먼저 내보내세요.</p>
<h3>제 사진이 업로드되나요?</h3>
<p>업로드되지 않습니다. 사진 드로잉은 전부 기기 안에서 처리되며, 사진은 전송되거나
저장되지 않습니다.</p>
<h3>VIP에는 무엇이 포함되나요?</h3>
<p>모든 색칠 페이지가 해당됩니다. 4장은 무료이고 나머지 58장은 VIP가 필요합니다.
자유 드로잉, 사진 드로잉, 배경화면, 갤러리 저장은 모두 무료이며 횟수 제한도
없습니다.</p>
<h3>구매는 어떻게 복원하나요?</h3>
<p>VIP 버튼을 누른 뒤 「구매 복원」을 선택하세요. 구매는 Apple 계정에 연결되어
어떤 기기에서 로그인해도 복원됩니다.</p>
<h3>지원하는 언어는 무엇인가요?</h3>
<p>영어, 중국어 간체, 중국어 번체, 일본어, 한국어 총 5개 언어를 지원합니다.</p>
<h3>오프라인으로 사용할 수 있나요?</h3>
<p>가능합니다. 색칠, 자유 드로잉, 사진 드로잉, 배경화면 모두 인터넷 연결 없이
사용할 수 있습니다.</p>
<h2>법적 고지</h2>
<ul>
  <li><a href="/privacy/{lang}.html">개인정보 처리방침</a></li>
  <li><a href="/terms/{lang}.html">이용약관</a></li>
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
h3 { font-size: 16px; margin: 22px 0 6px; font-weight: 700; }
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
    {"".join(f'<a href="/{path_prefix}/{s}.html" aria-current="{"page" if s == lang else "false"}">{html.escape(nm)}</a>' for s, nm in LOCALE_MAP.values())}
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <a href="/support/">{html.escape(BACK_TO_SUPPORT[lang])}</a>
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
    (out / "support").mkdir(parents=True, exist_ok=True)

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
        body = SUPPORT_HTML[lang].format(lang=lang, email=SUPPORT_EMAIL)
        # ⚠️ 2026-10-14 修：原来这里写的是 `href="{lang}.html"`，
        # 用的是**外层循环变量 lang**（当前语言）而不是循环项 s，
        # 于是 5 个语言按钮的 href 全指向当前页自己，
        # 且 5 个都带 aria-current="page"。实测 en.html 里 5 个 <a> 全是 en.html。
        # 现在 href 用 s、aria-current 只给当前语言 —— 隐私/条款页（第 264 行）
        # 从一开始就是对的，只有支持页这一处漏了。
        nav = "".join(
            f'<a href="/support/{s}.html" aria-current="{"page" if s == lang else "false"}">'
            f'{html.escape(nm)}</a>'
            for s, nm in LOCALE_MAP.values())
        doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(SUPPORT_DESC[lang])}">
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
        (out / "support" / f"{lang}.html").write_text(doc, encoding="utf-8")

    # ---- 根 index.html 已由官网占用，脚本**不得**生成 ----
    # 站点结构（2026-10-14 起）：
    #   /                      → 产品官网（手写，app/index.html 移上来）
    #   /support/index.html    → 支持门户（supportUrl 指向这里）
    #   /support/<locale>.html → 支持页各语种
    #   /privacy/<locale>.html → 隐私政策
    #   /terms/<locale>.html   → 服务条款
    # ⚠️ 以前这里会生成 index.html 覆盖官网。已移除 ——
    #    若误恢复，官网会被冲成语言选择页。

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

# meta description —— 搜索结果与浏览器标签页摘要
SUPPORT_DESC = {
    "en": "Support for Drawing Board: frequently asked questions about the free "
          "features, VIP, photo doodling, and where your artwork is stored.",
    "zh-Hans": "简笔画涂鸦板支持：免费功能、VIP、照片涂鸦与作品存储位置的常见问题解答。",
    "zh-Hant": "簡筆畫塗鴉板支援：免費功能、VIP、照片塗鴉與作品儲存位置的常見問題解答。",
    "ja": "おえかきボードのサポート：無料機能、VIP、写真へのドoodle、作品の保存場所に関するよくある質問。",
    "ko": "만화보드 지원: 무료 기능, VIP, 사진 위 드로잉, 작품 저장 위치에 대한 자주 묻는 질문.",
}

# ⚠️ 必须与 App Store Connect 里的 Support URL 联系方式保持一致（审核时会核对）。
# 与 Sakinah / Lune 共用同一个开发邮箱。
SUPPORT_EMAIL = "yanoutech@163.com"


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="marketing/site")
    ap.add_argument("--arb", default="l10n")
    a = ap.parse_args()
    build(root / a.out, root / a.arb)


if __name__ == "__main__":
    main()