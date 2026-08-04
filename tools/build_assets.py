"""Rebuild the site's derived static assets.

Run from the repository root after changing a source photograph, the wordmark
text, or a font:

    .venv/bin/pip install Pillow "fonttools[woff]"
    .venv/bin/python tools/build_assets.py

Source photographs and fonts live in ``assets-src/`` (never served).
Outputs land in ``static/registration/img`` and ``static/registration/fonts``
and are committed, so a deploy does not need image tooling installed.
"""

import pathlib
import subprocess
import sys

SRC = pathlib.Path("assets-src")
OUT = pathlib.Path("static/registration")
IMG_OUT = OUT / "img"
FONT_OUT = OUT / "fonts"

# source photograph -> output basename, widths to emit
IMAGE_JOBS = [
    ("photos/grass_dune.jpg", "dune", [1280, 1920, 2560]),
    ("photos/background_new.jpeg", "coast-wide", [1280, 1920]),
    ("photos/sunset.JPG", "sunset", [1280, 1920]),
    ("photos/sunset_moon.JPG", "moon", [1280, 1920]),
    ("photos/close_dune.JPG", "close-dune", [1280, 1920]),
    ("sage_hoodie.jpg", "hoodie-sage", [640]),
    ("green_hoodie.jpg", "hoodie-forest", [640]),
]

OG_SOURCE = "photos/grass_dune.jpg"

# The display face is used only for fixed wordmark strings — the site brand,
# the year, and the "STAFF" label. Subsetting to just those characters takes it
# from ~200 KB to ~50 KB. If you change any text rendered in this font, add its
# characters here and re-run.
DISPLAY_FONT_TEXT = "FullyAliveRetreat STAF0123456789"


def build_images():
    from PIL import Image, ImageOps

    IMG_OUT.mkdir(parents=True, exist_ok=True)

    for source, basename, widths in IMAGE_JOBS:
        path = SRC / source
        if not path.exists():
            print(f"  !! missing {path}")
            continue

        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            for width in widths:
                if width > im.width:
                    continue
                height = round(im.height * width / im.width)
                resized = im.resize((width, height), Image.LANCZOS)
                resized.save(
                    IMG_OUT / f"{basename}-{width}.jpg",
                    "JPEG", quality=78, optimize=True, progressive=True,
                )
                resized.save(
                    IMG_OUT / f"{basename}-{width}.webp", "WEBP", quality=76, method=6
                )
            print(f"  {basename}: {len(widths)} sizes")

    # Open Graph share image, cropped to the 1.91:1 ratio.
    with Image.open(SRC / OG_SOURCE) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        ImageOps.fit(im, (1200, 630), Image.LANCZOS).save(
            IMG_OUT / "og-cover.jpg", "JPEG", quality=82, optimize=True, progressive=True
        )
    print("  og-cover")

    with Image.open(SRC / "NWASBC Logo FINAL Full Wording Vertical White.png") as im:
        im = im.convert("RGBA")
        height = round(im.height * 300 / im.width)
        im.resize((300, height), Image.LANCZOS).save(
            IMG_OUT / "nwasbc-logo-vertical-white.png", "PNG", optimize=True
        )
    print("  nwasbc-logo")

    with Image.open(SRC / "NWASBC Logo Acronym Vertical.png") as im:
        canvas = Image.new("RGBA", (180, 180), (80, 128, 128, 255))
        logo = ImageOps.contain(im.convert("RGBA"), (140, 140), Image.LANCZOS)
        canvas.paste(logo, ((180 - logo.width) // 2, (180 - logo.height) // 2), logo)
        canvas.convert("RGB").save(IMG_OUT / "apple-touch-icon.png", "PNG", optimize=True)
    print("  apple-touch-icon")


def build_fonts():
    FONT_OUT.mkdir(parents=True, exist_ok=True)

    # Display face: subset to the wordmark characters only.
    subprocess.run(
        [
            sys.executable, "-m", "fontTools.subset", str(SRC / "Austhind.ttf"),
            f"--text={DISPLAY_FONT_TEXT}",
            "--flavor=woff2",
            f"--output-file={FONT_OUT / 'austhind.woff2'}",
        ],
        check=True,
    )
    print(f"  austhind.woff2 ({(FONT_OUT / 'austhind.woff2').stat().st_size // 1024}K)")

    # Body face: keep every glyph — it carries the Cyrillic used by church names.
    from fontTools.ttLib import TTFont

    font = TTFont(SRC / "8483.ttf")
    font.flavor = "woff2"
    font.save(FONT_OUT / "camp-sans.woff2")
    print(f"  camp-sans.woff2 ({(FONT_OUT / 'camp-sans.woff2').stat().st_size // 1024}K)")


if __name__ == "__main__":
    if not SRC.exists():
        sys.exit("Run this from the repository root.")
    print("Images:")
    build_images()
    print("Fonts:")
    build_fonts()
    print("Done.")
