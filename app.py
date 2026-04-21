from flask import Flask, render_template, request, jsonify
import random
import time
import numpy as np
import pandas as pd
import io
import traceback
from datetime import datetime, timedelta

try:
    import joblib
except ImportError:
    joblib = None

app = Flask(__name__)

# ==========================================
# CHARGER LES VRAIS MODÈLES ML
# ==========================================
try:
    phishing_model      = joblib.load('models/Phishing/best_phishing_model.pkl')
    phishing_vectorizer = joblib.load('models/Phishing/tfidf_vectorizer.pkl')
    phishing_labels     = joblib.load('models/Phishing/label_map.pkl')

    ids_model  = joblib.load('models/CICIDS2017/cicids2017_best_model_random_forest.joblib')
    ids_scaler = joblib.load('models/CICIDS2017/cicids2017_scaler.joblib')
    ids_labels = joblib.load('models/CICIDS2017/cicids2017_label_map.joblib')

    if hasattr(ids_scaler, 'feature_names_in_'):
        FEATURE_NAMES = list(ids_scaler.feature_names_in_)
    elif hasattr(ids_model, 'feature_names_in_'):
        FEATURE_NAMES = list(ids_model.feature_names_in_)
    else:
        FEATURE_NAMES = None

    N_FEATURES    = ids_model.n_features_in_
    models_loaded = True
    print(f"✅ Tous les modèles sont chargés avec succès ({N_FEATURES} features)")

except Exception as e:
    print(f"⚠️  Modèles non chargés (mode mock activé): {e}")
    FEATURE_NAMES = None
    N_FEATURES    = 47
    models_loaded = False

# ==========================================
# SESSION STATS — compteurs en mémoire
# (remis à zéro à chaque redémarrage)
# ==========================================
session_stats = {
    'emails_analyzed':  0,
    'phishing_detected': 0,
    'flows_analyzed':   0,
    'ids_alerts':       0,
    'last_predictions': [],   # liste des 20 dernières prédictions
}

# Historique sur 7 jours simulé (base fixe + variation session)
BASE_HISTORY = {
    'days':        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    'clean':       [3200, 4100, 3800, 4500, 5200, 2900, 2100],
    'malicious':   [120,  250,  180,  310,  480,  95,   60],
}

def add_prediction(category, label, confidence, threat_level):
    """Enregistre une prédiction dans l'historique session."""
    entry = {
        'time':        datetime.now().strftime('%H:%M:%S'),
        'category':    category,    # 'phishing' or 'ids'
        'label':       label,
        'confidence':  confidence,
        'threat':      threat_level,
    }
    session_stats['last_predictions'].insert(0, entry)
    session_stats['last_predictions'] = session_stats['last_predictions'][:20]


# ==========================================
# ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/phishing')
def phishing():
    return render_template('phishing.html')

@app.route('/ids')
def ids():
    return render_template('ids.html')


# ==========================================
# API DASHBOARD — stats dynamiques
# ==========================================
@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Retourne les compteurs de la session courante."""
    total = session_stats['emails_analyzed'] + session_stats['flows_analyzed']
    phish_rate = 0
    if session_stats['emails_analyzed'] > 0:
        phish_rate = round(
            session_stats['phishing_detected'] / session_stats['emails_analyzed'] * 100, 1
        )

    # Déterminer le threat level global
    ids_alerts   = session_stats['ids_alerts']
    phish_detect = session_stats['phishing_detected']
    if ids_alerts > 10 or phish_detect > 5:
        threat_level = 'HIGH'
    elif ids_alerts > 3 or phish_detect > 1:
        threat_level = 'MEDIUM'
    else:
        threat_level = 'LOW'

    return jsonify({
        'models_loaded':   models_loaded,
        'emails_analyzed': session_stats['emails_analyzed'],
        'phish_detected':  session_stats['phishing_detected'],
        'flows_analyzed':  session_stats['flows_analyzed'],
        'ids_alerts':      session_stats['ids_alerts'],
        'phish_rate':      phish_rate,
        'threat_level':    threat_level,
        'ids_accuracy':    99.86,
        'phish_accuracy':  95.61,
        'n_features':      N_FEATURES,
    })


@app.route('/api/dashboard/recent')
def api_dashboard_recent():
    """Retourne les 10 dernières prédictions pour le feed d'activité."""
    return jsonify({
        'predictions': session_stats['last_predictions'][:10]
    })


@app.route('/api/dashboard/chart_data')
def api_dashboard_chart_data():
    """Retourne les données pour les graphiques."""
    # Distribution des classes IDS basée sur les vraies stats CICIDS2017
    ids_distribution = {
        'Normal Traffic': 83.11,
        'DoS':            7.69,
        'DDoS':           5.08,
        'Port Scanning':  3.60,
        'Brute Force':    0.36,
        'Bots':           0.08,
        'Web Attacks':    0.08,
    }

    # Historique 7 jours avec les stats session ajoutées à aujourd'hui
    history = {
        'days':      BASE_HISTORY['days'],
        'clean':     BASE_HISTORY['clean'][:],
        'malicious': BASE_HISTORY['malicious'][:],
    }
    # Ajouter les stats session au dernier jour (aujourd'hui)
    today_idx = datetime.now().weekday()  # 0=Mon, 6=Sun
    history['clean'][today_idx]     += session_stats['flows_analyzed']
    history['malicious'][today_idx] += session_stats['ids_alerts']

    # Graphique menaces dans le temps (24h simulé)
    hours  = [f"{h:02d}:00" for h in range(0, 24, 4)]
    base   = [45, 12, 89, 234, 156, 67]
    # Ajouter le vrai nombre d'alertes à l'heure courante
    curr_slot = datetime.now().hour // 4
    if 0 <= curr_slot < len(base):
        base[curr_slot] += session_stats['ids_alerts'] + session_stats['phishing_detected']

    return jsonify({
        'ids_distribution': ids_distribution,
        'history':          history,
        'threat_timeline':  {'labels': hours, 'values': base},
    })


# ==========================================
# ENDPOINT PHISHING
# ==========================================
@app.route('/predict_phishing', methods=['POST'])
def predict_phishing():
    try:
        data       = request.json
        email_text = data.get('emailText', '').strip()

        if not email_text:
            return jsonify({'error': 'No email text provided.'}), 400

        session_stats['emails_analyzed'] += 1

        if models_loaded:
            X          = phishing_vectorizer.transform([email_text])
            pred       = phishing_model.predict(X)[0]
            prob       = phishing_model.predict_proba(X)[0]
            label      = phishing_labels[pred]
            confidence = round(float(prob[pred]) * 100, 2)
            threat     = 'High'   if label == 'Phishing' and confidence > 80 else \
                         'Medium' if label == 'Phishing' else 'Low'

            if label == 'Phishing':
                session_stats['phishing_detected'] += 1

            add_prediction('phishing', label, confidence, threat)

            return jsonify({
                'prediction':    label,
                'confidence':    confidence,
                'threat_level':  threat,
                'probabilities': {
                    'Phishing':   round(float(prob[1]) * 100, 2),
                    'Legitimate': round(float(prob[0]) * 100, 2),
                }
            })

        # Mock
        time.sleep(1.5)
        keywords      = ['urgent', 'password', 'bank', 'verify', 'account', 'login', 'click here']
        is_phish      = any(w in email_text.lower() for w in keywords) or random.random() > 0.7
        prediction    = 'Phishing' if is_phish else 'Legitimate'
        confidence    = round(random.uniform(75.0, 99.9), 2)
        phishing_prob = confidence if is_phish else 100 - confidence
        threat        = 'High' if is_phish else 'Low'

        if is_phish:
            session_stats['phishing_detected'] += 1

        add_prediction('phishing', prediction, confidence, threat)

        return jsonify({
            'prediction':    prediction,
            'confidence':    confidence,
            'threat_level':  threat,
            'probabilities': {
                'Phishing':   round(phishing_prob, 2),
                'Legitimate': round(100 - phishing_prob, 2),
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ==========================================
# HELPER — parse CSV
# ==========================================
def parse_csv_features(file_bytes, n_features, feature_names=None):
    text = file_bytes.decode('utf-8', errors='replace').strip()
    if not text:
        return None, 'Empty file.'

    for sep in [',', ';', '\t']:
        try:
            df_h   = pd.read_csv(io.StringIO(text), sep=sep)
            df_num = df_h.apply(pd.to_numeric, errors='coerce')

            if feature_names is not None:
                matching = [c for c in feature_names if c in df_num.columns]
                if len(matching) >= n_features * 0.8:
                    row = df_num[feature_names].dropna(axis=1).iloc[0]
                    if len(row) >= n_features:
                        return row.tolist()[:n_features], None

            numeric_cols = df_num.dropna(axis=1, how='all').columns.tolist()
            if len(numeric_cols) >= n_features:
                row = df_num[numeric_cols].iloc[0].dropna().tolist()
                if len(row) >= n_features:
                    return row[:n_features], None
        except Exception:
            pass

    for sep in [',', ';', '\t']:
        try:
            df     = pd.read_csv(io.StringIO(text), header=None, sep=sep)
            df_num = df.apply(pd.to_numeric, errors='coerce')
            for idx in range(len(df_num)):
                row = df_num.iloc[idx].dropna().tolist()
                if len(row) >= n_features:
                    return row[:n_features], None
        except Exception:
            pass

    for line in text.splitlines():
        line  = line.strip().replace(';', ',')
        parts = [p.strip() for p in line.split(',') if p.strip()]
        try:
            values = [float(p) for p in parts]
            if len(values) >= n_features:
                return values[:n_features], None
        except ValueError:
            continue

    return None, f'Could not find a row with {n_features} numeric values.'


# ==========================================
# ENDPOINT IDS
# ==========================================
@app.route('/predict_ids', methods=['POST'])
def predict_ids():
    try:
        features = None

        if 'file' in request.files:
            f = request.files['file']
            if not f.filename.lower().endswith('.csv'):
                return jsonify({'error': 'Only .csv files are accepted.'}), 400
            file_bytes = f.read()
            if not file_bytes:
                return jsonify({'error': 'Uploaded file is empty.'}), 400
            print(f"[IDS] CSV: {f.filename} ({len(file_bytes)} bytes)")
            features, err = parse_csv_features(file_bytes, N_FEATURES, FEATURE_NAMES)
            if err:
                return jsonify({'error': f'CSV parse error: {err}'}), 400
            print(f"[IDS] Features: {len(features)} — premiers: {features[:5]}")

        elif request.is_json:
            body     = request.get_json()
            features = body.get('features', None)
            if features is not None and len(features) != N_FEATURES:
                features = None
        else:
            return jsonify({'error': 'Send a CSV file or JSON with a "features" array.'}), 400

        session_stats['flows_analyzed'] += 1

        if models_loaded:
            if features is None:
                features = [0.0] * N_FEATURES

            if FEATURE_NAMES is not None:
                X = pd.DataFrame([features], columns=FEATURE_NAMES)
            else:
                X = np.array(features, dtype=float).reshape(1, -1)

            X_scaled = ids_scaler.transform(X)
            pred     = ids_model.predict(X_scaled)[0]
            probas   = ids_model.predict_proba(X_scaled)[0]
            label    = ids_labels[pred]

            top3_idx = np.argsort(probas)[::-1][:3]
            top3     = [{'type': ids_labels[i], 'prob': round(float(probas[i]) * 100, 2)}
                        for i in top3_idx]
            confidence = round(float(probas[pred]) * 100, 2)

            if label == 'Normal Traffic':
                threat = 'Low'
            elif label in ['Port Scanning', 'Brute Force']:
                threat = 'Medium'
            else:
                threat = 'High'

            if label != 'Normal Traffic':
                session_stats['ids_alerts'] += 1

            add_prediction('ids', label, confidence, threat)
            print(f"[IDS] → {label} ({confidence}%) Threat: {threat}")

            return jsonify({
                'prediction':      label,
                'confidence':      confidence,
                'threat_level':    threat,
                'top_predictions': top3,
            })

        # Mock
        time.sleep(1)
        attacks    = ['Normal Traffic', 'DDoS', 'Port Scanning', 'Brute Force', 'Bots']
        weights    = [40, 15, 15, 10, 10]
        prediction = random.choices(attacks, weights=weights, k=1)[0]
        confidence = round(random.uniform(80.0, 99.9), 2)
        threat     = 'Low'    if prediction == 'Normal Traffic' else \
                     'Medium' if prediction in ['Port Scanning', 'Brute Force'] else 'High'

        if prediction != 'Normal Traffic':
            session_stats['ids_alerts'] += 1

        other = [a for a in attacks if a != prediction]
        random.shuffle(other)
        top3 = [
            {'type': prediction, 'prob': confidence},
            {'type': other[0],   'prob': round(random.uniform(0.1, 10.0), 2)},
            {'type': other[1],   'prob': round(random.uniform(0.1,  5.0), 2)},
        ]
        top3.sort(key=lambda x: x['prob'], reverse=True)

        add_prediction('ids', prediction, confidence, threat)

        return jsonify({
            'prediction':      prediction,
            'confidence':      confidence,
            'threat_level':    threat,
            'top_predictions': top3,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/status')
def status():
    return jsonify({
        'models_loaded': models_loaded,
        'n_features':    N_FEATURES,
        'message':       'Models OK' if models_loaded else 'Running in mock mode'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)