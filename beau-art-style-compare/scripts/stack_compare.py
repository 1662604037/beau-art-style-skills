#!/usr/bin/env python3
"""Create a non-destructive, ink-album-style top/bottom comparison image."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stack original and modified images vertically.")
    parser.add_argument("--top", required=True, help="Original image path")
    parser.add_argument("--bottom", required=True, help="Modified image path")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=1600, help="Maximum display width")
    parser.add_argument("--gap", type=int, default=88, help="Paper gap between the two images")
    parser.add_argument("--margin", type=int, default=52, help="Outer paper margin")
    parser.add_argument("--edge-feather", type=int, default=56, help="Ink fade width at each image edge")
    parser.add_argument("--top-label", default="", help="Optional top label; hidden by default")
    parser.add_argument("--bottom-label", default="", help="Optional bottom label; hidden by default")
    parser.add_argument("--theme", choices=("ink-wash", "clean"), default="ink-wash", help="Display theme")
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


def paper_background(size: tuple[int, int]) -> Image.Image:
    noise = Image.effect_noise(size, 7).convert("L")
    return ImageOps.colorize(noise, black=(232, 224, 206), white=(250, 246, 234)).convert("RGBA")


def add_wash(canvas: Image.Image, seed: int = 17) -> Image.Image:
    random.seed(seed)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    width, height = canvas.size
    colors = ((91, 111, 108, 24), (118, 104, 85, 18), (72, 88, 84, 14))
    for _ in range(12):
        x = random.choice((random.randint(-80, width // 5), random.randint(width * 4 // 5, width + 80)))
        y = random.randint(0, height)
        rx = random.randint(50, 180)
        ry = random.randint(20, 100)
        color = random.choice(colors)
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(28))
    return Image.alpha_composite(canvas, layer)


def add_ink_divider(canvas: Image.Image, y: int, left: int, right: int) -> Image.Image:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    center = (left + right) // 2
    span = max(1, right - left)
    for offset, alpha, thickness in ((0, 32, 5), (7, 22, 3), (-6, 18, 2)):
        points = []
        for step in range(13):
            x = left + round(span * step / 12)
            wobble = int(5 * ((step % 3) - 1))
            points.append((x, y + offset + wobble))
        draw.line(points, fill=(63, 75, 71, alpha), width=thickness, joint="curve")
    draw.ellipse((center - 4, y - 4, center + 4, y + 4), fill=(63, 75, 71, 34))
    return Image.alpha_composite(canvas, layer.filter(ImageFilter.GaussianBlur(1.2)))


def add_label(canvas: Image.Image, label: str, x: int, y: int, font: ImageFont.ImageFont) -> None:
    if not label:
        return
    draw = ImageDraw.Draw(canvas, "RGBA")
    box = draw.textbbox((0, 0), label, font=font)
    left = x + 8
    baseline = y + 10 - box[1]
    draw.text((left, baseline), label, fill=(69, 72, 66, 215), font=font)
    underline_y = baseline + (box[3] - box[1]) + 9
    draw.line((left, underline_y, left + (box[2] - box[0]) + 20, underline_y), fill=(82, 94, 86, 95), width=2)


def ink_fade_mask(size: tuple[int, int], feather: int, seed: int) -> Image.Image:
    """Create an irregular alpha fade so each image dissolves into the paper."""
    width, height = size
    feather = max(1, min(feather, min(width, height) // 3))
    noise = Image.effect_noise(size, 18).load()
    mask = Image.new("L", size, 0)
    pixels = mask.load()
    random.seed(seed)
    for y in range(height):
        for x in range(width):
            distance = min(x, y, width - 1 - x, height - 1 - y)
            alpha = min(255, round(distance * 255 / feather))
            if distance < feather:
                alpha += round((noise[x, y] - 128) * 0.30)
            pixels[x, y] = max(0, min(255, alpha))
    return mask.filter(ImageFilter.GaussianBlur(1.2))


def paste_ink_faded(canvas: Image.Image, image: Image.Image, x: int, y: int, feather: int, seed: int) -> Image.Image:
    image_rgba = image.convert("RGBA")
    image_rgba.putalpha(ink_fade_mask(image.size, feather, seed))
    canvas.alpha_composite(image_rgba, (x, y))
    # A barely visible wash behind the edge creates a wet-ink halo without drawing a frame.
    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    halo_mask = ink_fade_mask(image.size, max(12, feather // 2), seed + 1).filter(ImageFilter.GaussianBlur(14))
    halo_color = Image.new("RGBA", image.size, (94, 108, 98, 20))
    halo_color.putalpha(halo_mask.point(lambda value: round(value * 0.16)))
    halo.alpha_composite(halo_color, (x, y))
    return Image.alpha_composite(canvas, halo)


def main() -> int:
    args = parse_args()
    if args.width <= 0 or args.gap < 0 or args.margin < 0 or args.edge_feather < 0:
        raise ValueError("width must be positive; spacing and edge feather cannot be negative")

    top = load_rgb(Path(args.top))
    bottom = load_rgb(Path(args.bottom))
    display_width = min(args.width, max(top.width, bottom.width))
    top = fit_width(top, display_width)
    bottom = fit_width(bottom, display_width)

    label_band = 54 if (args.top_label or args.bottom_label) else 0
    canvas_width = display_width + args.margin * 2
    canvas_height = args.margin + label_band + top.height + args.gap + label_band + bottom.height + args.margin
    if args.theme == "ink-wash":
        canvas = add_wash(paper_background((canvas_width, canvas_height)))
    else:
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (247, 247, 245, 255))
    top_x = args.margin
    top_y = args.margin + label_band
    bottom_x = args.margin
    bottom_y = top_y + top.height + args.gap + label_band
    fade = max(24, args.edge_feather)
    canvas = paste_ink_faded(canvas, top, top_x, top_y, fade, 511)
    canvas = paste_ink_faded(canvas, bottom, bottom_x, bottom_y, fade, 522)

    font = get_font(max(18, round(display_width / 48)))
    add_label(canvas, args.top_label, args.margin, args.margin, font)
    add_label(canvas, args.bottom_label, args.margin, top_y + top.height + args.gap, font)
    if args.theme == "ink-wash":
        canvas = add_ink_divider(canvas, top_y + top.height + args.gap // 2, args.margin + 30, canvas_width - args.margin - 30)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
