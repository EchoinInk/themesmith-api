import os
import io
import uuid
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

app = FastAPI(title="ThemeSmith API")

OUTPUT_DIR = "generated_icons"
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/generated_icons", StaticFiles(directory=OUTPUT_DIR), name="generated_icons")


# -------- Data models --------

class IconPackRequest(BaseModel):
    theme_name: str
    style: str
    primary_color: str
    secondary_color: Optional[str] = None
    finish: str
    icon_list: List[str]
    transparent_background: bool = True


class IconResult(BaseModel):
    app_name: str
    icon_url: str


class IconPackResponse(BaseModel):
    theme_name: str
    icons: List[IconResult]


# -------- App glyph map --------

APP_GLYPHS = {
    "Phone": "✆",
    "Messages": "✉",
    "Safari": "◉",
    "Camera": "◌",
    "Photos": "✦",
    "Settings": "⚙",
    "Mail": "✉",
    "Clock": "◔",
    "Calendar": "31",
    "Notes": "☰",
    "Reminders": "✓",
    "Maps": "⌖",
    "Weather": "☼",
    "App Store": "A",
    "Music": "♪",
    "Spotify": "♪",
    "Instagram": "◐",
    "Facebook": "f",
    "Messenger": "✉",
    "WhatsApp": "✆",
    "TikTok": "♪",
    "YouTube": "▶",
    "Netflix": "N",
    "Gmail": "M",
    "Uber": "U",
    "PayPal": "P",
}


# -------- Helper functions --------

def build_prompt(
    app_name: str,
    style: str,
    primary_color: str,
    secondary_color: Optional[str],
    finish: str,
    transparent_background: bool,
) -> str:
    secondary_text = f", secondary color {secondary_color}" if secondary_color else ""
    background_text = (
        "transparent background, no backdrop, isolated icon"
        if transparent_background
        else "clean solid background"
    )

    return (
        f"Minimal iPhone app icon for {app_name}, centered composition, "
        f"{style} style, {finish} finish, primary color {primary_color}"
        f"{secondary_text}, soft clean lighting, modern premium iOS aesthetic, "
        f"simple readable symbol, no text, {background_text}, square composition."
    )


def load_font(size: int):
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_celestial_icon(app_name: str) -> bytes:
    size = 1024
    plate_size = 760
    radius = 190

    # Transparent canvas
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    x0 = (size - plate_size) // 2
    y0 = (size - plate_size) // 2
    x1 = x0 + plate_size
    y1 = y0 + plate_size

    # Outer glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle(
        [x0 - 10, y0 - 10, x1 + 10, y1 + 10],
        radius=radius + 20,
        fill=(220, 225, 255, 70),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    img.alpha_composite(glow)

    # Plate base
    plate = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    plate_draw = ImageDraw.Draw(plate)

    # Pearl body
    plate_draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=radius,
        fill=(235, 238, 245, 185),
    )

    # Top lavender sheen
    plate_draw.rounded_rectangle(
        [x0 + 18, y0 + 18, x1 - 18, y0 + 220],
        radius=radius - 20,
        fill=(220, 210, 255, 70),
    )

    # Lower blue-silver sheen
    plate_draw.rounded_rectangle(
        [x0 + 30, y0 + 360, x1 - 30, y1 - 30],
        radius=radius - 35,
        fill=(210, 230, 255, 45),
    )

    # Soft diagonal glow
    plate_draw.ellipse(
        [x0 + 80, y0 + 60, x1 - 180, y1 - 280],
        fill=(255, 255, 255, 45),
    )

    plate = plate.filter(ImageFilter.GaussianBlur(1))
    img.alpha_composite(plate)

    # Edge highlight
    edge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge)
    edge_draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=radius,
        outline=(255, 255, 255, 90),
        width=3,
    )
    img.alpha_composite(edge)

    # Glyph selection
    glyph = APP_GLYPHS.get(app_name, app_name[:1].upper())

    # Glyph glow
    glyph_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glyph_draw = ImageDraw.Draw(glyph_layer)
    font = load_font(220)

    bbox = glyph_draw.textbbox((0, 0), glyph, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    tx = (size - text_w) / 2
    ty = (size - text_h) / 2 - 10

    glyph_draw.text((tx, ty), glyph, fill=(210, 220, 255, 110), font=font)
    glyph_layer = glyph_layer.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(glyph_layer)

    # Main glyph
    front = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    front_draw = ImageDraw.Draw(front)
    front_draw.text((tx, ty), glyph, fill=(255, 255, 255, 230), font=font)
    img.alpha_composite(front)

    # Export
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# -------- Routes --------

@app.get("/")
def root():
    return {"status": "ok", "message": "ThemeSmith API is running"}


@app.post("/generate_icon_pack", response_model=IconPackResponse)
def generate_icon_pack(payload: IconPackRequest):
    results: List[IconResult] = []

    try:
        for app_name in payload.icon_list:
            prompt = build_prompt(
                app_name=app_name,
                style=payload.style,
                primary_color=payload.primary_color,
                secondary_color=payload.secondary_color,
                finish=payload.finish,
                transparent_background=payload.transparent_background,
            )

            print(f"Generating icon for: {app_name}")
            print(f"Prompt: {prompt}")

            image_bytes = make_celestial_icon(app_name)

            filename = f"{uuid.uuid4().hex}_{app_name.lower().replace(' ', '_')}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            file_url = f"{BASE_URL}/generated_icons/{filename}"
            results.append(IconResult(app_name=app_name, icon_url=file_url))

        return IconPackResponse(theme_name=payload.theme_name, icons=results)

    except Exception as e:
        print("Unexpected error in /generate_icon_pack:", repr(e))
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")