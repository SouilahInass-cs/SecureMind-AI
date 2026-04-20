from flask import Flask, render_template, request, jsonify
import random
import time
import numpy as np
import pandas as pd
import io
import traceback

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

    # ── Récupérer les noms de colonnes attendus par le scaler ──
    if hasattr(ids_scaler, 'feature_names_in_'):
        FEATURE_NAMES = list(ids_scaler.feature_names_in_)
    elif hasattr(ids_model, 'feature_names_in_'):
        FEATURE_NAMES = list(ids_model.feature_names_in_)
    else:
        FEATURE_NAMES = None

    N_FEATURES = ids_model.n_features_in_
    print(f"✅ Tous les modèles sont chargés avec succès")
    print(f"   Features attendues : {N_FEATURES}")
    if FEATURE_NAMES:
        print(f"   Premières features : {FEATURE_NAMES[:5]}")

    models_loaded = True

except Exception as e:
    print(f"⚠️  Modèles non chargés (mode mock activé): {e}")
    FEATURE_NAMES = None
    N_FEATURES    = 47
    models_loaded = False


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

@app.route('/status')
def status():
    return jsonify({
        'models_loaded': models_loaded,
        'n_features':    N_FEATURES,
        'feature_names': FEATURE_NAMES[:5] if FEATURE_NAMES else None,
        'message':       'Models OK' if models_loaded else 'Running in mock mode'
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

        if models_loaded:
            X          = phishing_vectorizer.transform([email_text])
            pred       = phishing_model.predict(X)[0]
            prob       = phishing_model.predict_proba(X)[0]
            label      = phishing_labels[pred]
            confidence = round(float(prob[pred]) * 100, 2)
            threat     = 'High'   if label == 'Phishing' and confidence > 80 else \
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

        # ── Mock ──
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

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ==========================================
# HELPER — parse CSV robuste
# ==========================================
def parse_csv_features(file_bytes, n_features, feature_names=None):
    """
    Lit un fichier CSV uploadé et retourne les features dans le bon ordre.

    Cas gérés :
    1. CSV sans header  → une ligne de n valeurs numériques
    2. CSV avec header  → réordonne les colonnes selon feature_names si dispo
    3. Séparateur , ou ;
    """
    text = file_bytes.decode('utf-8', errors='replace').strip()

    if not text:
        return None, 'Empty file.'

    # ── Essai avec header auto-détecté ──
    for sep in [',', ';', '\t']:
        try:
            # Lire AVEC header (cas normal : fichier exporté avec noms de colonnes)
            df_with_header = pd.read_csv(io.StringIO(text), sep=sep)
            df_num = df_with_header.apply(pd.to_numeric, errors='coerce')

            # Si le CSV a les bons noms de colonnes ET qu'on connaît l'ordre attendu
            if feature_names is not None:
                matching = [c for c in feature_names if c in df_num.columns]
                if len(matching) >= n_features * 0.8:   # ≥ 80% des colonnes reconnues
                    row = df_num[feature_names].dropna(axis=1).iloc[0]
                    if len(row) >= n_features:
                        return row.tolist()[:n_features], None

            # Sinon : prendre les n premières colonnes numériques
            numeric_cols = df_num.dropna(axis=1, how='all').columns.tolist()
            if len(numeric_cols) >= n_features:
                row = df_num[numeric_cols].iloc[0].dropna().tolist()
                if len(row) >= n_features:
                    return row[:n_features], None

        except Exception:
            pass

    # ── Essai sans header (header=None) ──
    for sep in [',', ';', '\t']:
        try:
            df = pd.read_csv(io.StringIO(text), header=None, sep=sep)
            df_num = df.apply(pd.to_numeric, errors='coerce')

            for idx in range(len(df_num)):
                row = df_num.iloc[idx].dropna().tolist()
                if len(row) >= n_features:
                    return row[:n_features], None
        except Exception:
            pass

    # ── Parsing manuel ligne par ligne ──
    for line in text.splitlines():
        line = line.strip().replace(';', ',')
        parts = [p.strip() for p in line.split(',') if p.strip()]
        try:
            values = [float(p) for p in parts]
            if len(values) >= n_features:
                return values[:n_features], None
        except ValueError:
            continue   # ligne avec texte (header) → ignorer

    return None, (
        f'Could not find a row with {n_features} numeric values. '
        f'Make sure your CSV has {n_features} numeric columns.'
    )


# ==========================================
# ENDPOINT IDS  (CSV upload  OU  JSON features)
# ==========================================
@app.route('/predict_ids', methods=['POST'])
def predict_ids():
    try:
        features = None

        # ── CAS 1 : fichier CSV uploadé (multipart/form-data) ──
        if 'file' in request.files:
            f = request.files['file']

            if not f.filename.lower().endswith('.csv'):
                return jsonify({'error': 'Only .csv files are accepted.'}), 400

            file_bytes = f.read()
            if not file_bytes:
                return jsonify({'error': 'Uploaded file is empty.'}), 400

            print(f"[IDS] CSV reçu : {f.filename}  ({len(file_bytes)} bytes)")

            features, err = parse_csv_features(file_bytes, N_FEATURES, FEATURE_NAMES)

            if err:
                print(f"[IDS] CSV parse error: {err}")
                return jsonify({'error': f'CSV parse error: {err}'}), 400

            print(f"[IDS] Features extraites : {len(features)}  — premiers : {features[:5]}")

        # ── CAS 2 : JSON avec tableau "features" ──
        elif request.is_json:
            body     = request.get_json()
            features = body.get('features', None)

            if features is not None and len(features) != N_FEATURES:
                print(f"[IDS] JSON features : longueur {len(features)} ≠ {N_FEATURES} → vecteur nul")
                features = None

        else:
            return jsonify({
                'error': 'Send a CSV file (multipart/form-data) or JSON with a "features" array.'
            }), 400

        # ── PRÉDICTION ──
        if models_loaded:
            if features is None:
                features = [0.0] * N_FEATURES

            # Utiliser un DataFrame avec les noms de colonnes pour éviter les warnings
            if FEATURE_NAMES is not None:
                X = pd.DataFrame([features], columns=FEATURE_NAMES)
            else:
                X = np.array(features, dtype=float).reshape(1, -1)

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

            print(f"[IDS] Résultat : {label}  ({confidence}%)  Threat: {threat}")

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
        threat     = 'Low'    if prediction == 'Normal Traffic' else \
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
    

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)