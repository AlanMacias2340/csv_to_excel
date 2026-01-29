from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook

router = APIRouter()

@router.get("/hello", tags=["example"])
async def hello():
    return {"message": "Hello, world!"}

@router.post("/convert", tags=["conversion"])
async def convert_csv_to_excel(file: UploadFile = File(...)):
    """Receive a CSV file and return an XLSX file."""
    if file.content_type not in ("text/csv", "application/csv", "text/plain"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    contents = await file.read()
    # try utf-8 then fallback
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = contents.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode uploaded file.")

    reader = csv.reader(StringIO(text))

    wb = Workbook()
    ws = wb.active

    for row in reader:
        ws.append(row)

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    filename = (file.filename.rsplit(".", 1)[0] if file.filename else "converted") + ".xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
