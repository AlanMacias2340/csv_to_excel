from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook

router = APIRouter()

@router.get("/hello", tags=["example"])
async def hello():
    return {"message": "Hello, world!"}

@router.get("/upload", response_class=HTMLResponse, tags=["ui"])
async def upload_page():
    html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CSV → Excel Converter</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      .card { max-width: 600px; padding: 1rem; border: 1px solid #e1e1e1; border-radius: 8px; }
      input[type=file] { display:block; margin-bottom: 1rem; }
      button { padding: 0.5rem 1rem; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>CSV → Excel</h1>
      <p>Select a CSV file to convert to Excel (.xlsx).</p>
      <form id="upload-form" action="/api/v1/convert" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv,text/csv" required />
        <button type="submit">Convert & Download</button>
      </form>
      <hr />
      <p>Or use the API directly at <code>/api/v1/convert</code></p>
    </div>
    <script>
      // Optional: use fetch to download the converted file without leaving the page
      document.getElementById('upload-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const data = new FormData(form);
        const fileInput = form.querySelector('input[type=file]');
        if (!fileInput.files.length) return;
        const resp = await fetch(form.action, { method: 'POST', body: data });
        if (!resp.ok) {
          alert('Upload failed: ' + resp.statusText);
          return;
        }
        const blob = await resp.blob();
        const contentDisposition = resp.headers.get('content-disposition') || '';
        let filename = 'converted.xlsx';
        const m = /filename="(?<name>.+)"/.exec(contentDisposition);
        if (m && m.groups && m.groups.name) filename = m.groups.name;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
        window.URL.revokeObjectURL(url);
      });
    </script>
  </body>
</html>"""
    return HTMLResponse(content=html)

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
