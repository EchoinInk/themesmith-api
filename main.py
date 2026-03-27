import os
import uuid
import base64
import io
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

APP_COLORS = {
    "Phone": "#34C759",
    "Messages": "#007AFF",
    "Safari": "#FF3B30",
    "Camera": "#AF52DE",
    "Photos": "#FF9500",
    "Settings": "#8E8E93",
    "Mail": "#1C1C1E",
    "Clock": "#FFCC00",
    "Calendar": "#FF2D55",
    "Notes": "#FFD60A",
}

def make_test_icon(app_name: str) -> bytes:
    size = 1024
    icon_size = 700  # smaller centered icon
    color = APP_COLORS.get(app_name, "#444444")

    # Transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded square
    x0 = (size - icon_size) // 2
    y0 = (size - icon_size) // 2
    x1 = x0 + icon_size
    y1 = y0 + icon_size

    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=180,
        fill=color
    )

    try:
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        font = ImageFont.load_default()

    text = app_name[:8]
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]

    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2

    draw.text((text_x, text_y), text, fill="white", font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

app = FastAPI(title="ThemeSmith API")

OUTPUT_DIR = "generated_icons"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/generated_icons", StaticFiles(directory=OUTPUT_DIR), name="generated_icons")


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

            print(f"Generating test icon for: {app_name}")
            print(f"Prompt: {prompt}")

            image_bytes = make_test_icon(app_name)

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