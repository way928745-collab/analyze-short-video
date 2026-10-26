#!/usr/bin/env python3
"""
analyze-short-video 素材扫描与蒸馏进度工具。

扫 D:\\my_data\\downloaded_media\\{短视频,中视频,长视频}\\transcripts 里的三件套，
以及 D:\\my_data\\外来文案库 里的外来文案；读取 .json 的情感/时长/字数；
对照蒸馏进度清单，只列出"未蒸馏"项，支持把某一项标记为已蒸馏。

命令：
  python scan_unprocessed.py list [--tiers 短视频,中视频,长视频] [--manifest PATH] [--json]
  python scan_unprocessed.py mark <key> [--manifest PATH]

--json 时以纯 JSON 输出完整清单；默认输出人读表格。
"""
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

DEFAULT_BASE = Path(r"D:\my_data\downloaded_media")
DEFAULT_MANIFEST = Path(r"D:\my_data\蒸馏进度.json")
IMPORT_DIR = Path(r"D:\my_data\外来文案库")
TIER_DIRS = {"短视频": "短视频", "中视频": "中视频", "长视频": "长视频"}
# 外来文案库里作为说明/索引的文件不应当成文案源，按文件名 root 跳过
SKIP_STEMS = {"readme", "说明", "_index", "index", "目录", "使用说明", "readme.md"}


def load_manifest(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"updated": "", "distilled": {}}


def save_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_summary(jf: Path) -> dict:
    """读取 .json 的情感/实时长/字数；实时长用时间戳最大值推导(不可信 elapsed_sec)。"""
    try:
        d = json.loads(jf.read_text(encoding="utf-8"))
        return {
            "emotion": d.get("emotion", "?"),
            "duration_sec": _dur_from_json(d),
            "text_chars": len(d.get("text", "") or ""),
        }
    except Exception:
        return {"emotion": "?", "duration_sec": 0, "text_chars": 0}


def _dur_from_json(d: dict) -> float:
    """真实时长：优先 segments 最大结束时间，其次 words 最大 end，兜底 elapsed_sec。"""
    best = 0.0
    seg = d.get("segments") or []
    if seg:
        best = max((s[1] for s in seg if isinstance(s, (list, tuple)) and len(s) >= 2), default=0)
    if not best:
        wd = d.get("words") or []
        if wd:
            best = max((w.get("end", 0) for w in wd if isinstance(w, dict)), default=0)
    if best:
        return round(best / 1000.0, 1)
    try:
        return round(float(d.get("elapsed_sec", 0)), 1)
    except (TypeError, ValueError):
        return 0.0


def collect(base: Path, tiers) -> list:
    items = []
    for tier in tiers:
        td = base / TIER_DIRS[tier] / "transcripts"
        if not td.is_dir():
            continue
        for jf in sorted(td.glob("*.json")):
            key = f"{tier}/{jf.stem}"
            meta = read_json_summary(jf)
            items.append({
                "key": key, "tier": tier, "basename": jf.stem,
                "json": str(jf), "txt": str(jf.with_suffix(".txt")),
                "srt": str(jf.with_suffix(".srt")),
                **meta,
            })
    # 外来文案库
    imp = IMPORT_DIR
    if imp.is_dir():
        for f in sorted(imp.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".txt", ".md", ".json", ".srt", ".docx"):
                continue
            if f.stem.strip().lower() in SKIP_STEMS:
                continue
            key = f"外来/{f.stem}"
            meta = {"emotion": "?", "duration_sec": 0, "text_chars": 0}
            if f.suffix.lower() == ".json":
                meta = read_json_summary(f)
            elif f.suffix.lower() in (".txt", ".md"):
                try:
                    meta["text_chars"] = len(f.read_text(encoding="utf-8"))
                except Exception:
                    pass
            items.append({
                "key": key, "tier": "外来", "basename": f.stem,
                "json": "", "txt": str(f), "srt": "",
                **meta,
            })
    return items


def main():
    ap = argparse.ArgumentParser(description="analyze-short-video 素材扫描与蒸馏进度工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出未蒸馏的文案")
    p_list.add_argument("--tiers", default="", help="逗号分隔的时长域，默认全部")
    p_list.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p_list.add_argument("--json", action="store_true", help="纯 JSON 输出完整清单")

    p_mark = sub.add_parser("mark", help="把某项标记为已蒸馏")
    p_mark.add_argument("key", help="列表输出里的 key，例如 长视频/2026-08-05_xxx")
    p_mark.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)

    args = ap.parse_args()

    if args.cmd == "list":
        tiers = [t.strip() for t in args.tiers.split(",") if t.strip()] or list(TIER_DIRS)
        items = collect(DEFAULT_BASE, tiers)
        manifest = load_manifest(args.manifest)
        distilled = manifest.get("distilled", {})
        processed = [it for it in items if it["key"] in distilled]
        unprocessed = [it for it in items if it["key"] not in distilled]
        if args.json:
            print(json.dumps({
                "manifest": str(args.manifest),
                "total": len(items),
                "processed": len(processed),
                "unprocessed": unprocessed,
                "processed_keys": sorted(distilled.keys()),
            }, ensure_ascii=False, indent=2))
            return
        print(f"清单: {args.manifest}")
        print(f"素材总数 {len(items)} | 已蒸馏 {len(processed)} | 未蒸馏 {len(unprocessed)}")
        if not unprocessed:
            print("（没有未蒸馏的文案）")
            return
        print("\n=== 未蒸馏清单 ===")
        for it in unprocessed:
            print(f"[{it['tier']}] {it['basename']}")
            print(f"    情感={it['emotion']}  时长={it['duration_sec']}s  字数={it['text_chars']}  key={it['key']}")

    elif args.cmd == "mark":
        manifest = load_manifest(args.manifest)
        manifest.setdefault("distilled", {})[args.key] = {
            "ts": datetime.now().isoformat(timespec="seconds")
        }
        manifest["updated"] = datetime.now().isoformat(timespec="seconds")
        save_manifest(args.manifest, manifest)
        print(f"已标记: {args.key}")
        print(f"写入: {args.manifest}  (当前已蒸馏 {len(manifest['distilled'])} 项)")


if __name__ == "__main__":
    main()
