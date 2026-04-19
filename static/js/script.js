// ============================================================
// SECUREMIND AI — script.js  (version finale unifiée)
// Gère : navbar · counters · terminal · phishing · IDS (boutons + CSV upload) · charts
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // ════════════════════════════════════════════════════════
    // 1. NAVBAR SCROLL EFFECT
    // ════════════════════════════════════════════════════════
    const navbar = document.getElementById('main-nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.background    = 'rgba(0,0,0,0.97)';
                navbar.style.borderBottom  = '1px solid #30363d';
                navbar.style.paddingTop    = '0.5rem';
                navbar.style.paddingBottom = '0.5rem';
            } else {
                navbar.style.background    = 'var(--bg-primary, #000)';
                navbar.style.borderBottom  = '1px solid transparent';
                navbar.style.paddingTop    = '1rem';
                navbar.style.paddingBottom = '1rem';
            }
        });
    }

    // ════════════════════════════════════════════════════════
    // 2. ANIMATED STAT COUNTERS
    // ════════════════════════════════════════════════════════
    const counters = document.querySelectorAll('.stat-number');
    if (counters.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.target.innerText === '0') {
                    animateCounter(entry.target);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach(c => observer.observe(c));
    }

    function animateCounter(el) {
        const target    = parseFloat(el.getAttribute('data-target'));
        const isDecimal = target % 1 !== 0;
        const steps     = 60;
        const increment = target / steps;
        let current     = 0;

        const interval = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            if (isDecimal) {
                el.innerText = current.toFixed(1);
            } else if (target >= 1000000) {
                el.innerText = (current / 1000000).toFixed(1) + 'M';
            } else if (target >= 1000) {
                el.innerText = Math.ceil(current).toLocaleString();
            } else {
                el.innerText = Math.ceil(current);
            }
        }, 1800 / steps);
    }

    // ════════════════════════════════════════════════════════
    // 3. TERMINAL ANIMATION  (page d'accueil)
    // ════════════════════════════════════════════════════════
    const terminalBody = document.getElementById('terminal-logs');
    if (terminalBody) {
        const logs = [
            { type: 'info',  text: '[INFO]  Initializing SecureMind AI engine...' },
            { type: 'info',  text: '[INFO]  Loading RFC_CICIDS2017.joblib ... OK' },
            { type: 'info',  text: '[INFO]  Loading TFIDF_Phishing.pkl    ... OK' },
            { type: 'info',  text: '[INFO]  StandardScaler loaded          ... OK' },
            { type: 'info',  text: '[INFO]  Listening on 0.0.0.0:5000' },
            { type: 'warn',  text: '[WARN]  High traffic volume detected (eth0)' },
            { type: 'alert', text: '[ALERT] IDS: PortScan from 192.168.1.105 — Confidence: 88.1%' },
            { type: 'info',  text: '[INFO]  Flow flagged. TCP RST executed.' },
            { type: 'alert', text: '[ALERT] PHISH: Email #4092 — malicious payload detected' },
            { type: 'info',  text: '[INFO]  Email quarantined. Domain blocked.' },
            { type: 'alert', text: '[ALERT] IDS: DDoS pattern matched — Confidence: 99.2%' },
            { type: 'info',  text: '[INFO]  Rate-limit rules applied. Flow mitigated.' },
            { type: 'alert', text: '[ALERT] IDS: Brute Force SSH :22 — Confidence: 97.5%' },
            { type: 'info',  text: '[INFO]  IP 10.0.0.52 blocked. Alert sent.' },
        ];
        let idx = 0;
        function addLog() {
            const log  = logs[idx % logs.length];
            const now  = new Date().toISOString().split('T')[1].substring(0, 8);
            const div  = document.createElement('div');
            div.className = 'log-line';
            const cls  = log.type === 'alert' ? 'log-alert'
                       : log.type === 'warn'  ? 'log-warn'
                       : 'log-info';
            div.innerHTML = `<span class="log-time">[${now}]</span> <span class="${cls}">${log.text}</span>`;
            terminalBody.appendChild(div);
            terminalBody.scrollTop = terminalBody.scrollHeight;
            if (terminalBody.childElementCount > 12) terminalBody.removeChild(terminalBody.firstChild);
            idx++;
            setTimeout(addLog, Math.random() * 1800 + 700);
        }
        setTimeout(addLog, 800);
    }

    // ════════════════════════════════════════════════════════
    // 4. DASHBOARD CHARTS  (page index.html)
    // ════════════════════════════════════════════════════════
    if (document.getElementById('phishingPieChart')) initDashboardCharts();

    function initDashboardCharts() {
        if (typeof Chart === 'undefined') return;
        Chart.defaults.color       = '#7a8b9a';
        Chart.defaults.font.family = "'JetBrains Mono', monospace";

        const ctxPie = document.getElementById('phishingPieChart');
        if (ctxPie) {
            new Chart(ctxPie.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Normal Traffic','DoS/DDoS','Port Scanning','Brute Force','Bots','Web Attacks'],
                    datasets: [{
                        data: [83.11, 12.77, 3.60, 0.36, 0.08, 0.08],
                        backgroundColor: [
                            'rgba(0,255,136,0.75)', 'rgba(255,59,92,0.75)',
                            'rgba(56,189,248,0.75)', 'rgba(255,170,0,0.75)',
                            'rgba(124,58,237,0.75)', 'rgba(255,99,132,0.75)',
                        ],
                        borderWidth: 0, hoverOffset: 6,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, cutout: '72%',
                    plugins: {
                        legend: { position: 'bottom', labels: { padding: 14, boxWidth: 8, color: '#7a8b9a' } },
                        tooltip: { backgroundColor: '#0d1117', borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1 }
                    }
                }
            });
        }

        const ctxBar = document.getElementById('idsBarChart');
        if (ctxBar) {
            new Chart(ctxBar.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['DDoS','DoS','PortScan','BruteForce','Bots','WebAtk'],
                    datasets: [{
                        label: 'Events',
                        data: [1542, 1205, 850, 430, 125, 52],
                        backgroundColor: [
                            'rgba(255,59,92,0.7)', 'rgba(255,59,92,0.5)',
                            'rgba(56,189,248,0.7)', 'rgba(255,170,0,0.7)',
                            'rgba(124,58,237,0.7)', 'rgba(255,99,132,0.5)',
                        ],
                        borderRadius: 3, borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' }, border: { display: false } },
                        x: { grid: { display: false }, border: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
    }

    // ════════════════════════════════════════════════════════
    // 5. PHISHING DETECTION PAGE  (phishing.html)
    // ════════════════════════════════════════════════════════
    const phishInput      = document.getElementById('phishing-input');
    const charCounter     = document.getElementById('char-counter');
    const analyzePhishBtn = document.getElementById('analyze-phish-btn');

    if (phishInput && analyzePhishBtn) {

        phishInput.addEventListener('input', () => {
            if (charCounter) charCounter.innerText = `${phishInput.value.length} characters`;
        });

        analyzePhishBtn.addEventListener('click', async () => {
            const text = phishInput.value.trim();
            if (!text) {
                alert('Please paste email content before analyzing.');
                return;
            }

            const placeholder = document.getElementById('phishing-placeholder');
            const resultsBox  = document.getElementById('phishing-results');
            const loader      = document.getElementById('phishing-loader');
            const errorEl     = document.getElementById('phishing-error');
            const expBox      = document.getElementById('phishing-explanation');

            if (placeholder) placeholder.classList.add('d-none');
            if (resultsBox)  resultsBox.classList.remove('d-none');
            if (errorEl)     errorEl.classList.add('d-none');
            if (expBox)      expBox.classList.add('d-none');
            if (loader)      loader.classList.remove('d-none');

            try {
                const response = await fetch('/predict_phishing', {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({ emailText: text })   // ✅ app.py attend "emailText"
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
                if (loader) loader.classList.add('d-none');

                // app.py retourne : prediction='Phishing'|'Legitimate', confidence=0-100
                //                   threat_level, probabilities={Phishing, Legitimate}
                const prediction  = data.prediction  || 'ERROR';
                const confidence  = data.confidence  || 0;        // déjà en 0-100
                const threatLevel = data.threat_level || 'N/A';
                const isPhish     = prediction === 'Phishing';

                const predEl = document.getElementById('phishing-prediction');
                if (predEl) {
                    predEl.innerText  = prediction.toUpperCase();
                    predEl.className  = 'display-5 fw-bold font-mono mb-2 '
                        + (isPhish ? 'text-risk' : 'text-accent-green');
                }

                const riskEl = document.getElementById('phishing-risk');
                if (riskEl) {
                    riskEl.innerText = threatLevel.toUpperCase();
                    riskEl.className = 'fw-bold fs-6 px-2 py-1 ms-1 border '
                        + (isPhish ? 'text-risk border-danger' : 'text-accent-green border-success');
                }

                const confText = document.getElementById('phishing-confidence-text');
                const progBar  = document.getElementById('phishing-progress');
                if (confText) confText.innerText = confidence.toFixed(1) + '%';
                if (progBar) {
                    progBar.style.width = confidence + '%';
                    progBar.className   = 'progress-bar progress-bar-striped progress-bar-animated '
                        + (isPhish ? 'bg-danger' : 'bg-success');
                }

                if (expBox) {
                    expBox.classList.remove('d-none');
                    const expText = document.getElementById('phishing-explanation-text');
                    if (expText) {
                        const probP = data.probabilities?.Phishing  ?? '—';
                        const probL = data.probabilities?.Legitimate ?? '—';
                        expText.innerText = isPhish
                            ? `Phishing detected with ${confidence.toFixed(1)}% confidence. P(Phishing)=${probP}% · P(Legitimate)=${probL}%. Do not click links or provide credentials.`
                            : `Email appears legitimate with ${confidence.toFixed(1)}% confidence. P(Legitimate)=${probL}% · P(Phishing)=${probP}%. No phishing indicators detected.`;
                    }
                }

            } catch (err) {
                console.error('Phishing API error:', err);
                if (loader) loader.classList.add('d-none');
                const errBox  = document.getElementById('phishing-error');
                const errText = document.getElementById('phishing-error-text');
                if (errBox)  errBox.classList.remove('d-none');
                if (errText) errText.innerText = 'Error: ' + err.message + ' — Make sure Flask is running on port 5000.';
            }
        });
    }

    // ════════════════════════════════════════════════════════
    // 6a. IDS — VERSION BOUTONS  (ids.html avec sim-btn)
    // Utilisé par le ids.html avec les boutons Normal/DDoS/PortScan/etc.
    // La logique JS est inline dans ce ids.html — rien à faire ici.
    // ════════════════════════════════════════════════════════

    // ════════════════════════════════════════════════════════
    // 6b. IDS — VERSION DROPDOWN SELECT  (ids.html avec ids-sample-select)
    // ════════════════════════════════════════════════════════
    const idsSelect     = document.getElementById('ids-sample-select');
    const analyzeIdsBtn = document.getElementById('analyze-ids-btn');

    const IDS_SAMPLES = {
        normal:     [80,166,1,0,0,0,0,0,0,0,6024,83,0,83,83,0,0,0,0,0,0,0,0,0,0,20,0,0,0,0,0,0,0,0,0,0,1,0,0,0,8192,5840,0,20,0,0,0],
        ddos:       [80,15,50,3000,60,60,60,60,60,200000,3333,4.5,2.1,15,1,4.5,2.1,1,0,0,0,0,0,0,0,100,0,3333,60,60,60,0,0,1,0,0,1,0,0,0,8192,0,50,20,0,0,0],
        portscan:   [4444,100,1,0,0,0,0,0,0,0,10000,100,0,100,100,100,0,100,0,0,0,0,0,0,0,20,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1024,0,0,20,0,0,0],
        bruteforce: [22,500,3,120,40,40,40,0,0,240,6000,167,0,500,100,167,0,100,0,0,0,0,0,0,0,60,0,0,40,40,40,0,0,1,0,0,1,0,0,0,4096,0,3,20,0,0,0]
    };

    if (idsSelect && analyzeIdsBtn && !document.getElementById('file-dropzone')) {
        analyzeIdsBtn.addEventListener('click', async () => {
            const sampleType = idsSelect.value;
            const features   = IDS_SAMPLES[sampleType] || IDS_SAMPLES.normal;

            const placeholder = document.getElementById('ids-placeholder');
            const resultsBox  = document.getElementById('ids-results');
            const loader      = document.getElementById('ids-loader');
            const errorEl     = document.getElementById('ids-error');

            if (placeholder) placeholder.classList.add('d-none');
            if (resultsBox)  resultsBox.classList.remove('d-none');
            if (errorEl)     errorEl.classList.add('d-none');
            if (loader)      loader.classList.remove('d-none');

            try {
                const response = await fetch('/predict_ids', {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({ features })   // ✅ envoie le tableau de 47 features
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
                if (loader) loader.classList.add('d-none');
                renderIdsResult(data, 'ids-prediction', 'ids-risk', 'ids-confidence-text', 'ids-progress', 'ids-top-preds');
            } catch (err) {
                if (loader) loader.classList.add('d-none');
                const errBox  = document.getElementById('ids-error');
                const errText = document.getElementById('ids-error-text');
                if (errBox)  errBox.classList.remove('d-none');
                if (errText) errText.innerText = 'Error: ' + err.message + ' — Make sure Flask is running on port 5000.';
            }
        });
    }

    // ════════════════════════════════════════════════════════
    // 6c. IDS — VERSION CSV UPLOAD  (ids.html avec file-dropzone)
    // ════════════════════════════════════════════════════════
    const fileDropzone    = document.getElementById('file-dropzone');
    const fileInput       = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const analyzeIdsFileBtn = analyzeIdsBtn; // même ID dans les deux versions

    let currentUploadedFile = null;

    if (fileDropzone && fileInput && analyzeIdsFileBtn) {

        // Drag & Drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
            fileDropzone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); });
        });
        ['dragenter', 'dragover'].forEach(ev => {
            fileDropzone.addEventListener(ev, () => fileDropzone.classList.add('dragover'));
        });
        ['dragleave', 'drop'].forEach(ev => {
            fileDropzone.addEventListener(ev, () => fileDropzone.classList.remove('dragover'));
        });
        fileDropzone.addEventListener('drop', e => handleFiles(e.dataTransfer.files));
        fileInput.addEventListener('change', function () { handleFiles(this.files); });

        function handleFiles(files) {
            if (!files.length) return;
            const file = files[0];
            if (!file.name.endsWith('.csv')) {
                alert('Please upload a valid CSV file (.csv).');
                currentUploadedFile = null;
                if (fileNameDisplay) fileNameDisplay.classList.add('d-none');
                analyzeIdsFileBtn.setAttribute('disabled', 'true');
                return;
            }
            currentUploadedFile = file;
            if (fileNameDisplay) {
                fileNameDisplay.textContent = `✓ Selected: ${file.name}`;
                fileNameDisplay.classList.remove('d-none');
            }
            const icon = document.getElementById('file-icon');
            if (icon) icon.className = 'fa-solid fa-file-csv fa-3x text-accent-green mb-3';
            analyzeIdsFileBtn.removeAttribute('disabled');
        }

        analyzeIdsFileBtn.addEventListener('click', async () => {
            if (!currentUploadedFile) return;

            const formData = new FormData();
            formData.append('file', currentUploadedFile);

            const placeholder  = document.getElementById('ids-placeholder');
            const finalResults = document.getElementById('ids-final-results');
            const loader       = document.getElementById('ids-loader');
            const errorEl      = document.getElementById('ids-error');

            if (placeholder)  placeholder.classList.add('d-none');
            if (finalResults) finalResults.classList.add('d-none');
            if (errorEl)      errorEl.classList.add('d-none');
            if (loader)       loader.classList.remove('d-none');

            try {
                const response = await fetch('/predict_ids', {
                    method: 'POST',
                    body:   formData              // ✅ multipart — app.py lit request.files['file']
                    // PAS de Content-Type header : le navigateur le met automatiquement avec le boundary
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
                if (loader)       loader.classList.add('d-none');
                if (finalResults) finalResults.classList.remove('d-none');

                // app.py retourne : prediction, confidence (0-100), threat_level, top_predictions
                const prediction  = data.prediction  || 'ERROR';
                const confidence  = data.confidence  || 0;
                const threatLevel = data.threat_level || 'N/A';
                const isNormal    = prediction === 'Normal Traffic' || prediction === 'Normal';

                const predEl = document.getElementById('ids-prediction');
                if (predEl) {
                    predEl.innerText  = prediction.toUpperCase();
                    predEl.className  = 'display-5 fw-bold font-mono mb-2 '
                        + (isNormal ? 'text-accent-green' : 'text-danger');
                }

                const riskEl = document.getElementById('ids-risk');
                if (riskEl) {
                    riskEl.innerText  = threatLevel.toUpperCase();
                    riskEl.className  = 'fw-bold px-2 py-1 ms-1 border '
                        + (isNormal ? 'border-success text-accent-green' : 'border-danger text-danger');
                }

                const confText = document.getElementById('ids-confidence-text');
                const progBar  = document.getElementById('ids-progress');
                if (confText) confText.innerText = confidence.toFixed(1) + '%';  // ✅ déjà 0-100
                if (progBar) {
                    progBar.style.width = confidence + '%';
                    progBar.className   = 'progress-bar progress-bar-striped progress-bar-animated '
                        + (isNormal ? 'bg-success' : 'bg-danger');
                }

                // Top predictions — app.py retourne [{type, prob}]
                const topContainer = document.getElementById('ids-top-preds');
                if (topContainer) {
                    topContainer.innerHTML = '';
                    const preds = data.top_predictions || [];
                    preds.forEach((p, i) => {
                        const label    = p.type  || p.label    || '—';
                        const prob     = parseFloat(p.prob || p.probability || 0); // déjà 0-100
                        const isSafeP  = label === 'Normal Traffic' || label === 'Normal';
                        const barColor = isSafeP ? 'bg-success' : (prob > 50 ? 'bg-danger' : 'bg-warning');
                        topContainer.innerHTML += `
                            <div class="d-flex align-items-center">
                                <div style="width:130px;" class="fw-bold font-mono small text-truncate" title="${label}">
                                    ${i === 0 ? '▶ ' : ''}${label}
                                </div>
                                <div class="flex-grow-1 mx-3">
                                    <div class="progress rounded-0 border border-secondary" style="height:8px;background-color:#000;">
                                        <div class="progress-bar ${barColor}" style="width:${prob}%"></div>
                                    </div>
                                </div>
                                <div style="width:44px;text-align:right;" class="text-gray-400 small font-mono">
                                    ${prob.toFixed(1)}%
                                </div>
                            </div>`;
                    });
                    if (preds.length === 0) {
                        topContainer.innerHTML = '<span class="text-gray-500 small font-mono">No breakdown available.</span>';
                    }
                }

                // Alert message (ids-alert-msg)
                const msgBox = document.getElementById('ids-alert-msg');
                if (msgBox) {
                    if (isNormal) {
                        msgBox.className = 'alert mt-4 font-mono small rounded-0 border mb-0 text-center border-success text-accent-green bg-transparent';
                        msgBox.innerHTML = '<i class="fa-solid fa-check me-2"></i> No malicious anomalies detected in flow sample.';
                    } else {
                        msgBox.className = 'alert mt-4 font-mono small rounded-0 border mb-0 text-center border-danger text-danger bg-transparent';
                        msgBox.innerHTML = '<i class="fa-solid fa-skull me-2"></i> Malicious signature detected. Recommend immediate flow quarantine.';
                    }
                }

            } catch (err) {
                console.error('IDS CSV upload error:', err);
                if (loader) loader.classList.add('d-none');
                if (placeholder) placeholder.classList.remove('d-none');
                const errBox  = document.getElementById('ids-error');
                const errText = document.getElementById('ids-error-text');
                if (errBox)  errBox.classList.remove('d-none');
                if (errText) errText.innerText = 'Error: ' + err.message + ' — Make sure Flask is running on port 5000.';
            }
        });
    }

    // ════════════════════════════════════════════════════════
    // HELPER — render IDS result  (version dropdown)
    // ════════════════════════════════════════════════════════
    function renderIdsResult(data, predId, riskId, confId, progId, topId) {
        const prediction  = data.prediction  || 'ERROR';
        const confidence  = data.confidence  || 0;
        const threatLevel = data.threat_level || 'N/A';
        const isNormal    = prediction === 'Normal Traffic' || prediction === 'Normal';

        const predEl = document.getElementById(predId);
        if (predEl) {
            predEl.innerText = prediction.toUpperCase();
            predEl.className = 'display-5 fw-bold font-mono mb-2 '
                + (isNormal ? 'text-accent-blue' : 'text-accent-red');
        }

        const riskEl = document.getElementById(riskId);
        if (riskEl) {
            riskEl.innerText  = threatLevel.toUpperCase();
            riskEl.className  = 'fw-bold fs-6 px-2 py-1 ms-1 border '
                + (isNormal ? 'border-primary text-accent-blue' : 'border-danger text-accent-red');
        }

        const confText = document.getElementById(confId);
        const progBar  = document.getElementById(progId);
        if (confText) confText.innerText = confidence.toFixed(1) + '%';
        if (progBar) {
            progBar.style.width = confidence + '%';
            progBar.className   = 'progress-bar progress-bar-striped progress-bar-animated '
                + (isNormal ? 'bg-primary' : 'bg-danger');
        }

        const topContainer = document.getElementById(topId);
        if (topContainer) {
            topContainer.innerHTML = '';
            const preds = data.top_predictions || [];
            preds.forEach((p, i) => {
                const label    = p.type || p.label || '—';
                const prob     = parseFloat(p.prob || p.probability || 0);
                const isSafeP  = label === 'Normal Traffic' || label === 'Normal';
                const barColor = isSafeP ? 'bg-primary' : (prob > 50 ? 'bg-danger' : 'bg-warning');
                topContainer.innerHTML += `
                    <div class="d-flex align-items-center gap-2">
                        <div style="width:140px;font-size:.75rem;" class="fw-bold text-truncate" title="${label}">
                            ${i === 0 ? '▶ ' : ''}${label}
                        </div>
                        <div class="flex-grow-1">
                            <div class="progress bg-darker rounded-0 border border-dark" style="height:8px;">
                                <div class="progress-bar ${barColor}" style="width:${prob}%"></div>
                            </div>
                        </div>
                        <div style="width:46px;text-align:right;font-size:.75rem;" class="text-gray-400">
                            ${prob.toFixed(1)}%
                        </div>
                    </div>`;
            });
            if (preds.length === 0) {
                topContainer.innerHTML = '<span class="text-gray-500 small">No breakdown available.</span>';
            }
        }
    }

});