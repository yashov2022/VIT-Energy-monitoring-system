import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_MAP = {
    "PRP": ("prp_lstm_shifted.keras" ,"scaler_prp_shifted.pkl"),
    "PRP_BI": ("prp_bilstm_shifted.h5", "scaler_prp_bi_shifted.pkl"),

    "SJT": ("sjt_lstm_shifted.keras", "scaler_sjt_shifted.pkl"),
    "SJT_BI": ("sjt_bilstm_shifted.h5", "scaler_sjt_bi_shifted.pkl"),

    "TT": ("tt_lstm_shifted.keras", "scaler_tt_shifted.pkl"),
    "TT_BI": ("tt_bilstm_shifted.h5", "scaler_tt_bi_shifted.pkl"),

    "HPHII": ("hphii_lstm_shifted.keras", "scaler_hphii_shifted.pkl"),
    "HPHII_BI": ("hphii_bilstm_shifted.h5", "scaler_hphii_bi_shifted.pkl"),
}

def predict_next_day_shifted(sequence, model_key):
    model_file, scaler_file = MODEL_MAP[model_key]

    model = load_model(os.path.join(MODEL_DIR, model_file), compile=False)
    scaler = joblib.load(os.path.join(MODEL_DIR, scaler_file))

    data = scaler.transform(np.array(sequence))
    data = data.reshape(1, data.shape[0], data.shape[1])

    pred = model.predict(data, verbose=0)

    # ✅ FIX: handle full sequence output
    pred = pred.reshape(-1,1)

    dummy = np.zeros((len(pred), data.shape[2]))
    dummy[:, 0] = pred[:, 0]

    predictions = scaler.inverse_transform(dummy)[:,0]

    energy = np.max(predictions) - np.min(predictions)

    return float(energy)