#!/usr/bin/env python3
"""
analyze-short-video 初稿 vs 用户微调稿 差异分析器。

用法：
  python diff_draft.py <初稿.txt> <用户微调.txt>
  python diff_draft.py --raw <初稿.txt> <用户微调.txt>    # 只输出行级 diff

输出：
  1) 行级 unified diff（- 初稿 / + 微调）
  2) 量化指标前后对比（字数/句数/平均句长/问号/感叹号/语气词/emoji）
  3) 微调新增/删除的句子，便于逐维度归因"用户改了什么"
"""
import sys
import re
import difflib


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def split_sents(t):
    return [s.strip() for s in re.split(r'(?<=[。！？；])', t) if s.strip()]


def metrics_full(t):
    ch = len(re.sub(r'\s', '', t))
    sents = split_sents(t)
    avg = round(ch / len(sents), 1) if sents else 0
    return {
        "字数": ch,
        "句数": len(sents),
        "平均句长": avg,
        "问号": len(re.findall(r'[？?]', t)),
        "感叹号": len(re.findall(r'[！!]', t)),
        "语气词(啊嘛呢哈吧啦)": len(re.findall(r'[啊嘛呢哈吧啦]', t)),
        "emoji": len(re.findall(r'[\U0001F000-\U0001FAFF\u2600-\u27BF]', t)),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    raw = '--raw' in sys.argv
    if len(args) < 2:
        print("用法: python diff_draft.py <初稿> <微调稿> [--raw]")
        return
    a = read(args[0]); b = read(args[1])
    al = a.splitlines(); bl = b.splitlines()

    print("=" * 70)
    print("行级 diff（- 初稿 / + 用户微调）")
    print("=" * 70)
    for line in difflib.unified_diff(al, bl, fromfile=args[0], tofile=args[1], lineterm='', n=1):
        print(line)

    if raw:
        return

    print("\n" + "=" * 70)
    print("量化指标对比")
    print("=" * 70)
    ma, mb = metrics_full(a), metrics_full(b)
    print(f"{'指标':<16}{'初稿':>8}{'微调':>8}{'变化':>8}")
    for k in ma:
        d = mb[k] - ma[k]
        d = round(d, 1) if isinstance(d, float) else d
        print(f"{k:<16}{ma[k]:>8}{mb[k]:>8}{d:>8}")

    print("\n" + "=" * 70)
    print("改了什么（供逐维度归因偏好）")
    print("=" * 70)
    sa = split_sents(a); sb = split_sents(b)
    print("--- 用户微调 新增/改动的句子 ---")
    for s in sb:
        if s not in a:
            print("  +", s[:60])
    print("--- 初稿被 删除/改写的句子 ---")
    for s in sa:
        if s not in b:
            print("  -", s[:60])


if __name__ == "__main__":
    main()
