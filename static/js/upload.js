const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');
const brokerSelect = document.getElementById('brokerSelect');
const runAudit = document.getElementById('runAudit');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');
const errorBar = document.getElementById('errorBar');

let selectedFile = null;
let sessionId = null;

function setFile(file) {
  if (!file || !file.name.endsWith('.csv')) {
    showError('Please select a valid CSV file.');
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  filePreview.style.display = 'flex';
  dropZone.style.display = 'none';
  checkReady();
}

function clearFile() {
  selectedFile = null;
  sessionId = null;
  filePreview.style.display = 'none';
  dropZone.style.display = 'block';
  fileInput.value = '';
  checkReady();
}

function checkReady() {
  runAudit.disabled = !(selectedFile && brokerSelect.value);
}

function showError(msg) {
  errorBar.textContent = msg;
  errorBar.style.display = 'block';
  statusBar.style.display = 'none';
}

function showStatus(msg) {
  statusText.textContent = msg;
  statusBar.style.display = 'flex';
  errorBar.style.display = 'none';
}

// Drag and drop
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });
removeFile.addEventListener('click', clearFile);
brokerSelect.addEventListener('change', checkReady);

runAudit.addEventListener('click', async () => {
  runAudit.disabled = true;
  errorBar.style.display = 'none';
  showStatus('Analyzing portfolio...');

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('broker_id', brokerSelect.value);

    const res = await fetch('/audit', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Audit failed');

    sessionStorage.setItem('auditReport', JSON.stringify(data));
    window.location.href = '/report';
  } catch (err) {
    showError('Audit failed: ' + err.message);
    runAudit.disabled = false;
    statusBar.style.display = 'none';
  }
});
