# drawing-privacy

简笔画涂鸦板（Drawing Board）的**官网 + 法务与支持静态站**，整站部署到 Cloudflare Pages。

| 路径 | 内容 | ASC 对应字段 |
|---|---|---|
| `/` | **产品介绍官网** | `marketingUrl` |
| `/support/` | 支持门户（五语种导航） | `supportUrl` |
| `/privacy/<locale>.html` | 隐私政策 | `privacyPolicyUrl` |
| `/terms/<locale>.html` | 服务条款 | App 内链接 |
| `/support/<locale>.html` | 支持页 | — |

`locale` ∈ `zh-Hans` · `zh-Hant` · `en` · `ja` · `ko`

## 文件结构

```
index.html              产品官网（手写，根路径）  ← marketingUrl
style.css               官网样式（手写）
assets/icon.png         App 图标
assets/shots/*.png      真实模拟器截图（非伪造 UI）
support/
  index.html            支持门户（手写）        ← supportUrl
  <locale>.html         支持页（生成物）
privacy/<locale>.html   隐私政策（生成物）
terms/<locale>.html     服务条款（生成物）
404.html                未找到页
_headers                Cloudflare Pages 安全响应头
tool/shots/build_legal_site.py   法务站生成器
```

⚠️ **`build_legal_site.py` 不得生成根 `index.html`** —— 那是官网，
一旦被覆盖会变成语言选择页。脚本里已移除该逻辑并写了注释钉死。

## 构建

### 官网页面

`index.html` + `style.css` + `assets/` 是**手写源**，直接改即可：零外部资源、纯 HTML/CSS。

#### 🔴 事实数字不得写死

`index.html` 里任何「素材数量 / 笔刷种数 / 颜色数」都必须**从
`tool/site_facts.py` 派生**，不要写字面量。

2026-10-16 实测事故：App Store 上已上架的 1.1 文案写「62 张简笔画」，
而代码真源 `kSketchLibraryCount` 早已是 72；同一天发现**官网也有 9 处
写死 62**。两个仓库各有一份互不知情的副本，没有任何东西在看住它 ——
这正是 Guideline 2.3（元数据与实际功能不符）。

`tool/site_facts.py` 从 children_drawing 的 Dart 源码静态派生：

| 事实 | 源文件 | 解析对象 |
|---|---|---|
| 线稿总数 | `sketches.g.dart` | `_library` 顶层列表条目数 |
| 免费张数 | `feature_gate.dart` | `kFreeSketchCount` |
| 笔刷种数 | `brushes.dart` | `BrushRegistry.available` |
| 调色板色数 | `palette.dart` | `kCrayonPalette` |

⚠️ **跨仓库读不到就抛错，绝不退回硬编码** —— 退回硬编码正是漂移的根因。
跨仓库路径可用环境变量 `DRAWING_FLUTTER_REPO` 覆盖。

#### 🔴 商店链接必须带国家码

2026-10-16 逐变体实测（curl 跟到底看 `url_effective`）：

| 写法 | 桌面浏览器最终落点 |
|---|---|
| `apps.apple.com/app/id1501497099` | `apps.apple.com/cn/iphone/today` ← **app id 丢失** |
| `apps.apple.com/cn/app/id1501497099` | 正确跳到 App 页 |
| `itunes.apple.com/app/id1501497099` | 同上，丢失 |

iOS 移动 UA 下裸链接还会 301 到 `itms-appss://`（非法 scheme）。

⚠️ 这**不是**「中国区没上架」—— iTunes lookup 显示 cn/us/jp/kr 全都有
`resultCount=1`。所以正确做法是加国家码前缀，不是换区域。

正确写法：`https://apps.apple.com/cn/app/id1501497099`，
下载按钮额外加 `?mt=8` 唤起 App Store App。

#### 门禁

```bash
python3 tool/test_site_facts.py    # 13 条：事实线 / 链接线 / 合规线
```

判据读 `site_facts.render()` 的输出（即**真正会部署的那份 HTML**），
不解析源码 —— 第一版用 `script.contains(...)` 结果命中了自己文档里的
历史说明（记忆铁律：规则命中自己的文档 = 自我短路）。

注入证伪记录：

| 注入 | 结果 |
|---|---|
| 官网写回 `62` | ✅ 2 条红 |
| 下载按钮改回 `href="#get"` + 裸商店链接 | ✅ 2 条红 |

产品图为 `App Store 截图流水线`产出的**真实模拟器截图**（缩放到 900px 宽、已去 alpha）。
⚠️ 禁止用 CSS/HTML 伪造 App UI。

⚠️ **跨目录链接一律用站点根绝对路径**（`/privacy/…`、`/terms/…`、`/support/…`、`/`），
不要用 `../../` 或 `support/` 这类相对路径 —— 相对路径依赖尾斜杠，
用户从 `/terms`（无斜杠）进入时 `../` 会解析到域外。

官网页内**同目录**资源（`assets/…`、`style.css`）用相对路径即可，
因为官网固定从 `/` 进入，不存在层级歧义。

`og:image` / `og:url` / `canonical` 必须是**完整绝对 URL**，
社交平台爬取时只给 origin，相对路径会导致分享卡片无图。

重新生成官网素材：

```bash
# 从 children_drawing 工程的 marketing/raw/ 复制并压缩
# ⚠️ iPhone 首页图曾出现空白帧(pixel sd=0)，必须先校验再入库
python3 -c "
from PIL import Image
im = Image.open('raw.png').convert('L')
px = list(im.getdata()); m = sum(px)/len(px)
print('sd =', (sum((v-m)**2 for v in px[::37])/len(px[::37]))**0.5)
"
# sd < 3 说明是空白废图
```

### 法务站页面

由 `build_legal_site.py` 生成，**不要手改生成物**：

```bash
# ARB 是唯一内容源，在 Flutter 工程里
python3 tool/shots/build_legal_site.py --out . \
        --arb /Users/bot/Documents/App/children_drawing/l10n
```

脚本自带自检（非法 UTF-8 字节、U+FFFD 替换字符、占位符未替换）。
改内容请改脚本里的文案源；改链接请改脚本里的模板（不要改生成物）。

## 验收

改动后跑一次全站爬链，确保没有死链：

```bash
python3 -m http.server 8898 &
# 遍历所有 .html 的 href/src，逐个请求，应全部 200
kill %1
```

当前基线：**18 个页面 / 137 条链接，全部 200**（含从无尾斜杠 URL 进入的场景）。

官网门禁也要跑：
```bash
python3 tool/test_site_facts.py
```

## 部署（Cloudflare Pages）

本仓库是纯静态站，无构建步骤 —— 把**仓库根目录**直接作为 Pages 输出目录即可
（`app/` 会被当作静态资源一并发布）。

### wrangler CLI

```bash
wrangler login
wrangler pages deploy . --project-name=drawing-privacy --branch=main
```

### Dashboard

1. Workers & Pages → Create application → Pages → **Upload assets**
2. Project name: `drawing-privacy`
3. 拖拽仓库根目录内容上传
4. 部署后得到 `https://drawing-privacy.pages.dev`

### 接到自定义域

本项目正式域名：**`https://drawing-privacy.pages.dev`**

| URL | 指向 |
|---|---|
| `https://drawing-privacy.pages.dev/` | 产品官网 ← `marketingUrl` |
| `https://drawing-privacy.pages.dev/support/` | 支持门户 ← `supportUrl` |
| `https://drawing-privacy.pages.dev/privacy/zh-Hans.html` | 隐私政策 ← `privacyPolicyUrl` |
| `https://drawing-privacy.pages.dev/terms/zh-Hans.html` | 服务条款 |

部署后需回填 ASC。**当前 ASC 状态全是错的，必须改：**

| ASC 字段 | 当前值 | 应改为 |
|---|---|---|
| `appInfoLocalizations.supportUrl` | `null`（7 个 locale 全空） | `https://drawing-privacy.pages.dev/support/<locale>.html` |
| `appInfoLocalizations.privacyPolicyUrl` | `s.orzjun.com/.../baby_stick_figure_service_protocol.html`（原 App 遗留，正文写的是「服务协议」且含账号密码，本 App 无账号系统） | `https://drawing-privacy.pages.dev/privacy/<locale>.html` |
| `appStoreVersionLocalizations.supportUrl` | `https://www.facebook.com/Jingqi-103004027902475`（遗留） | 同上 |
| `appStoreVersionLocalizations.privacyPolicyUrl` | `null` | 同上 |
| `appInfoLocalizations.marketingUrl` | `null` | `https://drawing-privacy.pages.dev/` |

⚠️ 注意 ASC 有**两套** URL 字段：`appInfoLocalizations`（App 级）与
`appStoreVersionLocalizations`（版本级），**都要填**，只填一套审核仍会看到旧值。

⚠️ 关键词里的儿童定位词（`兒童畫`/`親子`/`子供`/`아이`）也要同步清掉。

## 内容合规约束（修改前必读）

本产品是**全年龄绘画工具，不是儿童专属 App**。文案改动必须保持：

- 不得表述为面向儿童 / 儿童专用；
- 不得出现 COPPA 条款；
- 不得暗示收集个人信息（本 App 无账号、纯本机存储）；
- 未成年人条款只能写「可在监护人陪同下使用」，不得写成目标用户群；
- 不得写「云同步」「去广告」等未实现的描述。

⚠️ 关键词与描述里的儿童定位词（如 `儿童画`、`親子`、`子供`、`아이`）
会被判定为 Kids 类目倾向，连带影响 Category 与年龄分级审核。

## 相关仓库

| 仓库 | 内容 |
|---|---|
| `ningwhy/drawing` | Flutter 源码（不部署） |
| `ningwhy/drawing-privacy` | 本仓库 —— 官网 + 法务站（部署至 CF） |