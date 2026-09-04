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
