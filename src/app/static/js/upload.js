// CSV form
const csvForm = document.getElementById('csv-form');
const csvInput = document.getElementById('file-input');
const csvList = document.getElementById('file-list');
const csvStatus = document.getElementById('csv-status');

// Image form
const imageForm = document.getElementById('image-form');
const imageInput = document.getElementById('image-input');
const imageList = document.getElementById('image-list');
const imageStatus = document.getElementById('image-status');

// WebP form
const webpForm = document.getElementById('webp-form');
const webpInput = document.getElementById('webp-input');
const webpList = document.getElementById('webp-list');
const webpStatus = document.getElementById('webp-status');

function renderList(container, files) {
    container.innerHTML = '';
    Array.from(files).forEach(f => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `<div class="file-name">${f.name}</div><div class="file-status">ready</div>`;
        container.appendChild(div);
    });
}

csvInput.addEventListener('change', (e) => renderList(csvList, e.target.files));
imageInput.addEventListener('change', (e) => renderList(imageList, e.target.files));
webpInput.addEventListener('change', (e) => renderList(webpList, e.target.files));

async function submitFiles(form, inputEl, statusEl, fieldName) {
    const files = inputEl.files;
    if (!files.length) return;
    statusEl.textContent = 'Uploading...';
    const data = new FormData();
    for (const f of files) data.append(fieldName, f);

    try {
        const resp = await fetch(form.action, { method: 'POST', body: data });
        if (!resp.ok) {
            const txt = await resp.text();
            statusEl.textContent = 'Upload failed';
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
        statusEl.textContent = 'Done';
    } catch (err) {
        statusEl.textContent = 'Error';
        alert('Upload error: ' + err.message);
    }
}

csvForm.addEventListener('submit', function (e) {
    e.preventDefault();
    submitFiles(csvForm, csvInput, csvStatus, 'files');
});

imageForm.addEventListener('submit', function (e) {
    e.preventDefault();
    submitFiles(imageForm, imageInput, imageStatus, 'images');
});

webpForm.addEventListener('submit', function (e) {
    e.preventDefault();
    submitFiles(webpForm, webpInput, webpStatus, 'images');
});