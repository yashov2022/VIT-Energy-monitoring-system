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
# AUTO DETECT MONTHLY DATABASE
# --------------------------------------------------
HOST = "localhost"
USER = "root"
PASS = ""

conn = mysql.connector.connect(host=HOST, user=USER, password=PASS)
cursor = conn.cursor()

cursor.execute("SHOW DATABASES")
dbs = [d[0] for d in cursor.fetchall()]

month = datetime.now().month
year = datetime.now().year

db_name = None
for db in dbs:
    if db.isdigit() and int(db[:2]) == month and int(db[2:]) == year:
        db_name = db
        break

if db_name is None:
    raise Exception("Monthly database not found")

print("Using database:", db_name)

conn.database = db_name

# --------------------------------------------------
# FETCH DAILY ENERGY DATA
# --------------------------------------------------
query = "SELECT day_date, real_energy FROM energy_17 ORDER BY day_date"
df = pd.read_sql(query, conn)
conn.close()

if len(df) < 8:
    raise Exception("Not enough data to train model (need > 7 days)")
    exit()
data = df["real_energy"].values.reshape(-1, 1)

# --------------------------------------------------
# SCALE DATA
# --------------------------------------------------
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_sjt.pkl"))

# --------------------------------------------------
# CREATE SEQUENCES
# --------------------------------------------------
WINDOW_SIZE = 7
X, y = [], []

for i in range(WINDOW_SIZE, len(data_scaled)):
    X.append(data_scaled[i-WINDOW_SIZE:i])
    y.append(data_scaled[i])

X, y = np.array(X), np.array(y)

# --------------------------------------------------
# BUILD LSTM MODEL
# --------------------------------------------------
model = Sequential([
    LSTM(50, activation='relu', input_shape=(WINDOW_SIZE, 1)),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')

# --------------------------------------------------
# TRAIN
# --------------------------------------------------
model.fit(X, y, epochs=50, verbose=1)

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
model.save(os.path.join(MODEL_DIR, "sjt_lstm.h5"))

print("✅ sjt Model saved successfully")
