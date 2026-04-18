// Initialization
document.addEventListener('DOMContentLoaded', () => {

    // --- DASHBOARD CHARTS ---
    const pieCanvas = document.getElementById('phishingPieChart');
    if (pieCanvas) {
        initCharts();
    }

    // --- PHISHING LOGIC ---
    const phishingForm = document.getElementById('phishingForm');
    if (phishingForm) {
        phishingForm.addEventListener('submit', handlePhishingSubmit);
    }

    // --- IDS LOGIC ---
    const idsForm = document.getElementById('idsForm');
    if (idsForm) {
        idsForm.addEventListener('submit', handleIdsSubmit);
    }
});

// Init Chart.js
function initCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    
    // Pie Chart
    const ctxPie = document.getElementById('phishingPieChart').getContext('2d');
    new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Legitimate', 'Phishing Attempts', 'Spam/Junk'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)', // success
                    'rgba(239, 68, 68, 0.8)', // danger
                    'rgba(245, 158, 11, 0.8)' // warning
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            cutout: '70%'
        }
    });

    // Bar Chart
    const ctxBar = document.getElementById('idsBarChart').getContext('2d');
    new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['DDoS', 'PortScan', 'Brute Force', 'Botnet', 'Infiltration'],
            datasets: [{
                label: 'Events Detected',
                data: [1542, 1205, 850, 430, 177],
                backgroundColor: 'rgba(0, 212, 255, 0.7)',
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Phishing Prediction handler
async function handlePhishingSubmit(e) {
    e.preventDefault();
    
    const emailInput = document.getElementById('emailInput').value;
    const btn = document.getElementById('analyzeEmailBtn');
    const spinner = document.getElementById('phishingSpinner');
    const btnText = btn.querySelector('.btn-text');
    const errorBox = document.getElementById('phishingError');
    
    const placeholder = document.getElementById('phishingPlaceholder');
    const resultBox = document.getElementById('phishingResult');

    // UI Reset
    errorBox.classList.add('d-none');
    
    if(!emailInput.trim()) {
        errorBox.textContent = 'Please enter an email payload to analyze.';
        errorBox.classList.remove('d-none');
        return;
    }

    // Loading State
    btn.disabled = true;
    spinner.classList.remove('d-none');
    btnText.textContent = 'Analyzing NLP Features...';
    placeholder.classList.remove('d-none');
    resultBox.classList.add('d-none');

    try {
        const response = await fetch('/predict_phishing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emailText: emailInput })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        updatePhishingUI(data);

    } catch (error) {
        errorBox.textContent = 'Backend Connection Error: ' + error.message;
        errorBox.classList.remove('d-none');
    } finally {
        // Reset loading UI
        btn.disabled = false;
        spinner.classList.add('d-none');
        btnText.textContent = 'Analyze Email via ML Model';
    }
}

function updatePhishingUI(data) {
    document.getElementById('phishingPlaceholder').classList.add('d-none');
    document.getElementById('phishingResult').classList.remove('d-none');

    const badge = document.getElementById('predictionBadge');
    const threatLevel = document.getElementById('threatLevel');
    const msgBox = document.getElementById('resultMessageBox');
    const msgText = document.getElementById('resultMessageText');

    badge.textContent = data.prediction;
    
    // Theme setup based on result
    if (data.prediction === 'Phishing') {
        badge.className = 'display-6 fw-bold mb-2 text-danger';
        threatLevel.textContent = data.threat_level;
        threatLevel.className = 'fw-bold text-danger';
        
        msgBox.className = 'alert mt-4 glass-alert result-alert alert-danger border-danger';
        msgBox.style.background = 'rgba(239, 68, 68, 0.1)';
        msgText.textContent = 'Malicious intent detected. Do not click any links.';
    } else {
        badge.className = 'display-6 fw-bold mb-2 text-success';
        threatLevel.textContent = data.threat_level;
        threatLevel.className = 'fw-bold text-success';

        msgBox.className = 'alert mt-4 glass-alert result-alert alert-success border-success';
        msgBox.style.background = 'rgba(16, 185, 129, 0.1)';
        msgText.textContent = 'Payload appears benign. Nominal threat.';
    }

    // Progress Bars Animations
    const cBar = document.getElementById('confidenceBar');
    document.getElementById('confidenceScore').textContent = data.confidence + '%';
    cBar.style.width = '0%';
    setTimeout(() => cBar.style.width = data.confidence + '%', 100);

    document.getElementById('probPhish').textContent = data.probabilities.Phishing + '%';
    const bP = document.getElementById('barPhish');
    bP.style.width = '0%';
    setTimeout(() => bP.style.width = data.probabilities.Phishing + '%', 100);

    document.getElementById('probLegit').textContent = data.probabilities.Legitimate + '%';
    const bL = document.getElementById('barLegit');
    bL.style.width = '0%';
    setTimeout(() => bL.style.width = data.probabilities.Legitimate + '%', 100);
}


// IDS Prediction handler
async function handleIdsSubmit(e) {
    e.preventDefault();
    
    const btn = document.getElementById('testTrafficBtn');
    const spinner = document.getElementById('idsSpinner');
    const btnText = btn.querySelector('.btn-text');
    const errorBox = document.getElementById('idsError');
    const termOut = document.getElementById('terminalOutput');
    
    const placeholder = document.getElementById('idsPlaceholder');
    const resultBox = document.getElementById('idsResult');

    // UI Reset
    errorBox.classList.add('d-none');
    
    // Loading State
    btn.disabled = true;
    spinner.classList.remove('d-none');
    btnText.textContent = 'Parsing Packet Trace...';
    placeholder.classList.remove('d-none');
    resultBox.classList.add('d-none');
    
    // Simulate terminal log
    let dots = 0;
    termOut.innerHTML = `> Extracting ${Math.floor(Math.random()*100)+40} network features...<br>> Feeding into Random Forest Model...`;

    try {
        const response = await fetch('/predict_ids', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'test_sample' })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        termOut.innerHTML += `<br>> Classification Complete. <span class="text-accent">OK.</span>`;
        updateIdsUI(data);

    } catch (error) {
        errorBox.textContent = 'Backend Connection Error: ' + error.message;
        errorBox.classList.remove('d-none');
        termOut.innerHTML = `> Error encountered. <span class="text-danger">ABORTED.</span>`;
    } finally {
        // Reset loading UI
        btn.disabled = false;
        spinner.classList.add('d-none');
        btnText.textContent = 'Test Sample Traffic Stream';
    }
}

function updateIdsUI(data) {
    document.getElementById('idsPlaceholder').classList.add('d-none');
    document.getElementById('idsResult').classList.remove('d-none');

    const badge = document.getElementById('idsPredictionBadge');
    const threatBadge = document.getElementById('idsThreatLevel');
    const confScore = document.getElementById('idsConfidenceScore');
    
    badge.textContent = data.prediction;
    confScore.textContent = data.confidence + '%';
    
    // Color coding
    if (data.prediction === 'Normal') {
        badge.className = 'fw-bold mb-1 text-success';
        threatBadge.className = 'badge bg-success rounded-pill px-3';
    } else if (data.threat_level === 'Medium') {
        badge.className = 'fw-bold mb-1 text-warning';
        threatBadge.className = 'badge bg-warning text-dark rounded-pill px-3';
    } else {
        badge.className = 'fw-bold mb-1 text-danger';
        threatBadge.className = 'badge bg-danger rounded-pill px-3';
    }
    threatBadge.textContent = data.threat_level;

    // Top Predictions Table
    const tbody = document.getElementById('idsTopPredictionsTable');
    tbody.innerHTML = ''; // clear previous
    
    data.top_predictions.forEach((item, index) => {
        const tr = document.createElement('tr');
        
        let colorClass = 'bg-secondary';
        if (item.type === 'Normal') colorClass = 'bg-success';
        else if (item.prob > 50) colorClass = 'bg-danger';
        else if (item.prob > 10) colorClass = 'bg-warning';

        tr.innerHTML = `
            <td>#${index + 1}</td>
            <td class="${index === 0 ? 'fw-bold text-white' : ''}">${item.type}</td>
            <td>${item.prob}%</td>
            <td style="width: 40%">
                <div class="progress custom-progress" style="height: 6px;">
                    <div class="progress-bar ${colorClass}" role="progressbar" style="width: ${item.prob}%;"></div>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
