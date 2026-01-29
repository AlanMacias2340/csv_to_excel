const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const status = document.getElementById('status');

function renderFiles(files) {
    fileList.innerHTML = '';
    Array.from(files).forEach(f => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `<div class="file-name">${f.name}</div><div class="file-status">ready</div>`;
        fileList.appendChild(div);
    });
}

fileInput.addEventListener('change', (e) => renderFiles(e.target.files));

form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const files = fileInput.files;
    if (!files.length) return;
    status.textContent = 'Uploading...';
    const data = new FormData();
    for (const f of files) data.append('files', f);

    try {
        const resp = await fetch(form.action, { method: 'POST', body: data });
        if (!resp.ok) {
            const txt = await resp.text();
            status.textContent = 'Upload failed';
            alert('Upload failed: ' + resp.status + '\n' + txt);
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
        status.textContent = 'Done';
    } catch (err) {
        status.textContent = 'Error';
        alert('Upload error: ' + err.message);
    }
});