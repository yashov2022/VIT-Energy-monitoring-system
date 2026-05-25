import mysql.connector
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import joblib
import os
from datetime import datetime

# --------------------------------------------------
# MODEL DIRECTORY
# --------------------------------------------------
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------
HOST = "localhost"
USER = "root"
PASS = ""

table_name = "meitest17"
TARGET_POINTS = 3000

# --------------------------------------------------
# CONNECT TO MYSQL
# --------------------------------------------------
conn = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASS
)

cursor = conn.cursor()

cursor.execute("SHOW DATABASES")
available_dbs = [d[0] for d in cursor.fetchall()]

# --------------------------------------------------
# FETCH DATA FROM PREVIOUS MONTHS ONLY
# --------------------------------------------------
month = datetime.now().month
year = datetime.now().year

# Start from previous month
month -= 1
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

    print("Reading database:", db_name)

    conn.database = db_name

    query = f"""
        SELECT 	RealEnergyWH
        FROM {table_name}
        ORDER BY Datetime DESC
    """

    df = pd.read_sql(query, conn)

    values = df["RealEnergyWH"].tolist()       	

    all_data.extend(values)

    # move to earlier month
    month -= 1
    if month == 0:
        month = 12
        year -= 1

conn.close()

if len(all_data) < TARGET_POINTS:
    raise Exception("Not enough historical data available")

# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------
data = np.array(all_data[:TARGET_POINTS][::-1], dtype=float).reshape(-1,1)

# 🔥 convert cumulative → consumption
energy = data.flatten()

energy_diff = np.diff(energy, prepend=energy[0])
energy_diff = np.clip(energy_diff, 0, None)

# 🔥 amplify signal
energy_diff = energy_diff * 50

data = energy_diff.reshape(-1,1)

# --------------------------------------------------
# SCALE DATA
# --------------------------------------------------
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_sjt.pkl"))

# --------------------------------------------------
# CREATE SEQUENCES
# --------------------------------------------------
WINDOW_SIZE = 288

X, y = [], []

for i in range(WINDOW_SIZE, len(data_scaled)):
    X.append(data_scaled[i-WINDOW_SIZE:i])
    y.append(data_scaled[i])

X, y = np.array(X), np.array(y)

# --------------------------------------------------
# BUILD LSTM MODEL
# --------------------------------------------------
from tensorflow.keras.layers import Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
model = Sequential()

model.add(Input(shape=(WINDOW_SIZE, 1)))

model.add(LSTM(64, return_sequences=True))
model.add(Dropout(0.2))

model.add(LSTM(32))
model.add(Dropout(0.2))

model.add(Dense(16, activation='relu'))
model.add(Dense(1))

model.compile(
    optimizer='adam',
    loss='huber'   # 🔥 change here
)

# --------------------------------------------------
# TRAIN
# --------------------------------------------------
split = int(len(X) * 0.8)

X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=20,
    restore_best_weights=True
)

model.fit(
    X_train,
    y_train,
    epochs=150,
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stop],
    verbose=1
)

# --------------------------------------------------
# PREDICT NEXT DAY (1440 minutes)
# --------------------------------------------------
# --------------------------------------------------
# PREDICT NEXT DAY (FIXED LOOP)
# --------------------------------------------------

future_steps = 1440

last_window = data_scaled[-WINDOW_SIZE:]
current_window = last_window.copy()

predictions = []

for _ in range(future_steps):

    pred = model.predict(
        current_window.reshape(1, WINDOW_SIZE, 1),
        verbose=0
    )

    predictions.append(pred[0][0])

    # 🔥 FIX: proper reshape (this was broken before)
    current_window = np.concatenate(
        (current_window[1:], pred.reshape(1,1)),
        axis=0
    )

predictions = np.array(predictions).reshape(-1,1)

# inverse scaling
predictions_wh = scaler.inverse_transform(predictions).flatten()
predictions_wh = predictions_wh / 50
# revert earlier amplification if you used it
predictions_wh = predictions_wh / 50

# 🔥 AUTO CALIBRATION
actual_mean = np.mean(data[:,0])
pred_mean = np.mean(predictions_wh)

correction_factor = actual_mean / pred_mean
predictions_wh = predictions_wh * correction_factor
# --------------------------------------------------
# DAILY ENERGY
# --------------------------------------------------
daily_energy = predictions_wh.sum()


print("Predicted Daily Energy (Wh):", daily_energy)
print("Predicted Daily Energy (kWh):", daily_energy / 1000)

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
model.save(os.path.join(MODEL_DIR, "sjt_lstm.keras"))

print("✅ sjt Model saved successfully")