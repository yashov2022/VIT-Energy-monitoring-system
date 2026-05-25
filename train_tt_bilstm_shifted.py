import mysql.connector
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import os
from datetime import datetime

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

HOST = "localhost"
USER = "root"
PASS = ""

table_name = "meitest18"

TARGET_POINTS = 4000
WINDOW_SIZE = 288
OUTPUT_SIZE = 700

# --------------------------------------------------
# FETCH DATA
# --------------------------------------------------
conn = mysql.connector.connect(host=HOST, user=USER, password=PASS)
cursor = conn.cursor()

cursor.execute("SHOW DATABASES")
available_dbs = [d[0] for d in cursor.fetchall()]

month = datetime.now().month - 1
year = datetime.now().year

if month == 0:
    month = 12
    year -= 1

all_data = []

def table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute("SHOW TABLES LIKE %s", (table_name,))
    res = cur.fetchone()
    cur.close()
    return res is not None

while len(all_data) < TARGET_POINTS:

    db_name = f"{month:02d}{year}"

    if db_name not in available_dbs:
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        continue

    print("Reading:", db_name)

    conn.database = db_name

    if not table_exists(conn, table_name):
        print(f"Skipping {db_name}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        continue

    df = pd.read_sql(f"""
        SELECT
            RealEnergyWH,
            LineVoltageVRY,
            LineVoltageVYB,
            LineVoltageVBR,
            LineCurrentIR,
            LineCurrentIY,
            LineCurrentIB
        FROM {table_name}
        ORDER BY Datetime DESC
    """, conn)

    all_data.extend(df.values.tolist())

    month -= 1
    if month == 0:
        month = 12
        year -= 1

conn.close()

# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------
data = np.array(all_data[:TARGET_POINTS][::-1]).astype(np.float32)

# 🔥 CONVERT cumulative → consumption
energy = data[:,0]

energy_diff = np.diff(energy, prepend=energy[0])
energy_diff = np.clip(energy_diff, 0, None)

data[:,0] = energy_diff
# --------------------------------------------------
# SCALE
# --------------------------------------------------
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_tt_bi_shifted.pkl"))

# --------------------------------------------------
# CREATE DATA
# --------------------------------------------------
X, y = [], []

for i in range(WINDOW_SIZE, len(data_scaled) - OUTPUT_SIZE):
    X.append(data_scaled[i-WINDOW_SIZE:i])
    y.append(data_scaled[i:i+OUTPUT_SIZE, 0])

X = np.array(X)
y = np.array(y)

# --------------------------------------------------
# MODEL (REDUCED → LESS OVERFITTING)
# --------------------------------------------------
model = Sequential()

model.add(Input(shape=(WINDOW_SIZE, data.shape[1])))

model.add(Bidirectional(LSTM(32)))   # 🔥 reduced from 64

model.add(Dropout(0.2))             # 🔥 reduced dropout

model.add(Dense(64, activation='relu'))  # 🔥 reduced from 256
model.add(Dense(OUTPUT_SIZE))

model.compile(
    optimizer='adam',
    loss='huber'   # 🔥 better than MAE
)

# --------------------------------------------------
# TRAIN
# --------------------------------------------------
split = int(len(X) * 0.8)

X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,    # 🔥 reduced
    restore_best_weights=True
)

model.fit(
    X_train,
    y_train,
    epochs=50,     # 🔥 reduced from 80
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stop],
    verbose=1
)

# --------------------------------------------------
# PREDICT
# --------------------------------------------------
last_window = data_scaled[-WINDOW_SIZE:]

pred_scaled = model.predict(
    last_window.reshape(1, WINDOW_SIZE, data.shape[1]),
    verbose=0
)

pred_scaled = pred_scaled.reshape(-1,1)

dummy = np.zeros((len(pred_scaled), data.shape[1]))
dummy[:,0] = pred_scaled[:,0]

predictions_wh = scaler.inverse_transform(dummy)[:,0]

# --------------------------------------------------
# 🔥 FIX: DAILY ENERGY (IMPORTANT)
# --------------------------------------------------
daily_energy = predictions_wh.sum()

print("Predicted Daily Energy (Wh):", daily_energy)
print("Predicted Daily Energy (kWh):", daily_energy / 1000)

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
model.save(os.path.join(MODEL_DIR, "tt_bilstm_shifted.h5"))

print("✅ BiLSTM Model saved successfully")