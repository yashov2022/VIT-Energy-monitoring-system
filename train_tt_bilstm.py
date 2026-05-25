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

table_name = "meitest19"

TARGET_POINTS = 6000   # ✅ increased
WINDOW_SIZE = 288
OUTPUT_SIZE = 1440

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

    df = pd.read_sql(f"""
        SELECT RealEnergyWH
        FROM {table_name}
        ORDER BY Datetime DESC
    """, conn)

    all_data.extend(df["RealEnergyWH"].tolist())

    month -= 1
    if month == 0:
        month = 12
        year -= 1

conn.close()

# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------
data = np.array(all_data[:TARGET_POINTS][::-1]).reshape(-1,1).astype(np.float32)

# ✅ less aggressive clipping
data = np.clip(data, np.percentile(data, 0.5), np.percentile(data, 99.5))

# --------------------------------------------------
# SCALE
# --------------------------------------------------
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_tt_bi.pkl"))

# --------------------------------------------------
# CREATE SEQ2SEQ DATA
# --------------------------------------------------
X, y = [], []

for i in range(WINDOW_SIZE, len(data_scaled) - OUTPUT_SIZE):
    X.append(data_scaled[i-WINDOW_SIZE:i])
    y.append(data_scaled[i:i+OUTPUT_SIZE])

X = np.array(X)
y = np.array(y).reshape(len(y), OUTPUT_SIZE)

# --------------------------------------------------
# MODEL (IMPROVED BiLSTM)
# --------------------------------------------------
model = Sequential()

model.add(Input(shape=(WINDOW_SIZE, 1)))

# ✅ deeper sequence learning
model.add(Bidirectional(LSTM(64, return_sequences=True)))
model.add(Dropout(0.3))

model.add(Bidirectional(LSTM(32)))
model.add(Dropout(0.3))

# ✅ gradual expansion
model.add(Dense(128, activation='relu'))
model.add(Dense(256, activation='relu'))

model.add(Dense(OUTPUT_SIZE))

# ✅ better for peaks
model.compile(
    optimizer='adam',
    loss='mse'
)

# --------------------------------------------------
# TRAIN
# --------------------------------------------------
split = int(len(X) * 0.8)

X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)

model.fit(
    X_train,
    y_train,
    epochs=200,
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stop],
    verbose=1
)

# --------------------------------------------------
# PREDICT FULL DAY
# --------------------------------------------------
last_window = data_scaled[-WINDOW_SIZE:]

pred_scaled = model.predict(
    last_window.reshape(1, WINDOW_SIZE, 1),
    verbose=0
)

pred_scaled = pred_scaled.reshape(-1,1)

predictions_wh = scaler.inverse_transform(pred_scaled)

# --------------------------------------------------
# DAILY ENERGY
# --------------------------------------------------
max_energy = predictions_wh.max()
min_energy = predictions_wh.min()

daily_energy = max_energy - min_energy

print("Predicted Daily Energy (Wh):", daily_energy)
print("Predicted Daily Energy (kWh):", daily_energy / 1000)

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
model.save(os.path.join(MODEL_DIR, "tt_bilstm.h5"))

print("✅ Improved BiLSTM Model saved successfully")