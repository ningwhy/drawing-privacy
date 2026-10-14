#!/usr/bin/env python3
"""
用 Cloudflare REST API 直接部署静态站到 Pages —— 不依赖 wrangler / npm。

为什么不用 wrangler：
  npm 装 wrangler 在本机网络极慢（registry 首包 >4min 未完成），
  而 Pages 的部署本质就是「建 deployment + 上传文件」两个 HTTP 调用，Python 足够。

流程（Cloudflare Pages 直传 API）：
  1. POST /accounts/{account}/pages/projects/{project}   建项目（已存在则 409，忽略）
  2. POST /accounts/{account}/pages/projects/{project}/deployments
     → 拿到 upload_url（形如 https://api.cloudflare.com/client/v4/.../pages/assets/check-missing）
  3. 对每个文件：POST {upload_url}/{filename}          上传（一次一个，20 个文件 20 次）
     → 返回 hash；missing 的是"该 deployment 需要但还没上传的"
  4. 校验：GET 站点 URL 抽查关键页面 200

Token 从环境变量 CLOUDFLARE_API_TOKEN 读，不落盘、不进 git。

用法：
  export CLOUDFLARE_API_TOKEN='xxx'
  python3 deploy_cf_pages.py --dir /tmp/cf_drawingboard_deploy \
      --account 971b4b89594129a947a13ff13c1d88c2 --project drawing-board-legal
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.cloudflare.com/client/v4"

# 这些是部署配置文件，不作为站点资源上传
SKIP_NAMES = {"wrangler.toml", "package.json", "package-lock.json", ".DS_Store"}


def call(method: str, url: str, token: str, body=None, raw=False, timeout=90):
    """调 Cloudflare API。返回 (status, parsed_json_or_bytes)。"""
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = r.read()
            if raw:
                return r.status, payload
            return r.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as e:
        payload = e.read()
        if raw:
            return e.code, payload
        try:
            return e.code, json.loads(payload)
        except Exception:
            return e.code, {"errors": [{"message": payload[:400].decode("utf-8", "replace")}]}
    except Exception as e:
        return 0, {"errors": [{"message": str(e)}]}


def die(msg: str, detail=None):
    print(f"!!! {msg}", file=sys.stderr)
    if detail:
        print(json.dumps(detail, ensure_ascii=False, indent=2)[:1600], file=sys.stderr)
    sys.exit(1)


def ensure_project(account: str, project: str, token: str):
    st, js = call("POST", f"{API}/accounts/{account}/pages/projects",
                  token, body={"name": project, "production_branch": "main"})
    if st in (200, 201):
        print(f"[ok] 项目已创建: {project}")
        return
    # 已存在是正常路径（409 / "project already exists"）
    txt = json.dumps(js, ensure_ascii=False)
    if st == 409 or "already exists" in txt.lower():
        print(f"[ok] 项目已存在: {project}")
        return
    die(f"创建项目失败 (HTTP {st})", js)


def collect_files(root: Path):
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.name in SKIP_NAMES or p.name.startswith("."):
            continue
        rel = p.relative_to(root).as_posix()
        out.append((rel, p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--account", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        die("未设置 CLOUDFLARE_API_TOKEN")

    # 0) 先验 Token
    st, js = call("GET", f"{API}/user/tokens/verify", token)
    if st != 200:
        die(f"Token 校验失败 (HTTP {st}) —— 权限或格式不对", js)
    print(f"[ok] Token 有效，状态: {js.get('result', {}).get('status')}")

    root = Path(args.dir).resolve()
    if not root.is_dir():
        die(f"目录不存在: {root}")
    files = collect_files(root)
    if not files:
        die(f"目录内没有可上传文件: {root}")
    print(f"[ok] 待上传 {len(files)} 个文件，共 "
          f"{sum(p.stat().st_size for _, p in files)/1024:.0f} KB")

    # 1) 确保项目存在
    ensure_project(args.account, args.project, token)

    # 2) 建 deployment，拿 upload_url
    manifest = {rel: hashlib.sha256(p.read_bytes()).hexdigest() for rel, p in files}
    st, js = call(
        "POST",
        f"{API}/accounts/{args.account}/pages/projects/{args.project}/deployments",
        token,
        body={
            "branch": args.branch,
            "commit_message": "Deploy legal/support site",
            "manifest": manifest,
        },
    )
    if st not in (200, 201):
        die(f"创建 deployment 失败 (HTTP {st})", js)
    result = js.get("result", {})
    upload_url = result.get("upload_url")
    deploy_url = result.get("url")
    deployment_id = result.get("id")
    if not upload_url:
        die("deployment 未返回 upload_url", js)
    print(f"[ok] deployment {deployment_id}")
    print(f"     upload_url = {upload_url[:96]}...")

    # 3) 逐个上传
    assets_base = upload_url.rstrip("/")
    uploaded = 0
    for rel, p in files:
        data = p.read_bytes()
        ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        url = f"{assets_base}/{rel}"
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": ctype,
            },
        )
        ok = False
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    body = json.loads(r.read() or b"{}")
                # check-missing 端点返回 {"result": [...], "success": true}
                if body.get("success", False):
                    ok = True
                    break
                die(f"上传 {rel} 返回失败", body)
            except urllib.error.HTTPError as e:
                payload = e.read()
                if e.code == 409:
                    # 该文件已存在（本 deployment 内），视为成功
                    ok = True
                    break
                if attempt == 3:
                    die(f"上传 {rel} 失败 (HTTP {e.code})",
                        payload[:400].decode("utf-8", "replace"))
                time.sleep(1.5 * attempt)
            except Exception as e:
                if attempt == 3:
                    die(f"上传 {rel} 异常: {e}")
                time.sleep(1.5 * attempt)
        uploaded += 1
        print(f"  [{uploaded}/{len(files)}] {rel}")

    print(f"\n[ok] 全部 {uploaded} 个文件已上传")
    print(f"     站点地址: {deploy_url}")

    # 4) 等部署生效并抽查（公开站点，无鉴权）
    if deploy_url:
        base = deploy_url.rstrip("/")
        checks = [
            "/", "/privacy/zh-Hans.html", "/terms/zh-Hans.html",
            "/privacy/en.html", "/terms/en.html", "/en.html", "/404-probe-xyz",
        ]
        print("\n等待部署生效，最多 90s …")
        import urllib.request as ur
        ok_paths, last = [], []
        for _ in range(30):
            time.sleep(3)
            results = []
            for path in checks:
                try:
                    req2 = ur.Request(f"{base}{path}", method="GET")
                    with ur.urlopen(req2, timeout=20) as r:
                        results.append((path, r.status))
                except urllib.error.HTTPError as e:
                    results.append((path, e.code))
                except Exception as e:
                    results.append((path, str(e)[:30]))
            last = results
            if all(s == 200 for _, s in results[:-1]):
                break
        print("\n抽查结果:")
        for path, s in last:
            note = ""
            if path == "/404-probe-xyz":
                note = "  (404 页应返回 404 或 200，取决于 CF 配置)"
            print(f"  {s}  {path}{note}")
        good = sum(1 for p, s in last[:-1] if s == 200)
        print(f"\n关键页面 {good}/{len(checks)-1} 返回 200")
        if good == len(checks) - 1:
            print(f"\n部署完成 ✅\n  supportUrl       = {base}/\n"
                  f"  privacyPolicyUrl = {base}/privacy/zh-Hans.html\n"
                  f"  termsUrl         = {base}/terms/zh-Hans.html")
            print("\nASC 里按语种填对应语言版本：")
            for loc, seg in [("zh-Hans", "zh-Hans"), ("zh-Hant", "zh-Hant"),
                             ("en", "en"), ("ja", "ja"), ("ko", "ko")]:
                print(f"  {loc:<8} privacy = {base}/privacy/{seg}.html")
        else:
            print("\n部分页面未就绪，稍后重试或查看 Cloudflare 控制台部署日志。")


if __name__ == "__main__":
    main()
