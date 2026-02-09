from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from starlette.templating import Jinja2Templates
import csv
from io import StringIO, BytesIO
from PIL import Image
import fitz  # PyMuPDF
from openpyxl import Workbook
from pathlib import Path

router = APIRouter()

# Templates directory relative to this file
# routes.py is at src/app/api/v1; templates live at src/app/templates -> use parents[2]
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))

@router.get("/hello", tags=["example"])
async def hello():
    return {"message": "Hello, world!"}

@router.get("/upload", response_class=HTMLResponse, tags=["ui"])
async def upload_page(request: Request):
    """Render the upload page (Jinja2 template)."""
    # TemplateResponse now expects the Request first to avoid deprecation warnings
    return templates.TemplateResponse(request, "upload.html", {"request": request})

@router.post("/convert", tags=["conversion"])
async def convert_csv_to_excel(files: list[UploadFile] = File(...)):
    """Receive one or more CSV files and return an XLSX for a single file or a ZIP for multiple files."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    allowed = ("text/csv", "application/csv", "text/plain")

    async def csv_to_xlsx_bytes(content_bytes: bytes):
        # decode with fallbacks
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(status_code=400, detail="Unable to decode uploaded file.")
        reader = csv.reader(StringIO(text))
        wb = Workbook()
        ws = wb.active
        for row in reader:
            ws.append(row)
        out = BytesIO()
        wb.save(out)
        return out.getvalue()

    # Validate and process files
    results = []  # list of tuples (filename, bytes)
    for file in files:
        if file.content_type not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Please upload CSV files.")
        contents = await file.read()
        xlsx_bytes = await csv_to_xlsx_bytes(contents)
        fname = (file.filename.rsplit('.', 1)[0] if file.filename else 'converted') + '.xlsx'
        results.append((fname, xlsx_bytes))

    # If only one file, return XLSX directly
    if len(results) == 1:
        fname, xlsx_bytes = results[0]
        out = BytesIO(xlsx_bytes)
        headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
        return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    # Multiple files: package into a ZIP
    import zipfile
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, data in results:
            zf.writestr(fname, data)
    zip_io.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="converted_files.zip"'}
    return StreamingResponse(zip_io, media_type="application/zip", headers=headers)

@router.post("/convert-image", tags=["conversion"])
async def convert_png_to_webp(images: list[UploadFile] = File(...)):
    """Convert one or more PNG images to WebP. Single image -> returns .webp, multiple -> returns ZIP of .webp files."""
    if not images:
        raise HTTPException(status_code=400, detail="No images uploaded.")

    results = []
    for img in images:
        if img.content_type != "image/png":
            raise HTTPException(status_code=400, detail=f"Invalid image type for {img.filename}. Only PNG supported.")
        contents = await img.read()
        try:
            im = Image.open(BytesIO(contents)).convert('RGBA')
            out = BytesIO()
            # Use lossy compression with quality=85 for better file size reduction
            im.save(out, format='WEBP', quality=85, method=6)
            out.seek(0)
            fname = (img.filename.rsplit('.', 1)[0] if img.filename else 'converted') + '.webp'
            results.append((fname, out.getvalue()))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Unable to process image {img.filename}.")

    # single image -> return webp
    if len(results) == 1:
        fname, data = results[0]
        return StreamingResponse(BytesIO(data), media_type="image/webp", headers={"Content-Disposition": f'attachment; filename="{fname}"'})

    # multiple images -> zip
    import zipfile
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, data in results:
            zf.writestr(fname, data)
    zip_io.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="converted_images.zip"'}
    return StreamingResponse(zip_io, media_type="application/zip", headers=headers)

@router.post("/convert-webp", tags=["conversion"])
async def convert_webp_to_png(images: list[UploadFile] = File(...)):
    """Convert one or more WebP images to PNG. Single image -> returns .png, multiple -> returns ZIP of .png files."""
    if not images:
        raise HTTPException(status_code=400, detail="No images uploaded.")

    results = []
    for img in images:
        if img.content_type != "image/webp":
            raise HTTPException(status_code=400, detail=f"Invalid image type for {img.filename}. Only WebP supported.")
        contents = await img.read()
        try:
            im = Image.open(BytesIO(contents))
            out = BytesIO()
            im.save(out, format='PNG')
            out.seek(0)
            fname = (img.filename.rsplit('.', 1)[0] if img.filename else 'converted') + '.png'
            results.append((fname, out.getvalue()))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Unable to process image {img.filename}.")

    # single image -> return png
    if len(results) == 1:
        fname, data = results[0]
        return StreamingResponse(BytesIO(data), media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{fname}"'})

    # multiple images -> zip
    import zipfile
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, data in results:
            zf.writestr(fname, data)
    zip_io.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="converted_webp_images.zip"'}
    return StreamingResponse(zip_io, media_type="application/zip", headers=headers)

@router.post("/convert-pdf", tags=["conversion"])
async def convert_pdf_to_png(files: list[UploadFile] = File(...)):
    """Convert PDF pages to PNG. Each page becomes a PNG. Returns single PNG or ZIP."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results = []  # list of (filename, png_bytes)
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Only PDF supported.")
        contents = await file.read()
        try:
            pdf_doc = fitz.open(stream=contents, filetype="pdf")
            base_name = file.filename.rsplit('.', 1)[0] if file.filename else 'converted'
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                # Render page to pixmap at 2x resolution (dpi=144)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                png_bytes = pix.tobytes("png")
                
                if len(pdf_doc) == 1:
                    fname = f"{base_name}.png"
                else:
                    fname = f"{base_name}_page_{page_num + 1}.png"
                results.append((fname, png_bytes))
            pdf_doc.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to process PDF {file.filename}: {str(e)}")

    # single PNG -> return it
    if len(results) == 1:
        fname, data = results[0]
        return StreamingResponse(BytesIO(data), media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{fname}"'})

    # multiple PNGs -> zip
    import zipfile
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, data in results:
            zf.writestr(fname, data)
    zip_io.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="converted_pdf_images.zip"'}
    return StreamingResponse(zip_io, media_type="application/zip", headers=headers)
