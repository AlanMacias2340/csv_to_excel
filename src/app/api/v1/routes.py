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
      <p>Select one or more CSV files to convert to Excel (.xlsx). Multiple files will be returned as a ZIP archive.</p>
      <form id="upload-form" action="/api/v1/convert" method="post" enctype="multipart/form-data">
        <input type="file" name="files" accept=".csv,text/csv" multiple required />
        <button type="submit">Convert & Download</button>
      </form>
      <hr />
      <p>Or use the API directly at <code>/api/v1/convert</code></p>
    </div>
    <script>
      // Use fetch to download the converted file without leaving the page
      document.getElementById('upload-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const fileInput = form.querySelector('input[type=file]');
        if (!fileInput.files.length) return;
        const data = new FormData();
        for (const f of fileInput.files) data.append('files', f);
        const resp = await fetch(form.action, { method: 'POST', body: data });
        if (!resp.ok) {
          const text = await resp.text();
          alert('Upload failed: ' + resp.status + '\n' + text);
          return;
        }
        const blob = await resp.blob();
        const contentDisposition = resp.headers.get('content-disposition') || '';
        let filename = 'converted';
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
