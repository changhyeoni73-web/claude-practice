"""썸네일 이미지 생성 → build/thumbnail.png (1080x1920)

구성: 어두운 서버실 배경 / 상단 제목 / 가운데 'AMERICA'에서 A와 I가 떨어져 나가는 그림 / 하단 태그
사용: python thumbnail.py   (Pillow 필요)
"""
import json, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont

ROOT = pathlib.Path(__file__).parent
B = ROOT / "build"; B.mkdir(exist_ok=True)
W, H = 1080, 1920
BLACK = ROOT / "assets/fonts/Pretendard-Black.otf"
CFG = json.load(open(ROOT / "script.json")).get("thumbnail", {})
TITLE1 = CFG.get("title1", "미국,")
TITLE2 = CFG.get("title2", "AI를 버렸다!")
TAG = CFG.get("tag", "주민투표 41곳, 결과는?")
BG_CLIP, BG_AT = CFG.get("bg_clip", "server"), CFG.get("bg_at", 8)
LIME, RED, WHITE = (212, 255, 58), (255, 59, 48), (255, 255, 255)


def font(size):
    return ImageFont.truetype(str(BLACK), size)


def background():
    png = B / "thumb_bg.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(BG_AT), "-i", str(ROOT / f"assets/clips/{BG_CLIP}.mp4"),
                    "-frames:v", "1", str(png)], check=True)
    im = Image.open(png).convert("RGB")
    s = max(W / im.width, H / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(6))
    im = ImageEnhance.Brightness(im).enhance(0.32)
    # 아래쪽에서 올라오는 붉은 빛
    glow = Image.new("RGB", (W, H), RED); mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for i in range(700):
        md.line([(0, H - i), (W, H - i)], fill=int(110 * (1 - i / 700) ** 2))
    return Image.composite(glow, im, mask)


def text_center(d, y, text, size, fill, stroke=10):
    f = font(size); w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def letter(img, ch, x, y, size, fill, angle=0, alpha=255):
    """글자 하나를 회전시켜 붙이기 (x, y = 글자 왼쪽 위)."""
    f = font(size); box = f.getbbox(ch); w, h = box[2] + 40, box[3] + 40
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    td.text((20, 20), ch, font=f, fill=fill + (alpha,), stroke_width=8, stroke_fill=(0, 0, 0, alpha))
    tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(tile, (int(x - (tile.width - w) / 2), int(y - (tile.height - h) / 2)))


def main():
    img = background().convert("RGBA"); d = ImageDraw.Draw(img)
    # 상단 제목
    text_center(d, 230, TITLE1, 170, WHITE)
    # 둘째 줄: 'AI'만 빨간색, 나머지는 연두색 (떨어지는 빨간 A·I와 이어지게)
    f2 = font(190); head, rest = ("AI", TITLE2[2:]) if TITLE2.startswith("AI") else ("", TITLE2)
    x2 = (W - d.textlength(TITLE2, font=f2)) / 2
    d.text((x2, 430), head, font=f2, fill=RED, stroke_width=12, stroke_fill=(0, 0, 0))
    d.text((x2 + d.textlength(head, font=f2), 430), rest, font=f2, fill=LIME, stroke_width=12, stroke_fill=(0, 0, 0))

    # 가운데: AMERICA — A(첫 글자)와 I는 빨간색으로 아래로 떨어져 나감
    word, size, y0 = "AMERICA", 200, 900
    f = font(size); widths = [d.textlength(c, font=f) for c in word]
    x = (W - sum(widths) - 6 * 4) / 2
    drop = {0: (-28, 330), 4: (22, 380)}            # 글자 위치: (회전 각도, 떨어지는 거리)
    for i, ch in enumerate(word):
        if i in drop:
            ang, dy = drop[i]
            letter(img, ch, x - 20, y0 - 20, size, (255, 255, 255), alpha=45)   # 빠져나간 자리의 흐린 흔적
            for k, a in ((0.35, 50), (0.65, 90)):                              # 떨어지는 잔상
                letter(img, ch, x - 20, y0 - 20 + dy * k, size, RED, angle=ang * k, alpha=a)
            letter(img, ch, x - 20, y0 - 20 + dy, size, RED, angle=ang)
        else:
            letter(img, ch, x - 20, y0 - 20, size, WHITE)
        x += widths[i] + 4

    # 하단 태그 (빨간 박스)
    d = ImageDraw.Draw(img); tf = font(64); tw = d.textlength(TAG, font=tf)
    bx, by = (W - tw) / 2 - 36, 1520
    d.rounded_rectangle([bx, by, bx + tw + 72, by + 110], radius=18, fill=RED)
    d.text((bx + 36, by + 18), TAG, font=tf, fill=WHITE)

    out = B / "thumbnail.png"; img.convert("RGB").save(out); print("saved", out)


if __name__ == "__main__":
    main()
