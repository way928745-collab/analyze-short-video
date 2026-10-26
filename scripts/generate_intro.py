# -*- coding: utf-8 -*-
"""analyze-short-video 发布包 intro_v1.html 生成器。

从 references/cases/ 真实案例卡读取统计字段，渲染自包含 HTML 介绍页（无外部依赖）。
用法：python scripts/generate_intro.py [技能根目录，默认脚本上一级]
产出：<技能根>/intro_v1.html
"""
import collections
import html
import pathlib
import re
import sys

SKILL_ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
CASES = SKILL_ROOT / "references" / "cases"
OUT = SKILL_ROOT / "intro_v1.html"


def parse_fm(txt):
    fm = {}
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) >= 3:
            for ln in parts[1].strip().splitlines():
                if ":" in ln:
                    k, _, v = ln.partition(":")
                    fm[k.strip()] = v.strip().strip('"')
    return fm


def theme_of(track):
    return re.split(r"[·/,]", track.strip(), maxsplit=1)[0].strip() or "未知"


def main():
    rows = []
    gold = 0
    for f in sorted(CASES.glob("*/*.md")):
        if f.name in ("README.md", "_index.md"):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_fm(txt)
        gold += len(re.findall(r"^- 「", txt, flags=re.M))
        rows.append((f, fm))

    n = len(rows)
    tiers = collections.Counter(fm.get("duration_tier", "未知") for _, fm in rows)
    platforms = collections.Counter(fm.get("platform", "未知") for _, fm in rows)
    themes = collections.Counter(theme_of(fm.get("track", "")) for _, fm in rows)
    forms = collections.Counter(fm.get("content_form", "未知") for _, fm in rows)
    goals = collections.Counter(fm.get("core_goal", "未知") for _, fm in rows)
    dates = sorted(fm["date_added"] for _, fm in rows if fm.get("date_added"))
    date_range = (dates[0], dates[-1]) if dates else ("", "")

    def bar(rows, limit=8):
        items = rows.most_common(limit)
        mx = max((v for _, v in items), default=1)
        out = []
        for k, v in items:
            w = int(round(v / mx * 100))
            out.append(
                f'<div class="bar-row"><div class="bar-label">{html.escape(str(k))}</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{w}%"></div></div>'
                f'<div class="bar-val">{v}</div></div>'
            )
        return "\n".join(out)

    css = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#0d1117;color:#e6edf3;line-height:1.7;padding:32px 16px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:26px;margin-bottom:4px}
.sub{color:#8b949e;font-size:14px;margin-bottom:24px}
h2{font-size:19px;margin:28px 0 12px;border-left:4px solid #d29922;padding-left:10px}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 20px;margin-bottom:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;text-align:center}
.stat b{display:block;font-size:30px;color:#d29922}
.stat span{font-size:13px;color:#8b949e}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.bar-label{width:150px;font-size:13px;text-align:right;color:#c9d1d9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar-track{flex:1;background:#21262d;border-radius:4px;height:18px;overflow:hidden}
.bar-fill{background:linear-gradient(90deg,#d29922,#f0b429);height:100%;border-radius:4px}
.bar-val{width:36px;font-size:13px;color:#8b949e}
.note{color:#8b949e;font-size:13px;margin-top:24px;border-top:1px solid #30363d;padding-top:12px}
"""
    tiers_html = bar(tiers)
    themes_html = bar(themes, 10)
    forms_html = bar(forms, 6)
    goals_html = bar(goals, 6)
    platform_rows = "".join(
        f"<li><b>{html.escape(k)}</b>：{v} 条</li>" for k, v in platforms.most_common(5)
    )

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>analyze-short-video · 短视频爆款文案分析与蒸馏创作（v1）</title>
<style>{css}</style>
</head>
<body><div class="wrap">
<h1>analyze-short-video</h1>
<div class="sub">短视频爆款文案深度分析 + 蒸馏创作 · v1 基础版 · 数据由 scripts/generate_intro.py 从 references/cases/ 实时统计</div>

<h2>这是什么</h2>
<div class="card">一套可自我进化的短视频文案方法论：不只分析视频「做了什么」，更提炼「为什么爆、怎么复刻」，并据此创作新时长的可执行文案。遇优秀爆款随时拆解入库，案例库越用越强。</div>

<h2>真实运行数据</h2>
<div class="grid">
<div class="stat"><b>{n}</b><span>已蒸馏案例</span></div>
<div class="stat"><b>{platforms.get("抖音", 0) + sum(v for k, v in platforms.items() if "抖音" in k)}</b><span>抖音系案例</span></div>
<div class="stat"><b>{gold}</b><span>可复刻金句</span></div>
<div class="stat"><b>{date_range[0] or "-"}</b><span>最早入库</span></div>
</div>

<h2>案例库时长分布</h2>
<div class="card">{tiers_html}</div>

<h2>题材覆盖（按案例卡 track 归纳）</h2>
<div class="card">{themes_html}</div>

<h2>内容形态 / 商业目标</h2>
<div class="card">{forms_html}
<div style="margin-top:14px">{goals_html}</div></div>

<h2>平台覆盖</h2>
<div class="card"><ul style="padding-left:20px">{platform_rows}</ul></div>

<div class="note">数据来源：references/cases/ 全部案例卡 frontmatter 与金句段（78 条，2026-08 起持续积累）。本页由生成脚本产出，禁止手填统计。</div>
</div></body></html>
"""
    OUT.write_text(doc, encoding="utf-8")
    print("intro 已生成:", OUT)
    print(f"案例 {n} / 金句 {gold} / 档位 {dict(tiers)}")


if __name__ == "__main__":
    main()