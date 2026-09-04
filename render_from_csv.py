#!/usr/bin/env python3
"""
公開CSVからカード画像を生成する

スプレッドシートを「ウェブに公開（CSV）」しておけば、認証なしで読める。
まだ画像が存在しない行だけを処理するので、何度実行しても無駄がない。

環境変数:
  SHEET_CSV_URL   ウェブに公開したCSVのURL
  ACCOUNT_HANDLE  画像下部に入れるアカウント名（省略時 @KumoAoiro）
"""

import csv
import hashlib
import io
import os
import sys
import urllib.request

from render_card import render

CARD_DIR = "docs/cards"

LABELS = {
    "katakana": ("カタカナ語、日本語で言うと？", "katakana"),
    "keiyaku": ("契約書のことば", "keiyaku"),
}


def make_slug(genre, term):
    """Code.gs の makeSlug と同じ規則"""
    h = hashlib.md5(f"{genre}_{term}".encode("utf-8")).hexdigest()
    return f"{genre}_{h[:10]}"


def fetch_rows(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def main():
    url = os.environ.get("SHEET_CSV_URL")
    if not url:
        print("SHEET_CSV_URL が設定されていません")
        sys.exit(1)

    handle = os.environ.get("ACCOUNT_HANDLE", "@KumoAoiro")
    os.makedirs(CARD_DIR, exist_ok=True)
    rows = fetch_rows(url)
    made = 0

    for row in rows:
        genre = (row.get("ジャンル") or "").strip()
        term = (row.get("見出し語") or "").strip()
        answer = (row.get("言い換え・訳") or "").strip()
        note = (row.get("補足") or "").strip()
        reading = (row.get("読み") or "").strip()

        if not (genre and term and answer):
            continue
        if genre not in LABELS:
            print(f"未知のジャンル '{genre}' を飛ばします（{term}）")
            continue

        slug = make_slug(genre, term)
        path = f"{CARD_DIR}/{slug}.png"
        if os.path.exists(path):
            continue

        label, theme = LABELS[genre]
        render({"theme": theme, "label": label, "term": term, "reading": reading,
                "answer": answer, "note": note, "footer": handle},
               size=(1080, 1080), out=path)
        print(f"rendered: {term} -> {slug}.png")
        made += 1

    print(f"{made}件の画像を生成しました" if made else "生成対象はありませんでした")


if __name__ == "__main__":
    main()
