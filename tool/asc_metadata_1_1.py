# -*- coding: utf-8 -*-
"""1.1 五语种 ASC 元数据新文案。

代码事实唯一来源（禁止手写数字）：
  TOTAL = lib/core/data/sketches.g.dart 条目数
  FREE  = lib/core/data/feature_gate.dart  _freeCount
"""

TOTAL_SKETCHES = 62   # sketches.g.dart 实测条目数
FREE_SKETCHES = 4     # feature_gate.dart _freeCount
VIP_SKETCHES = TOTAL_SKETCHES - FREE_SKETCHES  # 58

DESC = {}

DESC["zh-Hans"] = f"""随手涂两笔的安静角落：填简笔画、自由画，或者直接在照片上涂鸦。

【简笔画填色】
{TOTAL_SKETCHES} 张精心整理的简笔画线稿，从动物、食物到日常物件。
点击任意封闭区域即可上色 —— 选一支蜡笔，点第二下换颜色，看着画面一块块完成。

【自由绘画】
白纸 + 16 色蜡笔，笔粗从 2 到 40 自由调节，橡皮、撤销、重做一应俱全。
笔迹采用样条插值，曲线精确穿过每一个采样点，急转弯也不会被削圆。
写完立刻保存为矢量清晰的 PNG。

【照片涂鸦】
把任意照片导入成画布，直接在上面涂鸦改写。可以画圈、加注释，
也可以大面积擦除重塑。无论是给照片加手绘边框，还是把日常照改成漫画风，都能做到。

【每日壁纸】
每天一句暖心短句，配原创矢量插画与低饱和海报配色，可导出 PNG 并保存到相册。
换一张主题，就是一张新的壁纸。

【VIP 订阅】
{TOTAL_SKETCHES} 张线稿中有 {FREE_SKETCHES} 张免费，其余 {VIP_SKETCHES} 张由 VIP 解锁；
自由画、照片涂鸦、每日壁纸与画册保存始终免费，不限次数。
VIP 为自动续期订阅，提供月度与年度两种方案。可随时在「设置 › Apple 账号 › 订阅」
中关闭自动续费，也可以在应用内恢复购买。实际价格以 App Store 商店页显示为准。
购买页可直接阅读服务条款与隐私政策。

【画册与隐私】
所有作品保存在你的设备本地，不上传、不共享、无账号体系。
不收集任何个人信息，也不申请通讯录或位置权限。

从第一张填色页，到忙碌午后的随手一笔 ——
希望这里既是一个轻松的开始，也是日常表达自己的一个小出口。"""

DESC["zh-Hant"] = f"""隨手塗兩筆的安靜角落：填簡筆畫、自由畫，或者直接在照片上塗鴉。

【簡筆畫填色】
{TOTAL_SKETCHES} 張精心整理的簡筆畫線稿，從動物、食物到日常物件。
點擊任意封閉區域即可上色 —— 選一支蠟筆，點第二下換顏色，看著畫面一塊塊完成。

【自由繪畫】
白紙 + 16 色蠟筆，筆粗從 2 到 40 自由調節，橡皮、復原、重做一應俱全。
筆跡採用樣條插值，曲線精確穿過每一個採樣點，急轉彎也不會被削圓。
寫完立刻儲存為向量清晰的 PNG。

【照片塗鴉】
把任意照片匯入成畫布，直接在上面塗鴉改寫。可以畫圈、加註解，
也可以大面積擦除重塑。無論是給照片加手繪邊框，還是把日常照改成漫畫風，都能做到。

【每日桌布】
每天一句暖心短句，配原創向量插畫與低飽和海報配色，可匯出 PNG 並儲存到相簿。
換一張主題，就是一張新的桌布。

【VIP 訂閱】
{TOTAL_SKETCHES} 張線稿中有 {FREE_SKETCHES} 張免費，其餘 {VIP_SKETCHES} 張由 VIP 解鎖；
自由畫、照片塗鴉、每日桌布與畫冊儲存始終免費，不限次數。
VIP 為自動續期訂閱，提供每月與年度兩種方案。可隨時在「設定 › Apple 帳號 › 訂閱」
中關閉自動續訂，也可以在 App 內恢復購買。實際價格以 App Store 商店頁顯示為準。
購買頁可直接閱讀服務條款與隱私政策。

【畫冊與隱私】
所有作品儲存在你的裝置本機，不上傳、不共享、無帳號體系。
不收集任何個人資訊，也不申請通訊錄或位置權限。

從第一張填色頁，到忙碌午後的隨手一筆 ——
希望這裡既是一個輕鬆的開始，也是日常表達自己的一個小出口。"""

DESC["en-US"] = f"""A quiet place to fill in line art, sketch on a blank page, and doodle over a photo.

【COLORING BOOK】
{TOTAL_SKETCHES} hand-picked line drawings, from animals and food to everyday objects.
Tap any enclosed region to fill it with colour — pick a crayon, tap again to
switch, and watch the picture come together one region at a time.

【FREEHAND CANVAS】
A clean white sheet with 16 crayon colours. Adjust brush width from 2 to 40,
with eraser, undo and redo always one tap away.
Strokes use spline interpolation that passes exactly through every sampled
point, so sharp corners stay sharp and fast turns never detach from your
finger. Export as a crisp, high-resolution PNG.

【PHOTO DOODLE】
Turn any photo into your canvas. Draw over it, circle what matters, annotate,
or erase large areas to reimagine the whole image.
Add a hand-drawn frame to a memory, restyle a snapshot like a comic — it all
starts with one tap.

【DAILY WALLPAPER】
A warm quote of the day paired with original vector artwork and soft poster
tones, ready to export as a PNG and save to your camera roll.
Switch themes and you have a new wallpaper for your home or lock screen.

【VIP SUBSCRIPTION】
{FREE_SKETCHES} of the {TOTAL_SKETCHES} line drawings are free; VIP unlocks the other {VIP_SKETCHES}.
Freehand canvas, photo doodles, daily wallpapers and gallery saving stay free
and unlimited for everyone.
VIP is an auto-renewing subscription available monthly or yearly. Turn off
auto-renew any time in Settings › Apple Account › Subscriptions, and you can
restore a previous purchase inside the app. Prices are shown on the App Store
store page for your region.
The purchase screen links to our Terms of Service and Privacy Policy.

【GALLERY & PRIVACY】
Every piece you create stays on your device. Nothing is uploaded, nothing is
shared, and there are no accounts. We do not collect personal information and
do not ask for contacts or location access.

From a first colouring page to a quick sketch on a busy afternoon — we hope it
works as both an easy place to start and a small everyday way to express
yourself."""

DESC["ja"] = f"""線画のぬりえ、白紙でのおえかき、写真への落書き。
ひと息つける、静かな制作の場所です。

【ぬりえ】
{TOTAL_SKETCHES} 枚の厳選された線画。動物や食べ物、日用品まで。
閉じられた部分をタップすれば色が入ります。
クレヨンを選んで、もう一度タップで色を替える。
絵が少しずつ仕上げられていくのを楽しみます。

【おえかき】
白い画用紙に 16 色のクレヨン。筆の太さは 2 から 40 まで自由に調整でき、
消しゴム・元に戻す・やり直しも指一本で。
線はスプライン補間で、サンプリング点をちょうど通るので、
角は角のまま、急なカーブでも指からは離れません。
書き終えたら高解像度のまま PNG で保存できます。

【写真に描く】
写真をそのまま画用紙にします。なぞる、囲む、書き添える、大きく消す。
写真の印象そのものを描きかえられます。
思い出に手描きの枠を足すのも、写真を使い絵に見せるのも、タップひとつ。

【今日の壁紙】
その日のひとことを添えた温かい言葉と、オリジナルのベクターイラスト、
控えめなポスターの配色。PNG として書き出して写真に保存できます。
テーマを替えれば、新しい壁紙になります。

【VIP サブスクリプション】
{TOTAL_SKETCHES} 枚の線画のうち {FREE_SKETCHES} 枚は無料、残り {VIP_SKETCHES} 枚は VIP で解放されます。
おえかき・写真への落書き・今日の壁紙・ギャラリーの保存は、
どなたでも無料かつ回数無制限で使えます。
VIP は月額と年額の自動更新サブスクリプションです。
自動更新は「設定 › Apple アカウント › サブスクリプション」でいつでも停止でき、
購入済みの内容はアプリ内から復元できます。
価格は地域ごとの App Store 表示が正となります。
購入画面から利用規約とプライバシーポリシンを確認できます。

【ギャラリーとプライバシー】
作ったものはすべてこの端末の中。アップロードも送信も共有もせず、
アカウントも要りません。個人情報は集めない住所や連絡先の許可も求めません。

はじめてのぬりえから、忙しい午後のひといき —
ひと息つける場所でありますように。"""

DESC["ko"] = f"""선화 색칠하기, 빈 캔버스에 자유롭게 그리기, 사진에 그리기.
한숨 돌릴 수 있는 조용한 공간이에요.

【색칠하기】
동물부터 음식, 일상용품까지 고른 선화 {TOTAL_SKETCHES}여 종.
두드린 면 안에 색이 채워져요. 크레용을 고르고 한 번 더 누르면 색이 바뀌어요.
그림이 조금씩 완성되는 재미가 있어요.

【자유롭게 그리기】
흰 캔버스에 크레용 16색. 필기 굵기는 2에서 40까지 조절할 수 있고,
지우개 · 실행 취소 · 다시 하기도 손끝 한 번이면 돼요.
획은 모든 표본점을 정확히 지나는 스플라인 보간이라,
각진 모서리가 뭉개지지 않고 빠르게 꺾어도 손가락을 안 벗어나요.
그리면 또렷한 고해상도 PNG로 저장돼요.

【사진에 그리기】
사진을 그대로 캔버스처럼 쓸 수 있어요. 덧그리기, 동그라미, 메모,
큰 부분 지우기까지. 평범한 사진을 만화처럼 바꿔 보세요.
추억 사진에 손그림 테두리를 넣는 것도, 무엇을 그리는 자유로워요.

【오늘의 배경화면】
그날의 마음을 담은 따뜻한 한 문장과 독창적인 벡터 일러스트,
차분한 포스터 색감. PNG로 저장해 사진 앱에 둘 수 있어요.
테마를 바꾸면 새로운 배경화면이 돼요.

【VIP 구독】
선화 {TOTAL_SKETCHES}종 중 {FREE_SKETCHES}종은 무료이고, 나머지 {VIP_SKETCHES}종은 VIP로 열립니다.
자유그림 · 사진에 그리기 · 오늘의 배경화면 · 갤러리 저장은
누구나 무료로 무제한 이용할 수 있어요.
VIP는 월간과 연간 선택이 가능한 자동 갱신 구독입니다.
자동 갱신은 설정 › Apple 계정 › 구독에서 언제든지 끌 수 있고,
구매하신 내역은 앱 안에서 복원할 수 있습니다.
가격은 해당 지역의 App Store 표시를 기준으로 합니다.
구매 화면에서 이용약관과 개인정보 처리방침을 확인할 수 있어요.

【갤러리와 개인정보】
만든 작업물은 모두 이 기기 안에 남아요. 업로드도 공유도 없고,
계정도 필요 없어요. 개인정보는 모으지 않고 연락처나 위치 권한도 요청하지 않아요.

첫 색칠부터, 바쁜 오후의 짧은 스케치까지 —
손가락으로 시작하는 자리를, 조용한 매일의 한 줄로."""

# ---------- 关键词：剔除儿童定位红线词 ----------
KEYWORDS = {
    "zh-Hans": "简笔画,涂鸦,填色,涂色,自由画,绘画,画板,蜡笔,手绘,速写,涂色书,解压,壁纸,画画,涂鸦板,简笔画教程,绘画app,休闲",
    "zh-Hant": "簡筆畫,塗鴉,填色,塗色,自由畫,繪畫,畫板,蠟筆,手繪,速寫,塗色書,紓壓,桌布,畫畫,塗鴉板,簡筆畫教程,繪畫app,休閒",
    "en-US":   "coloring,doodle,sketch,line art,crayon,freehand,drawing,art,wallpaper,fill,paint,notebook",
    "en-GB":   "coloring,doodle,sketch,line art,crayon,freehand,drawing,art,wallpaper,fill,paint,notebook",
    "en-AU":   "coloring,doodle,sketch,line art,crayon,freehand,drawing,art,wallpaper,fill,paint,notebook",
    "ja":      "ぬりえ,おえかき,イラスト,スケッチ,落書き,写真,クレヨン,ペン,ノート,お絵かき,色ぬり,無料,大人,休日,アプリ,道具",
    "ko":      "색칠하기,자유그림,사진그리기,선화,스케치,일러스트,만화,크레용,필기,그림,색칠,사진,무료,붓,휴식,도구",
}

# ---------- promotionalText：口径 60+ → 62 ----------
PROMO = {
    "zh-Hans": "62 张简笔画线稿等你填色，还有空白画布与照片涂鸦，随手一画都是作品。",
    "zh-Hant": "62 張簡筆畫線稿等你填色，還有空白畫布與照片塗鴉，隨手一畫都是作品。",
    "en-US":   "62 line drawings to fill, a blank canvas for anything else, and photo doodles for the rest.",
    "en-GB":   "62 line drawings to fill, a blank canvas for anything else, and photo doodles for the rest.",
    "en-AU":   "62 line drawings to fill, a blank canvas for anything else, and photo doodles for the rest.",
    "ja":      "62 枚の線画をぬりえ、自由画や写真への落書きも。",
    "ko":      "62장의 선화를 색칠해 보세요. 자유그림과 사진에 그리기까지.",
}

# ---------- URL 字段：按 locale 映射站点真实产物 ----------
# 注意：站点产物用 en.html，不是 en-US.html。ASC locale→站点文件名不是恒等映射。
SITE = "https://drawing-privacy.pages.dev"
LOCALES = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko"]
# ASC locale → 站点文件名
SITE_FILE = {
    "zh-Hans": "zh-Hans",
    "zh-Hant": "zh-Hant",
    "en-US": "en",
    "en-GB": "en",
    "en-AU": "en",
    "ja": "ja",
    "ko": "ko",
}

URLS = {
    loc: {
        "privacyPolicyUrl": f"{SITE}/privacy/{SITE_FILE[loc]}.html",
        "supportUrl":       f"{SITE}/support/{SITE_FILE[loc]}.html",
        "marketingUrl":     f"{SITE}/",
    }
    for loc in LOCALES
}
