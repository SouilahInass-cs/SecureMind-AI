# 🛡️ SecureMind AI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.2-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A unified, AI-powered cybersecurity platform that detects network intrusions and phishing emails in real time using machine learning.**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Models](#-model-performance) • [Dataset](#-dataset) • [Project Structure](#-project-structure)

</div>

---

## 📌 Overview

SecureMind AI combines two trained ML models into a single web application:

- **Network Intrusion Detection System (IDS)** — classifies network traffic into 9 threat categories using a Random Forest trained on the CICIDS2017 dataset (2.5M+ flows).
- **Phishing Email Classifier** — detects phishing emails using TF-IDF vectorization + Random Forest on 82,000+ labeled emails.

Both models are served through a Flask backend and visualized in a dark-themed, glassmorphism dashboard.

---

## ✨ Features

- 🔍 **Real-time phishing detection** — paste any email content and get an instant classification with confidence score and probability breakdown
- 🌐 **Network intrusion detection** — analyze network flow features and classify traffic as Normal, DDoS, DoS, Port Scan, Brute Force, Botnet, or Web Attack
- 📊 **Interactive dashboard** — visualize threat statistics, recent activity, and model confidence
- 🤖 **Mock mode** — runs with simulated predictions if model files are not present, for demo purposes
- 🎨 **Modern UI** — dark theme with glassmorphism cards, animated charts (Chart.js), and responsive layout

---

## 🖥️ Demo

| Dashboard | Phishing Detector | Intrusion Detection |
|:---------:|:-----------------:|:-------------------:|
| Threat stats & charts | Email analysis with confidence scores | Network flow classification |

---

## ⚙️ Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/securemind-ai.git
cd securemind-ai

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Then open your browser at **http://localhost:5000**

> ⚠️ **Note:** The trained model files (`.pkl` / `.joblib`) are not included in this repository due to their size. See the [Models](#-model-performance) section to train them yourself using the provided notebooks.

---

## 📁 Project Structure

```
securemind-ai/
│
├── app.py                          # Flask application — routes & ML inference
├── requirements.txt                # Python dependencies
├── README.md
│
├── models/                         # Trained model artifacts (not tracked by Git)
│   ├── Phishing/
│   │   ├── best_phishing_model.pkl
│   │   ├── tfidf_vectorizer.pkl
│   │   └── label_map.pkl
│   └── CICIDS2017/
│       ├── cicids2017_best_model_random_forest.joblib
│       ├── cicids2017_scaler.joblib
│       └── cicids2017_label_map.joblib
│
├── static/
│   ├── css/
│   │   └── style.css               # Dark glassmorphism theme
│   └── js/
│       └── script.js               # Chart.js charts + fetch API calls
│
├── templates/
│   ├── base.html                   # Shared layout with sidebar navigation
│   ├── index.html                  # Dashboard — stats & charts
│   ├── phishing.html               # Phishing email analyzer
│   └── ids.html                    # Network intrusion detection
│
├── notebooks/
│   ├── CICIDS2017/
│   │   ├── data-preprocessing.ipynb   # Full preprocessing pipeline
│   │   └── model-training.ipynb       # RF & DT training + evaluation
│   └── Phishing/
│       ├── data-preprocessing.ipynb   # Text cleaning & EDA
│       └── model-training.ipynb       # TF-IDF + RF training
│
└── data_output/                    # Cleaned CSVs & train/val/test splits (not tracked)
```

---

## 🧠 Model Performance

All metrics calculated on the held-out test set (15% of data, never seen during training).

| Model | Dataset | Test Accuracy |
|-------|---------|:-------------:|
| Random Forest | CICIDS2017 (Network IDS) | **99.86%** |
| Decision Tree | CICIDS2017 (Network IDS) | **99.83%** |
| Random Forest | Phishing Emails | **95.61%** |

### CICIDS2017 — Class-level results (Random Forest)

| Class | Precision | Recall | F1-Score | Support |
|-------|:---------:|:------:|:--------:|:-------:|
| Normal Traffic | 1.00 | 1.00 | 1.00 | 314,259 |
| DoS | 1.00 | 1.00 | 1.00 | 29,062 |
| DDoS | 1.00 | 1.00 | 1.00 | 19,202 |
| Port Scanning | 0.99 | 1.00 | 0.99 | 13,604 |
| Brute Force | 1.00 | 1.00 | 1.00 | 1,373 |
| Bots | 0.92 | 0.46 | 0.61 | 292 |
| Web Attack – Brute Force | 0.71 | 0.96 | 0.82 | 220 |
| Web Attack – XSS | 0.82 | 0.09 | 0.17 | 98 |
| Web Attack – SQL Injection | 0.00 | 0.00 | 0.00 | 3 |

### Phishing — Class-level results (Random Forest)

| Class | Precision | Recall | F1-Score | Support |
|-------|:---------:|:------:|:--------:|:-------:|
| Legitimate | 0.98 | 0.93 | 0.95 | 5,940 |
| Phishing | 0.94 | 0.98 | 0.96 | 6,433 |

---

## 📊 Dataset

### CICIDS2017 — Network Intrusion Detection

| Property | Value |
|----------|-------|
| Source | Canadian Institute for Cybersecurity |
| Official page | https://www.unb.ca/cic/datasets/ids-2017.html |
| Total samples | 2,830,743 flows |
| After cleaning | 2,520,751 flows |
| Features used | 47 (after correlation filtering & Kruskal-Wallis selection) |
| Classes | 9 (Normal + 8 attack types) |
| Capture period | Monday–Friday, working hours |

**Preprocessing steps:** duplicate removal, identical column removal, inf/NaN dropping, label grouping, correlation filtering (|r| ≥ 0.95), Kruskal-Wallis feature importance, StandardScaler normalization.

### Phishing Email Dataset

| Property | Value |
|----------|-------|
| Total samples | 82,486 emails |
| Classes | 2 (Legitimate / Phishing) |
| Vectorization | TF-IDF, top 5,000 features |
| Split | 70% train / 15% val / 15% test |

---

## 🔌 API Endpoints

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| `POST` | `/predict_phishing` | `{ "emailText": "..." }` | `{ prediction, confidence, threat_level, probabilities }` |
| `POST` | `/predict_ids` | `{ "features": [47 numbers] }` | `{ prediction, confidence, threat_level, top_predictions }` |
| `GET` | `/status` | — | `{ models_loaded, message }` |

---

## 🔁 Training the Models Yourself

```bash
# 1. Download CICIDS2017 CSVs from the official page
#    Place them in: data/CICIDS2017/

# 2. Download the phishing dataset
#    Place it in: data/Phishing/phishing_email.csv

# 3. Run the preprocessing notebooks
jupyter notebook notebooks/CICIDS2017/data-preprocessing.ipynb
jupyter notebook notebooks/Phishing/data-preprocessing.ipynb

# 4. Run the training notebooks
jupyter notebook notebooks/CICIDS2017/model-training.ipynb
jupyter notebook notebooks/Phishing/model-training.ipynb

# 5. The trained artifacts will be saved automatically to models/
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10, Flask 3.0 |
| ML | scikit-learn 1.3, joblib, numpy, pandas |
| NLP | TF-IDF (scikit-learn) |
| Frontend | HTML5, CSS3, Bootstrap 5, Chart.js |
| Notebooks | Jupyter, matplotlib, seaborn, scipy |

---

## 📋 Requirements

```
Flask==3.0.0
joblib==1.3.2
scikit-learn==1.3.2
numpy>=1.24.0
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/) for the CICIDS2017 dataset
- [scikit-learn](https://scikit-learn.org/) for the ML framework
- [Bootstrap](https://getbootstrap.com/) and [Chart.js](https://www.chartjs.org/) for the frontend components

---

<div align="center">
Made with ❤️ for cybersecurity research
</div>
