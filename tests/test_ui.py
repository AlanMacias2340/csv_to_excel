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
    assert 'name="file"' in r.text
