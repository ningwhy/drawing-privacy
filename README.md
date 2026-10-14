# drawing-privacy

简笔画涂鸦板（Drawing Board）的**法务与支持静态站**源码。

App Store Connect 需要三个公开 URL，全部由本仓库构建的静态站提供：

| ASC 字段 | 路径 |
|---|---|
| `supportUrl` | `/` |
| `privacyPolicyUrl` | `/privacy/<locale>.html` |
| 服务条款（App 内链接） | `/terms/<locale>.html` |

`locale` ∈ `zh-Hans` · `zh-Hant` · `en` · `ja` · `ko`

## 构建

页面由 `build_legal_site.py` 生成，**不要手改生成物**：

```bash
python3 tool/shots/build_legal_site.py
```

脚本自带自检（非法 UTF-8 字节、U+FFFD 替换字符、占位符未替换），通过后输出到
`marketing/site/`。改内容请改脚本里的文案源。

## 部署（Cloudflare Pages）

本仓库是纯静态站，无构建步骤 —— 把仓库根目录直接作为 Pages 输出目录即可。

### wrangler CLI

```bash
wrangler login
wrangler pages deploy . --project-name=drawing-privacy --branch=main
```

### Dashboard（推荐用于首次部署）

1. Cloudflare Dashboard → Workers & Pages → Create application → Pages → Upload assets
2. Project name: `drawing-privacy`
3. 直接拖拽仓库根目录内容上传
4. 部署后得到 `https://drawing-privacy.pages.dev`

### API Token 方式（脚本）

```bash
export CLOUDFLARE_API_TOKEN='<Pages:Edit 权限的 token>'
python3 tool/shots/deploy_cf_pages.py \
    --dir . --account <ACCOUNT_ID> --project drawing-privacy
```

## 文件结构

```
index.html              支持页（语言选择入口）← supportUrl 指向这里
404.html                未找到页
en|zh-Hans|zh-Hant|ja|ko.html   支持页各语种
privacy/<locale>.html   隐私政策
terms/<locale>.html     服务条款
_headers                Cloudflare Pages 安全响应头
```

`_headers` 为 Pages 特有文件，Dashboard 上传时会作为静态资源保留但**只在 Pages
部署时生效**；wrangler CLI 同样识别。

## 内容合规约束（修改前必读）

本产品是**全年龄绘画工具，不是儿童专属 App**。文案改动必须保持：

- 不得表述为面向儿童 / 儿童专用；
- 不得出现 COPPA 条款；
- 不得暗示收集个人信息（本 App 无账号、纯本机存储）；
- 未成年人条款只能写"可在监护人陪同下使用"，不得写成目标用户群。

违反以上任一条会连带触发 App Store Connect 的 Category、年龄分级、隐私标签
审核问题。
