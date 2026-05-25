import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_MAP = {
    "PRP": ("prp_lstm.keras" ,"scaler_prp.pkl"),
    "PRP_BI": ("prp_bilstm.h5", "scaler_prp_bi.pkl"),

    "SJT": ("sjt_lstm.keras", "scaler_sjt.pkl"),
    "SJT_BI": ("sjt_bilstm.h5", "scaler_sjt_bi.pkl"),

    "TT": ("tt_lstm.keras", "scaler_tt.pkl"),
    "TT_BI": ("tt_bilstm.h5", "scaler_tt_bi.pkl"),

    "HPHII": ("hphii_lstm.keras", "scaler_hphii.pkl"),
    "HPHII_BI": ("hphii_bilstm.h5", "scaler_hphii_bi.pkl"),
}

def predict_next_day(sequence, model_key):
    model_file, scaler_file = MODEL_MAP[model_key]

    model = load_model(os.path.join(MODEL_DIR, model_file), compile=False)
    scaler = joblib.load(os.path.join(MODEL_DIR, scaler_file))

    data = scaler.transform(np.array(sequence).reshape(-1,1))
    data = data.reshape(1, data.shape[0], 1)

    pred = model.predict(data, verbose=0)
    return float(scaler.inverse_transform(pred)[0][0])
