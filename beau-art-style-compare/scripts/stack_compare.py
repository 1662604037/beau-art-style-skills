#!/usr/bin/env python3
"""Create a non-destructive top/bottom before-after comparison image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stack original and modified images vertically.")
    parser.add_argument("--top", required=True, help="Original image path")
    parser.add_argument("--bottom", required=True, help="Modified image path")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=1600, help="Maximum display width")
    parser.add_argument("--gap", type=int, default=24, help="Gap between the two images")
    parser.add_argument("--margin", type=int, default=24, help="Outer margin")
    parser.add_argument("--top-label", default="原图", help="Top label; use an empty string to hide")
    parser.add_argument("--bottom-label", default="修改后", help="Bottom label; use an empty string to hide")
    return parser.parse_args()


def load_rgb(path: Path) -> Image.Image:
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def fit_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image.copy()
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def add_label(canvas: Image.Image, image: Image.Image, label: str, x: int, y: int, font: ImageFont.ImageFont) -> None:
    if not label:
        return
    draw = ImageDraw.Draw(canvas, "RGBA")
    box = draw.textbbox((0, 0), label, font=font)
    pad_x, pad_y = 12, 7
    left = x + 16
    top = y + 16
    right = left + (box[2] - box[0]) + pad_x * 2
    bottom = top + (box[3] - box[1]) + pad_y * 2
    draw.rounded_rectangle((left, top, right, bottom), radius=10, fill=(255, 255, 255, 220))
    draw.text((left + pad_x, top + pad_y - box[1]), label, fill=(45, 45, 45, 255), font=font)


def main() -> int:
    args = parse_args()
    if args.width <= 0 or args.gap < 0 or args.margin < 0:
        raise ValueError("width must be positive; gap and margin cannot be negative")

    top = load_rgb(Path(args.top))
    bottom = load_rgb(Path(args.bottom))
    display_width = min(args.width, max(top.width, bottom.width))
    top = fit_width(top, display_width)
    bottom = fit_width(bottom, display_width)

    label_space = 0
    if args.top_label or args.bottom_label:
        label_space = 0
    canvas_width = display_width + args.margin * 2
    canvas_height = args.margin + top.height + args.gap + bottom.height + args.margin
    canvas = Image.new("RGB", (canvas_width, canvas_height), (247, 247, 245))
    top_x = args.margin
    top_y = args.margin
    bottom_x = args.margin
    bottom_y = args.margin + top.height + args.gap
    canvas.paste(top, (top_x, top_y))
    canvas.paste(bottom, (bottom_x, bottom_y))

    font = get_font(max(18, round(display_width / 55)))
    add_label(canvas, top, args.top_label, top_x, top_y, font)
    add_label(canvas, bottom, args.bottom_label, bottom_x, bottom_y, font)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
