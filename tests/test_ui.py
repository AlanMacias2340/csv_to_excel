import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# ensure src is on path so `import app` works when running pytest from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app

@pytest.mark.asyncio
async def test_upload_page():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v1/upload")

    assert r.status_code == 200
    assert "<form" in r.text
    assert 'enctype="multipart/form-data"' in r.text
    # input name should be 'files' and it should support multiple selection
    assert 'name="files"' in r.text
    assert 'multiple' in r.text

@pytest.mark.asyncio
async def test_static_assets_served():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_css = await ac.get("/static/css/style.css")
        r_js = await ac.get("/static/js/upload.js")

    assert r_css.status_code == 200
    assert 'file-list' in r_js.text
