import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# ensure src is on path so `import app` works when running pytest from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app

@pytest.mark.asyncio
async def test_convert_csv_to_excel():
    csv_content = "a,b,c\n1,2,3\nfoo,bar,baz\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert", files=files)

    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    # XLSX files are ZIP files and should start with PK
    assert r.content[:2] == b"PK"
