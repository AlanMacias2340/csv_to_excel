import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
import zipfile
from io import BytesIO

# ensure src is on path so `import app` works when running pytest from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app

@pytest.mark.asyncio
async def test_convert_single_csv_to_excel():
    csv_content = "a,b,c\n1,2,3\nfoo,bar,baz\n"
    files = [("files", ("test.csv", csv_content, "text/csv"))]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert", files=files)

    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    # XLSX files are ZIP files and should start with PK
    assert r.content[:2] == b"PK"

@pytest.mark.asyncio
async def test_convert_multiple_csv_to_zip():
    csv1 = "a,b\n1,2\n"
    csv2 = "x,y\na,b\n"
    files = [
        ("files", ("one.csv", csv1, "text/csv")),
        ("files", ("two.csv", csv2, "text/csv")),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert", files=files)

    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/zip"

    z = zipfile.ZipFile(BytesIO(r.content))
    names = z.namelist()
    assert "one.xlsx" in names
    assert "two.xlsx" in names
    # check that files inside ZIP look like XLSX (start with PK)
    for name in names:
        data = z.read(name)
        assert data[:2] == b"PK"
