#!/usr/bin/env python3
"""Create a presentation-ready GIF of Pac-Man chasing U-log.

The script only depends on Pillow. By default it uses the current Avoha mascot
PNG as the U-log asset, but any transparent PNG can be swapped in with --logo.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGO = ROOT / "frontend" / "public" / "images" / "mascot.png"
DEFAULT_OUTPUT = ROOT / "design" / "deliverables" / "animation" / "pacman_ulog.gif"


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * value)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit_image(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    image.thumbnail(box, Image.Resampling.LANCZOS)
    return image


def draw_pacman(draw: ImageDraw.ImageDraw, center: tuple[float, float], radius: int, frame: int) -> None:
    cx, cy = center
    mouth_cycle = abs(math.sin(frame * math.pi / 5))
    mouth_angle = 12 + mouth_cycle * 34
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]

    draw.pieslice(bbox, mouth_angle, 360 - mouth_angle, fill="#FFD51D")
    draw.arc(bbox, mouth_angle, 360 - mouth_angle, fill="#FFF1A0", width=3)
    draw.ellipse([cx - radius * 0.18, cy - radius * 0.55, cx - radius * 0.02, cy - radius * 0.39], fill="#101010")


def rounded_rectangle(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def paste_center(base: Image.Image, asset: Image.Image, center: tuple[float, float]) -> None:
    x = int(center[0] - asset.width / 2)
    y = int(center[1] - asset.height / 2)
    base.alpha_composite(asset, (x, y))


def draw_ulog_badge(frame: Image.Image, center: tuple[float, float], text: str) -> None:
    draw = ImageDraw.Draw(frame)
    font = load_font(22, bold=True)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    pad_x, pad_y = 15, 9
    box_w = text_w + pad_x * 2
    box_h = text_h + pad_y * 2
    left = int(center[0] - box_w / 2)
    top = int(center[1] + 54)
    shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    rounded_rectangle(shadow_draw, (left + 2, top + 3, left + box_w + 2, top + box_h + 3), 12, "#00000090")
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    frame.alpha_composite(shadow)
    rounded_rectangle(draw, (left, top, left + box_w, top + box_h), 12, "#FFFFFF")
    draw.text((left + pad_x, top + pad_y - 2), text, fill="#2B2B2B", font=font)


def make_frame(
    logo: Image.Image,
    frame_index: int,
    total_frames: int,
    width: int,
    height: int,
    label: str,
) -> Image.Image:
    bg = Image.new("RGBA", (width, height), "#080808")
    draw = ImageDraw.Draw(bg)

    lane_y = height * 0.5
    progress = frame_index / (total_frames - 1)
    eased = ease_in_out(progress)
    start_x = -70
    end_x = width + 70
    pac_x = start_x + (end_x - start_x) * eased
    logo_x = pac_x - 145

    # Subtle corridor grid for a retro stage feel.
    for x in range(0, width, 48):
        alpha = 32 if x % 96 == 0 else 18
        draw.line([(x, 0), (x, height)], fill=(40, 42, 58, alpha), width=1)
    for y in range(0, height, 48):
        alpha = 28 if y % 96 == 0 else 16
        draw.line([(0, y), (width, y)], fill=(40, 42, 58, alpha), width=1)

    # Dots disappear as Pac-Man reaches them.
    dot_start = 110
    dot_gap = 62
    for i in range(13):
        x = dot_start + i * dot_gap
        if x > pac_x - 28:
            pulse = 0.84 + 0.16 * math.sin(frame_index * 0.55 + i)
            r = int(6 * pulse)
            draw.ellipse((x - r, lane_y - r, x + r, lane_y + r), fill="#FFDFA4")

    # Motion trail behind the U-log asset.
    for i, alpha in enumerate((34, 24, 16)):
        ghost = logo.copy()
        ghost_alpha = ghost.getchannel("A").point(lambda p, a=alpha: min(p, a))
        ghost.putalpha(ghost_alpha)
        paste_center(bg, ghost, (logo_x - (i + 1) * 16, lane_y))

    paste_center(bg, logo, (logo_x, lane_y))
    draw_ulog_badge(bg, (logo_x, lane_y), label)
    draw_pacman(draw, (pac_x, lane_y), 48, frame_index)

    return bg.convert("P", palette=Image.Palette.ADAPTIVE, colors=192)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Pac-Man and U-log GIF for slides.")
    parser.add_argument("--logo", type=Path, default=DEFAULT_LOGO, help="PNG asset that follows Pac-Man.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="GIF output path.")
    parser.add_argument("--label", default="U-log", help="Badge label shown under the following asset.")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--frames", type=int, default=54)
    parser.add_argument("--duration", type=int, default=55, help="Frame duration in milliseconds.")
    args = parser.parse_args()

    if not args.logo.exists():
        raise FileNotFoundError(f"Logo PNG not found: {args.logo}")

    logo = fit_image(Image.open(args.logo), (86, 86))
    frames = [
        make_frame(logo, i, args.frames, args.width, args.height, args.label)
        for i in range(args.frames)
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=args.duration,
        loop=0,
        optimize=False,
        disposal=2,
    )
    print(args.output)


if __name__ == "__main__":
    main()
