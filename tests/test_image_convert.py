import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from io import BytesIO
import zipfile
from PIL import Image
import fitz  # PyMuPDF

# ensure src is on path so `import app` works when running pytest from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app

@pytest.mark.asyncio
async def test_convert_single_png_to_webp():
    # create a small PNG
    img = Image.new('RGBA', (10, 10), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format='PNG')
    png_bytes = buf.getvalue()

    files = [("images", ("one.png", png_bytes, "image/png"))]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert-image", files=files)

    assert r.status_code == 200
    assert r.headers.get('content-type') == 'image/webp'
    # WebP starts with RIFF
    assert r.content[:4] == b'RIFF'

@pytest.mark.asyncio
async def test_convert_multiple_png_to_zip():
    img1 = Image.new('RGBA', (8, 8), (0, 255, 0, 255))
    buf1 = BytesIO(); img1.save(buf1, format='PNG'); b1 = buf1.getvalue()
    img2 = Image.new('RGBA', (6, 6), (0, 0, 255, 255))
    buf2 = BytesIO(); img2.save(buf2, format='PNG'); b2 = buf2.getvalue()

    files = [
        ("images", ("one.png", b1, "image/png")),
        ("images", ("two.png", b2, "image/png")),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert-image", files=files)

    assert r.status_code == 200
    assert r.headers.get('content-type') == 'application/zip'

    z = zipfile.ZipFile(BytesIO(r.content))
    names = z.namelist()
    assert 'one.webp' in names
    assert 'two.webp' in names
    for name in names:
        data = z.read(name)
        assert data[:4] == b'RIFF'

@pytest.mark.asyncio
async def test_convert_webp_to_png():
    # create a small WebP
    img = Image.new('RGBA', (10, 10), (255, 128, 0, 255))
    buf = BytesIO()
    img.save(buf, format='WEBP')
    webp_bytes = buf.getvalue()

    files = [("images", ("test.webp", webp_bytes, "image/webp"))]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert-webp", files=files)

    assert r.status_code == 200
    assert r.headers.get('content-type') == 'image/png'
    # PNG starts with PNG signature
    assert r.content[:4] == b'\x89PNG'

@pytest.mark.asyncio
async def test_convert_pdf_to_png():
    # create a simple PDF with one page
    pdf_doc = fitz.open()
    page = pdf_doc.new_page(width=200, height=200)
    page.insert_text((50, 100), "Test PDF", fontsize=20)
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    files = [("files", ("test.pdf", pdf_bytes, "application/pdf"))]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/convert-pdf", files=files)

    assert r.status_code == 200
    assert r.headers.get('content-type') == 'image/png'
    # PNG starts with PNG signature
    assert r.content[:4] == b'\x89PNG'
