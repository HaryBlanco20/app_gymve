#!/usr/bin/env python3
"""Genera iconos PWA GymVe (gradiente aurora). Requiere: pip install pillow."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Instala Pillow: pip install pillow")

OUT = Path(__file__).resolve().parents[1] / "app" / "static"

# Violeta profundo → eléctrico → rosa
GRAD_TOP = (0x5B, 0x21, 0xB6)
GRAD_MID = (0x25, 0x63, 0xEB)
GRAD_BOTTOM = (0xEC, 0x48, 0x99)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def gradient_bg(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        if t < 0.5:
            u = t / 0.5
            r = lerp(GRAD_TOP[0], GRAD_MID[0], u)
            g = lerp(GRAD_TOP[1], GRAD_MID[1], u)
            b = lerp(GRAD_TOP[2], GRAD_MID[2], u)
        else:
            u = (t - 0.5) / 0.5
            r = lerp(GRAD_MID[0], GRAD_BOTTOM[0], u)
            g = lerp(GRAD_MID[1], GRAD_BOTTOM[1], u)
            b = lerp(GRAD_MID[2], GRAD_BOTTOM[2], u)
        for x in range(size):
            px[x, y] = (r, g, b)
    return img


def make(size: int) -> None:
    img = gradient_bg(size)
    draw = ImageDraw.Draw(img)
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        outline=(0xC4, 0xF0, 0x42),
        width=max(size // 32, 2),
    )
    text = "GV"
    font_size = max(size // 3, 12)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - 2),
        text,
        fill=(255, 255, 255),
        font=font,
    )
    img.save(OUT / f"icon-{size}.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make(192)
    make(512)
    print("Iconos escritos en", OUT)


if __name__ == "__main__":
    main()
