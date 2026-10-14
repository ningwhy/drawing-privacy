# drawing-privacy

简笔画涂鸦板（Drawing Board）的**官网 + 法务与支持静态站**，整站部署到 Cloudflare Pages。

| 路径 | 内容 | ASC 对应字段 |
|---|---|---|
| `/app/` | 产品介绍官网 | `marketingUrl` |
| `/` | 门户页（官网入口 + 五语种法务导航） | `supportUrl` |
| `/privacy/<locale>.html` | 隐私政策 | `privacyPolicyUrl` |
| `/terms/<locale>.html` | 服务条款 | App 内链接 |
| `/<locale>.html` | 支持页 | — |

`locale` ∈ `zh-Hans` · `zh-Hant` · `en` · `ja` · `ko`

## 文件结构

```
index.html              门户页 ← supportUrl 指向这里
app/                    产品介绍官网（官网唯一手写源）
  index.html
  style.css
  assets/icon.png       App 图标
  assets/shots/*.png    真实模拟器截图（非伪造 UI）
404.html                未找到页
en|zh-Hans|zh-Hant|ja|ko.html   支持页各语种
privacy/<locale>.html   隐私政策（生成物）
terms/<locale>.html     服务条款（生成物）
_headers                Cloudflare Pages 安全响应头
tool/shots/build_legal_site.py   法务站生成器
```

## 构建

### 官网页面

`app/` 下三个文件是**手写源**，直接改即可：零外部资源、纯 HTML/CSS。

产品图为 `App Store 截图流水线`产出的**真实模拟器截图**（缩放到 900px 宽、已去 alpha）。
⚠️ 禁止用 CSS/HTML 伪造 App UI。

重新生成官网素材：

```bash
# 从 children_drawing 工程的 marketing/raw/ 复制并压缩
# iPhone 首页图曾出现空白帧(pixel sd=0)，必须先校验再入库
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
python3 tool/shots/build_legal_site.py
```

脚本自带自检（非法 UTF-8 字节、U+FFFD 替换字符、占位符未替换）。
改内容请改脚本里的文案源。

## 验收

改动后跑一次全站爬链，确保没有死链：

```bash
python3 -m http.server 8898 &
# 遍历所有 .html 的 href/src，逐个请求，应全部 200
kill %1
```

当前基线：**18 个页面 / 130 条链接，全部 200**。

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

官网与法务站同域时，`supportUrl` 填 `https://<域名>/`，
`privacyPolicyUrl` 填 `https://<域名>/privacy/zh-Hans.html`，
`marketingUrl` 填 `https://<域名>/app/`。

部署后需回填 ASC（当前全部为 null 或指向已失效的 Facebook 主页）。

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