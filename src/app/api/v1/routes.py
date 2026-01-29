from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from starlette.templating import Jinja2Templates
import csv
from io import StringIO, BytesIO
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
    return templates.TemplateResponse("upload.html", {"request": request})

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
