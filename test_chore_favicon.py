import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from eink_backend.main import app


ASSETS_DIR = Path(__file__).parent / "assets"
ASSET_PATH = ASSETS_DIR / "favicon.ico"
MANIFEST_PATH = ASSETS_DIR / "manifest.webmanifest"


def test_favicon_asset_is_valid_ico():
    assert ASSET_PATH.is_file()
    assert ASSET_PATH.stat().st_size > 0

    with Image.open(ASSET_PATH) as favicon:
        assert favicon.format == "ICO"
        assert favicon.size in {(16, 16), (32, 32), (48, 48)}


def test_high_resolution_icon_assets_are_valid():
    for size in (192, 512):
        icon_path = ASSETS_DIR / "icons" / f"icon-{size}.png"
        assert icon_path.is_file()
        assert icon_path.stat().st_size > 0
        with Image.open(icon_path) as icon:
            assert icon.format == "PNG"
            assert icon.size == (size, size)


def test_chores_page_declares_favicon():
    with TestClient(app) as client:
        response = client.get("/chores")

    assert response.status_code == 200
    assert '<link rel="icon" type="image/x-icon" href="/favicon.ico">' in response.text


def test_chores_page_declares_pwa_metadata():
    with TestClient(app) as client:
        response = client.get("/chores")

    assert response.status_code == 200
    assert '<link rel="manifest" href="/manifest.webmanifest">' in response.text
    assert '<meta name="theme-color" content="#2c5282">' in response.text
    assert '<link rel="apple-touch-icon" href="/icons/icon-192.png">' in response.text


def test_manifest_route_serves_required_metadata():
    with TestClient(app) as client:
        response = client.get("/manifest.webmanifest")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/manifest+json"
    manifest = response.json()
    assert manifest["start_url"] == "/chores"
    assert manifest["display"] == "standalone"
    assert {icon["src"] for icon in manifest["icons"]} == {
        "/icons/icon-192.png",
        "/icons/icon-512.png",
    }


def test_favicon_route_serves_checked_in_asset():
    expected_bytes = ASSET_PATH.read_bytes()

    with TestClient(app) as client:
        response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/x-icon"
    assert response.content == expected_bytes


def test_manifest_asset_is_valid_json():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["short_name"] == "Chores"


def test_png_icon_routes_serve_checked_in_assets():
    with TestClient(app) as client:
        for size in (192, 512):
            response = client.get(f"/icons/icon-{size}.png")
            expected_bytes = (ASSETS_DIR / "icons" / f"icon-{size}.png").read_bytes()

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == expected_bytes