from flask import Flask, render_template, request, jsonify
import random
import time
import numpy as np

try:
    import joblib
except ImportError:
    joblib = None

app = Flask(__name__)

# ==========================================
# CHARGER LES VRAIS MODÈLES ML
# ==========================================
try:
    phishing_model = joblib.load('models/Phishing/best_phishing_model.pkl')
    phishing_vectorizer = joblib.load('models/Phishing/tfidf_vectorizer.pkl')
    phishing_labels = joblib.load('models/Phishing/label_map.pkl')

    ids_model = joblib.load('models/CICIDS2017/cicids2017_best_model_random_forest.joblib')
    ids_scaler = joblib.load('models/CICIDS2017/cicids2017_scaler.joblib')
    ids_labels = joblib.load('models/CICIDS2017/cicids2017_label_map.joblib')

    models_loaded = True
    print("✅ Tous les modèles sont chargés avec succès")
except Exception as e:
    print(f"⚠️  Modèles non chargés (mode mock activé): {e}")
    models_loaded = False


@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/phishing')
def phishing():
    return render_template('phishing.html')

@app.route('/ids')
def ids():
    return render_template('ids.html')


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
        # ── VRAI MODÈLE ML ──
        X = phishing_vectorizer.transform([email_text])
        pred = phishing_model.predict(X)[0]
        prob = phishing_model.predict_proba(X)[0]

        label = phishing_labels[pred]          # 'Legitimate' ou 'Phishing'
        confidence = round(float(prob[pred]) * 100, 2)

        if label == 'Phishing':
            threat = 'High' if confidence > 80 else 'Medium'
        else:
            threat = 'Low'

        return jsonify({
            'prediction':    label,
            'confidence':    confidence,
            'threat_level':  threat,
            'probabilities': {
                'Phishing':   round(float(prob[1]) * 100, 2),
                'Legitimate': round(float(prob[0]) * 100, 2),
            }
        })

    # ── MODE MOCK (si modèles absents) ──
    time.sleep(1.5)
    keywords = ['urgent', 'password', 'bank', 'verify', 'account', 'login', 'click here']
    is_phish = any(w in email_text.lower() for w in keywords) or random.random() > 0.7
    prediction = 'Phishing' if is_phish else 'Legitimate'
    confidence = round(random.uniform(75.0, 99.9), 2)
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
# ENDPOINT IDS
# ==========================================
@app.route('/predict_ids', methods=['POST'])
def predict_ids():
    data = request.json

    if models_loaded:
        # ── VRAI MODÈLE ML ──
        # Si des features sont envoyées depuis le frontend, on les utilise
        features = data.get('features', None)

        if features and len(features) == ids_model.n_features_in_:
            X = np.array(features, dtype=float).reshape(1, -1)
        else:
            # Aucune feature envoyée → on génère un vecteur zéro (Normal Traffic)
            X = np.zeros((1, ids_model.n_features_in_))

        X_scaled = ids_scaler.transform(X)
        pred = ids_model.predict(X_scaled)[0]
        probas = ids_model.predict_proba(X_scaled)[0]
        label = ids_labels[pred]

        # Top-3 prédictions
        top3_idx = np.argsort(probas)[::-1][:3]
        top3 = [
            {
                'type': ids_labels[i],
                'prob': round(float(probas[i]) * 100, 2)
            }
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
    time.sleep(2)
    attacks = ['Normal', 'DDoS', 'PortScan', 'Brute Force', 'Botnet']
    weights = [40, 15, 15, 10, 10]
    prediction = random.choices(attacks, weights=weights, k=1)[0]
    confidence = round(random.uniform(80.0, 99.9), 2)

    threat = 'Low' if prediction == 'Normal' else \
             'Medium' if prediction in ['PortScan', 'Brute Force'] else 'High'

    other = [a for a in attacks if a != prediction]
    random.shuffle(other)
    top3 = [
        {'type': prediction, 'prob': confidence},
        {'type': other[0],   'prob': round(random.uniform(0.1, 10.0), 2)},
        {'type': other[1],   'prob': round(random.uniform(0.1, 5.0),  2)},
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