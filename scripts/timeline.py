#!/usr/bin/env python3
"""
analyze-short-video 时间轴工具：用 .json 的字级时间戳算精确秒位。

用法：
  python timeline.py sentences <json路径> [--max N]      # 输出句子级时间轴 [秒位] 文本
  python timeline.py locate   <json路径> <短语>          # 返回该短语的起始秒位
  python timeline.py words    <json路径> [--from S]      # 按词输出，检验对齐
"""
import json
import re
import sys
import argparse


def build(d):
    words = d.get("words") or []
    offsets, cs = [], 0
    for w in words:
        t = w.get("word", "")
        offsets.append((cs, cs + len(t), (w.get("start", 0) or 0) / 1000.0))
        cs += len(t)
    return words, offsets, d.get("text", ""), cs


def sec_of_prefix(offsets, idx, end):
    """返回覆盖 [idx,end) 的词起始秒。"""
    for o_s, o_e, t in offsets:
        if o_s <= idx < o_e or (o_s < end and idx < end and end <= o_e) or (o_s <= idx and o_e >= end):
            return t
    return None


def sentences_mode(path, max_n):
    d = json.loads(open(path, encoding="utf-8").read())
    words, offsets, text, cs = build(d)
    # 用标点切句，但保留精确字符位置
    parts = list(re.finditer(r"[^。！？\n]{1,120}[。！？]?", text))
    out = []
    for m in parts:
        s, e = m.start(), m.end()
        if s >= len(text):
            continue
        seg = text[s:e].strip()
        if not seg:
            continue
        sec = sec_of_prefix(offsets, s, e)
        out.append((round(sec, 1) if sec is not None else None, seg))
    if max_n:
        out = out[:max_n]
    for sec, seg in out:
        mark = f"{sec:6.1f}s" if sec is not None else "   ?  "
        print(f"{mark} | {seg}")


def locate_mode(path, phrase):
    d = json.loads(open(path, encoding="utf-8").read())
    words, offsets, text, cs = build(d)
    idx = text.find(phrase)
    if idx < 0:
        print(f"NOT_FOUND: {phrase!r}")
        return
    sec = sec_of_prefix(offsets, idx, idx + len(phrase))
    print(f"{phrase!r} -> {sec:.1f}s" if sec is not None else f"{phrase!r} -> (无词级时间)")


def words_mode(path, from_sec=0.0):
    d = json.loads(open(path, encoding="utf-8").read())
    words, _, _, _ = build(d)
    for w in words:
        s = (w.get("start", 0) or 0) / 1000.0
        if s >= from_sec:
            print(f"{s:7.2f}s | {w.get('word', '')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    c1 = sub.add_parser("sentences")
    c1.add_argument("path")
    c1.add_argument("--max", type=int, default=0)

    c2 = sub.add_parser("locate")
    c2.add_argument("path")
    c2.add_argument("phrase")

    c3 = sub.add_parser("words")
    c3.add_argument("path")
    c3.add_argument("--from", type=float, default=0.0, dest="frm")

    a = ap.parse_args()
    if a.cmd == "sentences":
        sentences_mode(a.path, a.max)
    elif a.cmd == "locate":
        locate_mode(a.path, a.phrase)
    elif a.cmd == "words":
        words_mode(a.path, a.frm)


if __name__ == "__main__":
    main()
