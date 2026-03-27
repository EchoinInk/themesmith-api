import os
import uuid
import base64
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load .env from the same folder as this file
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


def make_placeholder_png() -> bytes:
    # 1x1 transparent PNG
    png_base64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
        "/w8AAn8B9pQnWQAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(png_base64)


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
    return {
        "status": "ok",
        "message": "ThemeSmith API is running"
    }


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

            print(f"Generating placeholder icon for: {app_name}")
            print(f"Prompt: {prompt}")

            image_bytes = make_placeholder_png()

            filename = f"{uuid.uuid4().hex}_{app_name.lower().replace(' ', '_')}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            file_url = f"{BASE_URL}/generated_icons/{filename}"
            results.append(IconResult(app_name=app_name, icon_url=file_url))

        return IconPackResponse(theme_name=payload.theme_name, icons=results)

    except Exception as e:
        print("Unexpected error in /generate_icon_pack:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )