#!/usr/bin/env python3
"""
投稿画像テンプレート renderer
JSON の内容を流し込んで X / Instagram 用の PNG を書き出す。
フォント: Zen Maru Gothic (SIL Open Font License / 商用利用可)
"""

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/tmp"
F_BLACK = f"{FONT_DIR}/zmg.ttf"              # Bold
F_MED = f"{FONT_DIR}/ZenMaruGothic-Medium.ttf"
F_REG = f"{FONT_DIR}/ZenMaruGothic-Regular.ttf"

# ── テーマ（ジャンルごとに色だけ差し替える）
THEMES = {
    "katakana": {
        "bg": "#FFF6EC", "card": "#FFFFFF", "accent": "#E8833A",
        "accent_soft": "#FBE3CE", "ink": "#3A3226", "sub": "#8C7B67",
    },
    "keiyaku": {
        "bg": "#EEF4F8", "card": "#FFFFFF", "accent": "#2F6E9E",
        "accent_soft": "#D3E4F0", "ink": "#22303A", "sub": "#6B808E",
    },
}


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap_jp(draw, text, fnt, max_w):
    """日本語用の文字単位折り返し（禁則の簡易処理つき）"""
    NG_HEAD = "、。」）,.!?！？ー"
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=fnt) > max_w and cur:
            if ch in NG_HEAD:      # 行頭にできない文字はぶら下げる
                lines.append(trial)
                cur = ""
            else:
                lines.append(cur)
                cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_block(draw, text, fnt, x, y, max_w, fill, leading=1.5, center=False):
    lines = wrap_jp(draw, text, fnt, max_w)
    lh = int(fnt.size * leading)
    for i, ln in enumerate(lines):
        px = x + (max_w - draw.textlength(ln, font=fnt)) / 2 if center else x
        draw.text((px, y + i * lh), ln, font=fnt, fill=fill)
    return y + len(lines) * lh


def face(draw, cx, cy, r, color, ink):
    """やわらかい顔アイコン（挿絵がわり）"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    ey, ex, er = cy - r * 0.12, r * 0.34, r * 0.11
    for s in (-1, 1):
        draw.ellipse([cx + s * ex - er, ey - er * 1.3,
                      cx + s * ex + er, ey + er * 1.3], fill=ink)
    draw.arc([cx - r * 0.34, cy + r * 0.02, cx + r * 0.34, cy + r * 0.5],
             start=10, end=170, fill=ink, width=max(3, int(r * 0.09)))
    for s in (-1, 1):   # ほっぺ
        draw.ellipse([cx + s * r * 0.62 - r * 0.13, cy + r * 0.08,
                      cx + s * r * 0.62 + r * 0.13, cy + r * 0.3],
                     fill="#F6B9A0")


def render(spec, size=(1080, 1350), out="card.png"):
    th = THEMES[spec["theme"]]
    W, H = size
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    s = W / 1080.0   # スケール係数

    # 背景の飾り円
    d.ellipse([-W * 0.18, -H * 0.10, W * 0.34, H * 0.16], fill=th["accent_soft"])
    d.ellipse([W * 0.74, H * 0.86, W * 1.22, H * 1.14], fill=th["accent_soft"])

    M = int(70 * s)
    card_t, card_b = int(H * 0.135), int(H * 0.845)
    d.rounded_rectangle([M, card_t, W - M, card_b], radius=int(44 * s),
                        fill=th["card"])

    inner = M + int(56 * s)
    maxw = W - inner * 2
    y = card_t + int(56 * s)

    # ラベル
    f_label = font(F_BLACK, int(30 * s))
    lw = d.textlength(spec["label"], font=f_label)
    d.rounded_rectangle([inner, y, inner + lw + 40 * s, y + 52 * s],
                        radius=int(26 * s), fill=th["accent"])
    d.text((inner + 20 * s, y + 9 * s), spec["label"], font=f_label, fill="#FFFFFF")
    y += int(96 * s)

    # 見出し語
    if spec.get("reading"):
        d.text((inner, y), spec["reading"], font=font(F_MED, int(26 * s)),
               fill=th["sub"])
        y += int(38 * s)
    y = draw_block(d, spec["term"], font(F_BLACK, int(84 * s)),
                   inner, y, maxw, th["ink"], leading=1.22)
    y += int(26 * s)

    # 矢印
    ax = inner + int(8 * s)
    d.line([ax, y + 16 * s, ax, y + 54 * s], fill=th["accent"], width=int(8 * s))
    d.polygon([(ax - 18 * s, y + 50 * s), (ax + 18 * s, y + 50 * s),
               (ax, y + 82 * s)], fill=th["accent"])
    y += int(104 * s)

    # 言い換え／やさしい訳
    y = draw_block(d, spec["answer"], font(F_BLACK, int(62 * s)),
                   inner, y, maxw, th["accent"], leading=1.3)
    y += int(34 * s)

    # 補足（カード内に収まるよう文字サイズを自動調整）
    d.line([inner, y, inner + maxw, y], fill=th["accent_soft"], width=int(4 * s))
    y += int(30 * s)
    avail = (card_b - int(30 * s)) - y
    nw = int(maxw * 0.78)
    for size in range(int(34 * s), int(20 * s), -1):
        fnt = font(F_REG, size)
        lh = int(size * 1.62)
        if len(wrap_jp(d, spec["note"], fnt, nw)) * lh <= avail:
            break
    draw_block(d, spec["note"], fnt, inner, y, nw, th["sub"], leading=1.62)

    face(d, W - M - int(96 * s), card_b - int(104 * s), int(62 * s),
         th["accent_soft"], th["ink"])

    # フッター
    f_foot = font(F_MED, int(30 * s))
    fw = d.textlength(spec["footer"], font=f_foot)
    d.text(((W - fw) / 2, card_b + int(38 * s)), spec["footer"],
           font=f_foot, fill=th["sub"])

    img.save(out, quality=95)
    return out


if __name__ == "__main__":
    import json
    import sys
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    render(spec, out=sys.argv[2] if len(sys.argv) > 2 else "card.png")
