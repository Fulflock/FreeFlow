# scripts/generate_icon.py
"""Generate the FreeFlow .ico from scratch (pink bubble + cream FF)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PINK = (255, 93, 143, 255)
PINK_SHADOW = (255, 180, 200, 180)
INK = (22, 20, 15, 255)
CREAM = (255, 245, 230, 255)

SIZES = [16, 32, 48, 64, 128, 256]
OUT = Path(__file__).resolve().parents[1] / "assets" / "freeflow.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)


def _font(size_px):
    for name in ("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size_px)
        except OSError:
            continue
    return ImageFont.load_default()


def render(px):
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = max(1, px // 16)
    shadow = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (pad + px // 32, pad + px // 16, px - pad + px // 32, px - pad + px // 16),
        radius=px // 5, fill=PINK_SHADOW,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(px // 48 + 1))
    img.alpha_composite(shadow)
    d.rounded_rectangle(
        (pad, pad, px - pad, px - pad),
        radius=px // 5, fill=PINK, outline=INK, width=max(1, px // 64),
    )
    font = _font(int(px * 0.58))
    text = "FF"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (px - tw) // 2 - bbox[0]
    ty = (px - th) // 2 - bbox[1] - px // 32
    d.text((tx, ty), text, fill=CREAM, font=font)
    return img


def main():
    frames = [render(s) for s in SIZES]
    # Save largest frame as base so all sub-frames preserve their native resolution;
    # otherwise Pillow downsamples from frames[0] (16x16) and every slot looks pixelated.
    frames[-1].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[:-1],
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
