// Feltoltes oldal logika: drag & drop + AJAX upload
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const progress = document.getElementById('uploadProgress');
    const errorMsg = document.getElementById('errorMsg');

    if (!dropZone || !fileInput) return;

    // kattintas = tallozas
    dropZone.addEventListener('click', () => fileInput.click());

    // drag esemenyek
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary', 'bg-primary/5');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-primary', 'bg-primary/5');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary', 'bg-primary/5');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFile(fileInput.files[0]);
        }
    });

    async function handleFile(file) {
        // meret ellenorzes
        if (file.size > 10 * 1024 * 1024) {
            showError('A fájl mérete meghaladja a 10MB-os limitet.');
            return;
        }

        // formatum ellenorzes
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'pdf', 'xlsx', 'xls'].includes(ext)) {
            showError('Nem támogatott formátum. Használj CSV, PDF vagy XLSX fájlt.');
            return;
        }

        // UI: feltoltes inditas
        errorMsg.classList.add('hidden');
        progress.classList.remove('hidden');
        document.getElementById('fileName').textContent = file.name;
        updateStep(1, 'active');

        const formData = new FormData();
        formData.append('file', file);

        try {
            updateStep(1, 'done');
            updateStep(2, 'active');
            document.getElementById('statusText').textContent = 'AI feldolgozás folyamatban...';

            const resp = await fetch('/import/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await resp.json();

            if (result.success) {
                updateStep(2, 'done');
                updateStep(3, 'done');
                document.getElementById('statusText').textContent = 'Kész! Átirányítás...';
                // kicsi varakozas az animacio miatt
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 500);
            } else {
                showError(result.error || 'Ismeretlen hiba történt.');
                progress.classList.add('hidden');
            }
        } catch (e) {
            showError('Hálózati hiba: ' + e.message);
            progress.classList.add('hidden');
        }
    }

    function updateStep(step, state) {
        const icon = document.getElementById(`step${step}Icon`);
        const text = document.getElementById(`step${step}Text`);
        if (state === 'active') {
            icon.classList.add('bg-primary', 'text-white');
            icon.classList.remove('bg-dark-border');
            text.classList.add('text-gray-200');
            text.classList.remove('text-gray-400');
        } else if (state === 'done') {
            icon.innerHTML = '✓';
            icon.classList.add('bg-green-600', 'text-white');
            icon.classList.remove('bg-dark-border', 'bg-primary');
            text.classList.add('text-green-400');
            text.classList.remove('text-gray-400', 'text-gray-200');
        }
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove('hidden');
    }
});
