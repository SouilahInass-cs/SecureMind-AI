from flask import Flask, render_template, request, jsonify
import random
import time
import numpy as np
import pandas as pd
import io

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

    models_loaded = True
    print("✅ Tous les modèles sont chargés avec succès")
except Exception as e:
    print(f"⚠️  Modèles non chargés (mode mock activé): {e}")
    models_loaded = False


# ==========================================
# ROUTES
# ==========================================
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/phishing')
def phishing():
    return render_template('phishing.html')

@app.route('/ids')
def ids():
    return render_template('ids.html')

@app.route('/status')
def status():
    return jsonify({
        'models_loaded': models_loaded,
        'message': 'Models OK' if models_loaded else 'Running in mock mode'
    })


# ==========================================
# ENDPOINT PHISHING
# ==========================================
@app.route('/predict_phishing', methods=['POST'])
def predict_phishing():
    data = request.json
    email_text = data.get('emailText', '').strip()

    if not email_text:
        return jsonify({'error': 'No email text provided.'}), 400

    if models_loaded:
        X          = phishing_vectorizer.transform([email_text])
        pred       = phishing_model.predict(X)[0]
        prob       = phishing_model.predict_proba(X)[0]
        label      = phishing_labels[pred]
        confidence = round(float(prob[pred]) * 100, 2)
        threat     = 'High' if label == 'Phishing' and confidence > 80 else \
                     'Medium' if label == 'Phishing' else 'Low'

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

    return jsonify({
        'prediction':    prediction,
        'confidence':    confidence,
        'threat_level':  'High' if is_phish else 'Low',
        'probabilities': {
            'Phishing':   round(phishing_prob, 2),
            'Legitimate': round(100 - phishing_prob, 2),
        }
    })


# ==========================================
# HELPER — parse CSV robuste
# Accepte les formats :
#   - une seule ligne de valeurs  (sans header)
#   - header + une ou plusieurs lignes de données
#   - valeurs séparées par virgule ou point-virgule
# ==========================================
def parse_csv_features(file_bytes, n_features=47):
    """
    Lit un fichier CSV uploadé et retourne la première ligne
    de données sous forme de liste de float (longueur = n_features).
    Gère : avec/sans header, séparateur , ou ;
    """
    text = file_bytes.decode('utf-8', errors='replace').strip()

    # ── Essai 1 : lecture avec pandas, séparateur virgule ──
    for sep in [',', ';', '\t']:
        try:
            # header=None : pandas ne traite pas la 1re ligne comme header
            df = pd.read_csv(io.StringIO(text), header=None, sep=sep)

            # Garder uniquement les colonnes numériques
            df_num = df.apply(pd.to_numeric, errors='coerce')

            # Trouver la première ligne ayant assez de valeurs non-NaN
            for idx in range(len(df_num)):
                row = df_num.iloc[idx].dropna().tolist()
                if len(row) >= n_features:
                    return row[:n_features], None   # (features, error)

            # Si pandas a regroupé tout sur une ligne avec mauvais sep, continuer
        except Exception:
            continue

    # ── Essai 2 : parsing manuel ligne par ligne ──
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remplacer point-virgule par virgule
        line = line.replace(';', ',')
        parts = [p.strip() for p in line.split(',')]
        try:
            values = [float(p) for p in parts if p != '']
            if len(values) >= n_features:
                return values[:n_features], None
        except ValueError:
            # Ligne avec des non-numériques (header texte) → ignorer
            continue

    return None, f'Could not find a row with at least {n_features} numeric values in the CSV.'


# ==========================================
# ENDPOINT IDS  (CSV upload  OU  JSON features)
# ==========================================
@app.route('/predict_ids', methods=['POST'])
def predict_ids():
    features = None

    # ── CAS 1 : fichier CSV uploadé (multipart/form-data) ──
    if 'file' in request.files:
        f = request.files['file']

        if not f.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files are accepted.'}), 400

        file_bytes = f.read()
        n_expected = ids_model.n_features_in_ if models_loaded else 47
        features, err = parse_csv_features(file_bytes, n_expected)

        if err:
            return jsonify({'error': f'CSV parse error: {err}'}), 400

    # ── CAS 2 : JSON avec tableau "features" ──
    elif request.is_json:
        body     = request.get_json()
        features = body.get('features', None)

        if features is not None:
            n_expected = ids_model.n_features_in_ if models_loaded else 47
            if len(features) != n_expected:
                # mauvaise longueur → vecteur nul
                features = None

    else:
        return jsonify({
            'error': 'Send a CSV file (multipart) or JSON body with a "features" array.'
        }), 400

    # ── PRÉDICTION ──
    if models_loaded:
        if features is None:
            features = [0.0] * ids_model.n_features_in_

        X        = np.array(features, dtype=float).reshape(1, -1)
        X_scaled = ids_scaler.transform(X)
        pred     = ids_model.predict(X_scaled)[0]
        probas   = ids_model.predict_proba(X_scaled)[0]
        label    = ids_labels[pred]

        top3_idx = np.argsort(probas)[::-1][:3]
        top3     = [
            {'type': ids_labels[i], 'prob': round(float(probas[i]) * 100, 2)}
            for i in top3_idx
        ]
        confidence = round(float(probas[pred]) * 100, 2)

        if label == 'Normal Traffic':
            threat = 'Low'
        elif label in ['Port Scanning', 'Brute Force']:
            threat = 'Medium'
        else:
            threat = 'High'

        return jsonify({
            'prediction':      label,
            'confidence':      confidence,
            'threat_level':    threat,
            'top_predictions': top3,
        })

    # ── MODE MOCK ──
    time.sleep(1)
    attacks    = ['Normal Traffic', 'DDoS', 'Port Scanning', 'Brute Force', 'Bots']
    weights    = [40, 15, 15, 10, 10]
    prediction = random.choices(attacks, weights=weights, k=1)[0]
    confidence = round(random.uniform(80.0, 99.9), 2)

    threat = 'Low'    if prediction == 'Normal Traffic' else \
             'Medium' if prediction in ['Port Scanning', 'Brute Force'] else 'High'

    other = [a for a in attacks if a != prediction]
    random.shuffle(other)
    top3 = [
        {'type': prediction, 'prob': confidence},
        {'type': other[0],   'prob': round(random.uniform(0.1, 10.0), 2)},
        {'type': other[1],   'prob': round(random.uniform(0.1,  5.0), 2)},
    ]
    top3.sort(key=lambda x: x['prob'], reverse=True)

    return jsonify({
        'prediction':      prediction,
        'confidence':      confidence,
        'threat_level':    threat,
        'top_predictions': top3,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)