#!/usr/bin/env python3
"""Genera iconos PWA simples (gradiente violeta GymVe). Requiere: pip install pillow."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Instala Pillow: pip install pillow")

OUT = Path(__file__).resolve().parents[1] / "app" / "static"
def make(size: int) -> None:
    img = Image.new("RGB", (size, size), (0x7C, 0x3A, 0xED))
    draw_bg = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(0x7C + (0xF9 - 0x7C) * t * 0.6)
        g = int(0x3A + (0x73 - 0x3A) * t * 0.5)
        b = int(0xED + (0x16 - 0xED) * t * 0.4)
        draw_bg.line([(0, y), (size, y)], fill=(r, g, b))
    draw = ImageDraw.Draw(img)
    text = "GV"
    font_size = max(size // 3, 12)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 2), text, fill=(255, 255, 255), font=font)
    img.save(OUT / f"icon-{size}.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make(192)
    make(512)
    print("Iconos escritos en", OUT)


if __name__ == "__main__":
    main()
