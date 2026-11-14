#!/usr/bin/env python3
"""Render animated SVG profile cards to GIFs for GitHub README display.

GitHub sanitizes SVG animation in README embeds. Rendering the source SVGs in
Chromium and capturing frames preserves the intended CSS/SMIL motion.
"""
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
CARDS = ROOT / "cards"
SOURCES = [
    "01-hero-v2.svg",
    "02-tile-1-v2.svg",
    "02-tile-2-v2.svg",
    "02-tile-3-v2.svg",
    "03-activity.svg",
    "04-heatmap.svg",
    "06-achievements-v2.svg",
    "07-milestones-v3.svg",
]
FRAME_COUNT = 20
FRAME_DELAY_MS = 350


def dimension(value, fallback):
    match = re.match(r"^([0-9.]+)", value or "")
    return max(1, int(round(float(match.group(1))))) if match else fallback


def render_one(browser, source):
    path = CARDS / source
    root = ET.parse(path).getroot()
    width = min(1200, dimension(root.attrib.get("width"), 880))
    height = min(900, dimension(root.attrib.get("height"), 420))
    page = browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        reduced_motion="no-preference",
    )
    page.goto(path.as_uri(), wait_until="load")
    frames = []
    for _ in range(FRAME_COUNT):
        page.wait_for_timeout(FRAME_DELAY_MS)
        png = page.screenshot(type="png", animations="allow")
        from io import BytesIO
        frame = Image.open(BytesIO(png)).convert("RGB")
        # A shared adaptive palette keeps the GIF compact and consistent.
        frames.append(frame)
    page.close()

    # Quantize every frame against the first frame's palette.
    palette = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
    quantized = [palette]
    quantized.extend(
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames[1:]
    )
    output = path.with_suffix(".gif")
    quantized[0].save(
        output,
        save_all=True,
        append_images=quantized[1:],
        duration=FRAME_DELAY_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"{output.relative_to(ROOT)}: {width}x{height}, {FRAME_COUNT} frames, {output.stat().st_size:,} bytes")


def main():
    missing = [name for name in SOURCES if not (CARDS / name).exists()]
    if missing:
        raise SystemExit("Missing SVG source cards: " + ", ".join(missing))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--no-sandbox"])
        try:
            for source in SOURCES:
                render_one(browser, source)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
