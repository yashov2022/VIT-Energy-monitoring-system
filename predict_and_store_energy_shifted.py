import mysql.connector
from datetime import datetime
import numpy as np
import joblib
import os
from tensorflow.keras.models import load_model

HOST = "localhost"
USER = "root"
PASS = ""

MODEL_DIR = "models"

# one day minute data
WINDOW_SIZE = 288


# --------------------------------------------------
# LOAD MODEL + SCALER
# --------------------------------------------------

def load_ml_assets(station):

    model_path = os.path.join(MODEL_DIR, f"{station}_lstm_shifted.keras")
    scaler_path = os.path.join(MODEL_DIR, f"scaler_{station}_shifted.pkl")

    model = load_model(model_path)
    scaler = joblib.load(scaler_path)

    return model, scaler


# --------------------------------------------------
# PREDICTION FUNCTION
# --------------------------------------------------
def predict_next_day_shifted(sequence, station):

    model, scaler = load_ml_assets(station)

    # ✅ correct shape (288, 7)
    seq = np.array(sequence)

    # scale
    seq_scaled = scaler.transform(seq)

    # reshape for model
    X = seq_scaled.reshape(1, WINDOW_SIZE, seq.shape[1])

    # ✅ direct prediction (NO LOOP)
    pred_scaled = model.predict(X, verbose=0)

    pred_scaled = pred_scaled.reshape(-1,1)

    # inverse scaling (only energy column)
    dummy = np.zeros((len(pred_scaled), seq.shape[1]))
    dummy[:,0] = pred_scaled[:,0]

    preds = scaler.inverse_transform(dummy)[:,0]

    # daily energy
    energy = np.max(preds) - np.min(preds)
    print(model.input_shape)
    print(scaler.n_features_in_)
    return float(energy)


# --------------------------------------------------
# FIND CURRENT MONTH DATABASE
# --------------------------------------------------

def get_monthly_db():

    conn = mysql.connector.connect(host=HOST, user=USER, password=PASS)
    cursor = conn.cursor()

    cursor.execute("SHOW DATABASES")
    dbs = [d[0] for d in cursor.fetchall()]

    cursor.close()
    conn.close()

    month = datetime.now().month
    year = datetime.now().year

    for db in dbs:
        if db.isdigit() and int(db[:2]) == month and int(db[2:]) == year:
            return db

    return None


# --------------------------------------------------
# FETCH LAST DAY MINUTE DATA
# --------------------------------------------------

def fetch_last_day_minutes(conn, table):

    cursor = conn.cursor()

    # first try current DB
    cursor.execute(f"""
       SELECT
    RealEnergyWH,
    LineVoltageVRY,
    LineVoltageVYB,
    LineVoltageVBR,
    LineCurrentIR,
    LineCurrentIY,
    LineCurrentIB
    from {table}
    ORDER BY Datetime DESC
    LIMIT 288
    """)

    rows = cursor.fetchall()

    # if enough data → return
    if len(rows) >= 288:
        cursor.close()
        return [list(map(float, r)) for r in rows[::-1]]

    # otherwise fetch remaining from previous month
    remaining = 288 - len(rows)

    current_db = conn.database

    month = int(current_db[:2])
    year = int(current_db[2:])

    month -= 1
    if month == 0:
        month = 12
        year -= 1

    prev_db = f"{month:02d}{year}"

    cursor.execute("SHOW DATABASES")
    dbs = [d[0] for d in cursor.fetchall()]

    if prev_db not in dbs:
        cursor.close()
        return None

    # connect to previous DB
    conn.database = prev_db
    cursor.execute(f"""
        SELECT
    RealEnergyWH,
    LineVoltageVRY,
    LineVoltageVYB,
    LineVoltageVBR,
    LineCurrentIR,
    LineCurrentIY,
    LineCurrentIB
     from {table}
     ORDER BY Datetime DESC
        LIMIT {remaining}
    """)

    prev_rows = cursor.fetchall()

    # restore original DB
    conn.database = current_db

    cursor.close()

    combined = prev_rows + rows
    if len(combined) < 288:
        return None

    return [list(map(float, r)) for r in combined[::-1]]

# --------------------------------------------------
# MAIN
# --------------------------------------------------

db_name = get_monthly_db()

if not db_name:
    print("No monthly DB found")
    exit()

conn = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASS,
    database=db_name
)

forecast_date = datetime.now().date()


# fetch sequences
PRP_seq = fetch_last_day_minutes(conn, "meitest16")
SJT_seq = fetch_last_day_minutes(conn, "meitest17")
TT_seq = fetch_last_day_minutes(conn, "meitest18")
HPHII_seq = fetch_last_day_minutes(conn, "meitest19")


# check data availability
if not all([PRP_seq, SJT_seq, TT_seq, HPHII_seq]):
    print("Not enough data for prediction")
    conn.close()
    exit()


# --------------------------------------------------
# MAKE PREDICTIONS
# --------------------------------------------------

PRP_pred = predict_next_day_shifted(PRP_seq, "PRP")
SJT_pred = predict_next_day_shifted(SJT_seq, "SJT")
TT_pred = predict_next_day_shifted(TT_seq, "TT")
HPHII_pred = predict_next_day_shifted(HPHII_seq, "HPHII")
# --------------------------------------------------
# STORE FORECAST
# --------------------------------------------------

cursor = conn.cursor()

insert_query = """
INSERT INTO daily_energy_forecast_shifted
(forecast_date, prp_energy, sjt_energy, tt_energy, hphii_energy)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
prp_energy = VALUES(prp_energy),
sjt_energy = VALUES(sjt_energy),
tt_energy = VALUES(tt_energy),
hphii_energy = VALUES(hphii_energy)
"""
print(PRP_pred)
print(SJT_pred)
print(TT_pred)

cursor.execute(insert_query, (
    forecast_date,
    PRP_pred,
    SJT_pred,
    TT_pred,
    HPHII_pred
))

conn.commit()

cursor.close()
conn.close()

print("✅ Energy forecast stored successfully")