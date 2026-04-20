# generate_test_samples.py
# ============================================================
# Génère des CSV de test SANS cicids2017_test.csv
# Utilise uniquement les modèles dans models/
#
#   python generate_test_samples.py
# ============================================================

import numpy as np
import pandas as pd
import joblib
import os

SCALER_PATH = 'models/CICIDS2017/cicids2017_scaler.joblib'
MODEL_PATH  = 'models/CICIDS2017/cicids2017_best_model_random_forest.joblib'
LABELS_PATH = 'models/CICIDS2017/cicids2017_label_map.joblib'
OUTPUT_DIR  = 'test_samples'

print("📂 Chargement des modèles...")
model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
labels = joblib.load(LABELS_PATH)

if hasattr(scaler, 'feature_names_in_'):
    feature_names = list(scaler.feature_names_in_)
elif hasattr(model, 'feature_names_in_'):
    feature_names = list(model.feature_names_in_)
else:
    feature_names = [f'feature_{i}' for i in range(model.n_features_in_)]

N = len(feature_names)
print(f"✅ {N} features  |  Classes : {labels}")
print(f"   Ordre features : {feature_names}\n")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Valeurs brutes (avant scaling) ───────────────────────────
# Basées sur les statistiques du dataset CICIDS2017
SAMPLES_RAW = {
    'normal_traffic': [
        80, 166, 1, 0, 0, 0, 0.0, 0, 0,
        0.0, 6024.1, 83.0, 0.0, 83, 83,
        0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0,
        0, 0, 20, 0, 0.0,
        0, 0.0, 0, 0.0,
        0, 0, 0, 0, 1, 0,
        0, 8192, 5840, 0, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
    'ddos_attack': [
        80, 12, 100, 6000, 60, 60, 60.0, 60, 60,
        5000000.0, 8333.3, 0.12, 0.05, 1, 0,
        0.12, 0.05, 0, 0, 0.0, 0.0, 0, 0,
        0, 0, 200, 0, 8333.3,
        60, 60.0, 60, 0.0,
        0, 1, 0, 0, 1, 0,
        0, 8192, 0, 100, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
    'dos_attack': [
        80, 119000000, 3, 0, 0, 0, 0.0, 0, 0,
        0.0, 0.025, 39666666.7, 56399952.0, 119000000, 0,
        39666666.7, 56399952.0, 0, 0, 0.0, 0.0, 0, 0,
        0, 0, 60, 0, 0.0,
        0, 0.0, 0, 0.0,
        0, 0, 1, 0, 0, 0,
        0, 8192, 0, 3, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
    'port_scan': [
        4444, 33, 1, 0, 0, 0, 0.0, 0, 0,
        0.0, 30303.0, 33.0, 0.0, 33, 33,
        0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0,
        0, 0, 20, 0, 0.0,
        0, 0.0, 0, 0.0,
        0, 1, 1, 0, 0, 0,
        0, 1024, 0, 0, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
    'brute_force': [
        21, 130000, 7, 336, 48, 48, 48.0, 110, 110,
        3430.8, 53.8, 21666.7, 25617.0, 72000, 3000,
        10800.0, 15427.3, 1500, 208000, 34666.7, 39741.0, 120000, 4000,
        0, 0, 140, 110, 46.2,
        48, 65.5, 110, 1411.0,
        0, 1, 0, 0, 1, 0,
        0, 65535, 8192, 7, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
    'bots': [
        6881, 30000000, 10, 1500, 150, 150, 150.0, 200, 200,
        56.7, 0.67, 3333333.3, 3534119.4, 12000000, 100000,
        3000000.0, 3162277.6, 100000, 27000000, 3000000.0, 3162277.6, 12000000, 100000,
        0, 0, 200, 200, 0.33,
        150, 171.4, 200, 595.2,
        0, 0, 0, 1, 1, 0,
        1, 65535, 65535, 10, 20,
        0.0, 0.0, 0, 0, 0.0
    ],
}

print("📦 Génération + vérification...\n")
results = []

for name, raw in SAMPLES_RAW.items():
    # Ajuster à N features exactement
    if len(raw) < N:
        raw = raw + [0.0] * (N - len(raw))
    raw = raw[:N]

    df_sample = pd.DataFrame([raw], columns=feature_names)
    out_path  = os.path.join(OUTPUT_DIR, f'{name}.csv')
    df_sample.to_csv(out_path, index=False)

    # Test avec le vrai modèle
    X_scaled   = scaler.transform(df_sample)
    pred_idx   = model.predict(X_scaled)[0]
    pred_label = labels[pred_idx]
    probas     = model.predict_proba(X_scaled)[0]
    confidence = round(float(probas[pred_idx]) * 100, 2)

    results.append((name, pred_label, confidence))
    icon = '✅' if name.split('_')[0] in pred_label.lower().replace(' ', '_') else '⚠️ '
    print(f"{icon} {name}.csv  →  '{pred_label}'  ({confidence}%)")

print("\n" + "─" * 55)
print("📊 RÉSUMÉ FINAL\n")
for name, pred, conf in results:
    bar = '█' * int(conf / 5)
    print(f"  {name+'.csv':28s}  {pred:22s}  {conf:5.1f}%")

print(f"\n✅ {len(results)} fichiers dans '{OUTPUT_DIR}/'")
print("   → Uploadez-les sur la page IDS pour tester le modèle.")
