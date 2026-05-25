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
TARGET_POINTS = 5000

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
data = np.array(all_data[:TARGET_POINTS][::-1]).reshape(-1,1)

# --------------------------------------------------
# SCALE DATA
# --------------------------------------------------
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_sjt_bi.pkl"))

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
from tensorflow.keras.layers import Dropout, Input, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping

model = Sequential()

model.add(Input(shape=(WINDOW_SIZE, 1)))

# First BiLSTM layer
model.add(Bidirectional(LSTM(32, return_sequences=True)))
model.add(Dropout(0.2))

# Second BiLSTM layer
model.add(Bidirectional(LSTM(16)))
model.add(Dropout(0.2))

# Dense layers
model.add(Dense(8, activation='relu'))
model.add(Dense(1))
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
    patience=25,
    restore_best_weights=True
)

model.fit(
    X_train,
    y_train,
    epochs=120,
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stop],
    verbose=1
)

# --------------------------------------------------
# PREDICT NEXT DAY (1440 minutes)
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

    current_window = np.append(current_window[1:], pred)

predictions = np.array(predictions).reshape(-1,1)

# inverse scaling
predictions_wh = scaler.inverse_transform(predictions)

# --------------------------------------------------
# CALCULATE DAILY ENERGY
# --------------------------------------------------
max_energy = predictions_wh.max()
min_energy = predictions_wh.min()

daily_energy = max_energy - min_energy

print("Predicted Daily Energy (Wh):", daily_energy)
print("Predicted Daily Energy (kWh):", daily_energy / 1000)

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
model.save(os.path.join(MODEL_DIR, "sjt_bilstm.h5"))

print("✅ sjt Model saved successfully")