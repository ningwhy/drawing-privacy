#!/usr/bin/env python3
"""官网事实的**单一真源** —— 从 children_drawing 的 Dart 源码派生。

## 为什么官网也需要这个文件

2026-10-16 实测：App Store 上已上架的 1.1 文案写「62 张简笔画」，
而代码真源 `kSketchLibraryCount` 早已是 72。那是商店侧的漂移（已修）。

但同一天查官网时发现**同一个漂移在官网也存在**：`index.html` 有 9 处写死
「62 张」。两个仓库各有一份互不知情的副本，没有任何东西在看住它。

官网是 `marketingUrl`，审核员和用户都会看 —— 写错同样是 Guideline 2.3。

## 解法

不硬编码数字，文案里写 `{n}`，构建时由本脚本替换。
`build_site.py` 调用本模块；`test_site_facts.py` 负责对拍与证伪。

## 派生方式（都是静态解析，不执行 Dart）

| 事实 | 源文件 | 解析对象 |
|---|---|---|
| 线稿总数 | `lib/core/data/sketches.g.dart` | `_library` 顶层列表条目数 |
| 免费张数 | `lib/core/data/feature_gate.dart` | `kFreeSketchCount = N` |
| 笔刷种数 | `lib/features/drawing/brushes.dart` | `BrushRegistry.available` 的列表字面量 |
| 调色板色数 | `lib/core/theme/palette.dart` | `kCrayonPalette` 的列表字面量 |

⚠️ **静态解析的失效模式是「静默返回 0 或 1」**，而不是报错。
所以每个解析函数都要求「必须匹配到」并在失败时 `raise`，
并且 `test_site_facts.py` 会与 Dart 运行时的真值对拍。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# 官网工程自己的目录
SITE_ROOT = Path(__file__).resolve().parent.parent

# 跨仓库引用的 Flutter 工程。⚠️ 路径在 CI / 别的机器上可能不存在，
# 此时**不静默降级**，而是抛错 —— 宁可构建失败，也不要推一个数字错的产品页。
FLUTTER_REPO = Path(
    os.environ.get("DRAWING_FLUTTER_REPO", "/Users/bot/Documents/App/children_drawing")
)


class FactsUnavailable(RuntimeError):
    """源码不可达或结构变了。**绝不返回猜测值。**"""


def _require(path: Path) -> str:
    if not path.exists():
        raise FactsUnavailable(
            f"❌ 找不到 {path}\n"
            f"   官网的事实数字必须从 children_drawing 的 Dart 源码派生。\n"
            f"   设环境变量 DRAWING_FLUTTER_REPO 指向该工程，或修本文件的默认路径。\n"
            f"   ⚠️ **绝不要在这里退回硬编码数字** —— 那正是 62 → 72 漂移的根因。"
        )
    return path.read_text(encoding="utf-8")


def _count_list_items(src: str, decl_re: str, what: str) -> int:
    """数一个顶层列表字面量的条目数。

    ⚠️ 只认「一行一个条目、尾随逗号」的生成物格式。
    生成物格式变了就应该报错，而不是继续猜。
    """
    m = re.search(decl_re, src, re.S)
    if not m:
        raise FactsUnavailable(
            f"❌ 没能从源码解析{what}。\n"
            f"   正则：{decl_re}\n"
            f"   如果源文件结构变了（改了变量名 / 改成展开运算符 / 改了分行方式），"
            f"这里必须同步改。**静默返回 0 会让产品页写出「0 张线稿」。**"
        )
    items = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
    if not items:
        raise FactsUnavailable(f"❌ 解析到{what}是空列表 —— 源结构一定变了。")
    return len(items)


def sketch_total() -> int:
    """内置简笔画线稿总数（= Dart 侧 kSketchLibraryCount）。"""
    src = _require(FLUTTER_REPO / "lib/core/data/sketches.g.dart")
    return _count_list_items(
        src,
        r"final\s+List<\s*\w+\s*>\s+_\w+\s*=\s*\[(.*?)\n\];",
        "线稿列表",
    )


def sketch_free() -> int:
    """免费可用张数（= Dart 侧 kFreeSketchCount）。"""
    src = _require(FLUTTER_REPO / "lib/core/data/feature_gate.dart")
    m = re.search(r"const\s+int\s+kFreeSketchCount\s*=\s*(\d+)\s*;", src)
    if not m:
        raise FactsUnavailable(
            "❌ 没能从 feature_gate.dart 解析 kFreeSketchCount。\n"
            "   如果它不再是 `const int` 字面量（例如改成了 getter），这里必须同步改。"
        )
    return int(m.group(1))


def sketch_vip() -> int:
    """需 VIP 的线稿数（= sketch_total - sketch_free）。"""
    return max(0, sketch_total() - sketch_free())


def brush_count() -> int:
    """笔刷种数（= Dart 侧 BrushRegistry.available.length）。"""
    src = _require(FLUTTER_REPO / "lib/features/drawing/brushes.dart")
    # `static List<int> get available => const [ ... ];`
    return _count_list_items(
        src,
        r"static\s+List<int>\s+get\s+available\s*=>\s*const\s*\[(.*?)\n\s*\];",
        "笔刷列表",
    )


def crayon_colors() -> int:
    """调色板颜色数（= Dart 侧 kCrayonPalette.length）。"""
    src = _require(FLUTTER_REPO / "lib/core/theme/palette.dart")
    return _count_list_items(
        src,
        r"const\s+List<CrayonColor>\s+kCrayonPalette\s*=\s*\[(.*?)\n\];",
        "调色板",
    )


def all_facts() -> dict[str, int]:
    """一次性取全部事实。任一项不可用即抛错，不返回部分结果。"""
    total = sketch_total()
    free = sketch_free()
    return {
        "sketchTotal": total,
        "sketchFree": free,
        "sketchVip": max(0, total - free),
        "brushCount": brush_count(),
        "colorCount": crayon_colors(),
    }


def render(template: str) -> str:
    """把 `{sketchTotal}` 这类占位符替换成真值。

    ⚠️ 用 `str.format` 会和文案里的花括号打架。
    这里只替换已知 key，其余花括号原样保留。
    """
    facts = all_facts()
    out = template
    for k, v in facts.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def unfilled_placeholders(template: str) -> list[str]:
    """返回还没被替换的 `{key}` 占位符。

    ✅ 判据方向：**只认本模块已知的 key**。
    官网文案的 `{n}` 之类（来自商店脚本的旧约定）不算漏，
    但 `{sketchTotal}` 没被替换就是真 bug。
    """
    return sorted(set(re.findall(r"\{(\w+)\}", template)) & set(all_facts().keys()))


if __name__ == "__main__":
    for k, v in all_facts().items():
        print(f"  {k:14} = {v}")
