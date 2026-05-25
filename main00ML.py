#main.py without AI integration
import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")

# --------------------------------------------------
# DATE CONFIG
# --------------------------------------------------
DATE_TODAY = datetime.today().strftime('%d/%m/%Y')
DATE_1 = (datetime.today() - timedelta(1)).strftime('%d/%m/%Y')
DATE_2 = (datetime.today() - timedelta(2)).strftime('%d/%m/%Y')
DATE_3 = (datetime.today() - timedelta(3)).strftime('%d/%m/%Y')
DATE_4 = (datetime.today() - timedelta(4)).strftime('%d/%m/%Y')
DATE_5 = (datetime.today() - timedelta(5)).strftime('%d/%m/%Y')
DATE_6 = (datetime.today() - timedelta(6)).strftime('%d/%m/%Y')

MONTH = datetime.now().month
YEAR = datetime.now().year

HOST_DB_LIST = "10.30.104.235"
HOST_DB_DATA = "localhost"

# --------------------------------------------------
# COLORS (UNCHANGED)
# --------------------------------------------------
VIT_DARK_BLUE = "#2A3B8B"
VIT_LIGHT_BLUE = "#E0E5F0"
VIT_ACCENT_BLUE = "#4682B4"
VIT_BACKGROUND_LIGHT_GREY = "#F5F5F5"
VIT_TEXT_GREY = "#606060"

# --------------------------------------------------
# CSS STYLING (UNCHANGED)
# --------------------------------------------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {VIT_BACKGROUND_LIGHT_GREY};
}}

.styled-image {{
    width: 250px;
    height: auto;
}}

.Page-title {{
    font-size: 22px;
    color: {VIT_DARK_BLUE};
    font-weight: bold;
}}

.display-date {{
    font-size: 14px;
    color: {VIT_ACCENT_BLUE};
    font-weight: bold;
}}

.total-consumption-title {{
    font-size: 22px;
    color: {VIT_DARK_BLUE};
    font-weight: bold;
    text-align: center;
    padding: 8px;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}}

.energy-card-container {{
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    overflow: hidden;
}}

.energy-card-header {{
    background-color: {VIT_ACCENT_BLUE};
    color: white;
    padding: 10px;
    font-weight: bold;
    text-align: center;
}}

.energy-card-body {{
    padding: 12px;
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATABASE UTILITIES (FIXED & SAFE)
# --------------------------------------------------
def get_monthly_db_name():
    try:
        conn = mysql.connector.connect(
            host=HOST_DB_LIST,
            user="root",
            password="",
            connection_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conn.close()

        for db in dbs:
            if db.isdigit():
                if int(db[:2]) == MONTH and int(db[2:]) == YEAR:
                    return db

        st.error("❌ Monthly database not found")
        st.stop()

    except mysql.connector.Error as e:
        st.error(f"MySQL Error: {e}")
        st.stop()


def get_db_connection():
    return mysql.connector.connect(
        host=HOST_DB_DATA,
        user="root",
        password="",
        database=get_monthly_db_name(),
        autocommit=True,
        connection_timeout=5
    )


def safe_cursor(conn):
    try:
        if not conn.is_connected():
            conn.reconnect(attempts=3, delay=2)
        return conn.cursor()
    except mysql.connector.Error as e:
        st.error(f"MySQL reconnect failed: {e}")
        return None


# --------------------------------------------------
# DATA FETCH FUNCTIONS (SAFE)
# --------------------------------------------------
def fetch_energy_data(conn, table, date):
    cursor = safe_cursor(conn)
    if cursor is None:
        return 0.0, 0.0

    try:
        cursor.execute(
            f"""
            SELECT Datetime, RealEnergyWH, RealPower
            FROM {table}
            WHERE Datetime LIKE %s
            """,
            (date + "%",)
        )
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return 0.0, 0.0

        df = pd.DataFrame(rows, columns=["Datetime", "Energy", "Power"])
        df["Energy"] = df["Energy"].astype(float)
        df["Power"] = df["Power"].astype(float)
        df = df[df["Energy"] != 0]

        if df.empty:
            return 0.0, 0.0

        energy = df.iloc[-1]["Energy"] - df.iloc[0]["Energy"]
        if energy < 0:
           energy += 1000000  # Handle rollover
        power = df.iloc[-1]["Power"]

        return round(energy, 2), round(power, 2)

    except mysql.connector.Error as e:
        st.error(f"MySQL Query Error: {e}")
        return 0.0, 0.0


# --------------------------------------------------
# OPEN CONNECTION ONCE
# --------------------------------------------------
conn = get_db_connection()

# --------------------------------------------------
# FETCH TODAY DATA
# --------------------------------------------------
PRP_E, PRP_P = fetch_energy_data(conn, "meitest16", DATE_TODAY)
SJT_E, SJT_P = fetch_energy_data(conn, "meitest17", DATE_TODAY)
TT_E, TT_P = fetch_energy_data(conn, "meitest18", DATE_TODAY)
HPHII_E, HPHII_P = fetch_energy_data(conn, "meitest19", DATE_TODAY)

total_energy_11kV = PRP_E + SJT_E + TT_E + HPHII_E
total_power_11kV = (PRP_P / 1000) + (SJT_P / 1000) + (TT_P / 1e6) + (HPHII_P / 1e6)
# --------------------------------------------------
# TOTAL ENERGY
# --------------------------------------------------
st.markdown(f"""
<div class="total-consumption-title">
    Today's Energy Consumption: {total_energy_11kV:.2f} units
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo = Image.open(os.path.join(BASE_DIR,"vit_logo1.png"))
c1,c2,c3 = st.columns([1,4,2])
with c1: st.image(logo,width=250)
with c2:
    st.markdown('<div class="Page-title">SMART ENERGY MONITORING SYSTEM</div><b>School of Electrical Engineering</b>',unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='text-align:right;color:{VIT_ACCENT_BLUE};font-weight:bold;'>{datetime.now():%d/%m/%Y %H:%M}</div>",unsafe_allow_html=True)


# --------------------------------------------------


# --------------------------------------------------
# DAYWISE STACKED BAR
# --------------------------------------------------
energy_df = pd.DataFrame({
    "Date": [DATE_6, DATE_6, DATE_6, DATE_6,
             DATE_5, DATE_5, DATE_5, DATE_5,
             DATE_4, DATE_4, DATE_4, DATE_4,
             DATE_3, DATE_3, DATE_3, DATE_3,
             DATE_2, DATE_2, DATE_2, DATE_2,
             DATE_1, DATE_1, DATE_1, DATE_1,
             DATE_TODAY, DATE_TODAY, DATE_TODAY, DATE_TODAY],
    "Source": ["PRP", "SJT", "TT", "HPHII"] * 7,
    "Energy": [
        fetch_energy_data(conn, "meitest16", DATE_6)[0], fetch_energy_data(conn, "meitest17", DATE_6)[0],
        fetch_energy_data(conn, "meitest18", DATE_6)[0], fetch_energy_data(conn, "meitest19", DATE_6)[0],
        fetch_energy_data(conn, "meitest16", DATE_5)[0], fetch_energy_data(conn, "meitest17", DATE_5)[0],
        fetch_energy_data(conn, "meitest18", DATE_5)[0], fetch_energy_data(conn, "meitest19", DATE_5)[0],
        fetch_energy_data(conn, "meitest16", DATE_4)[0], fetch_energy_data(conn, "meitest17", DATE_4)[0],
        fetch_energy_data(conn, "meitest18", DATE_4)[0], fetch_energy_data(conn, "meitest19", DATE_4)[0],
        fetch_energy_data(conn, "meitest16", DATE_3)[0], fetch_energy_data(conn, "meitest17", DATE_3)[0],
        fetch_energy_data(conn, "meitest18", DATE_3)[0], fetch_energy_data(conn, "meitest19", DATE_3)[0],
        fetch_energy_data(conn, "meitest16", DATE_2)[0], fetch_energy_data(conn, "meitest17", DATE_2)[0],
        fetch_energy_data(conn, "meitest18", DATE_2)[0], fetch_energy_data(conn, "meitest19", DATE_2)[0],
        fetch_energy_data(conn, "meitest16", DATE_1)[0], fetch_energy_data(conn, "meitest17", DATE_1)[0],
        fetch_energy_data(conn, "meitest18", DATE_1)[0], fetch_energy_data(conn, "meitest19", DATE_1)[0],
        PRP_E, SJT_E, TT_E, HPHII_E
    ]
})

totals_df = energy_df.groupby("Date")["Energy"].sum().reset_index()

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        energy_df,
        x="Date",
        y="Energy",
        color="Source",
        barmode="stack",
        title="Energy Consumption (Units)",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )

    fig1.add_trace(
        go.Scatter(
            x=totals_df["Date"],
            y=totals_df["Energy"],
            text=totals_df["Energy"].round(2),
            mode="text",
            textposition="top center",
            showlegend=False
        )
    )

    fig1.update_layout(showlegend=False, height=420)
    st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------
# PIE CHART
# --------------------------------------------------
with col2:
    if total_power_11kV > 0:
        fig2 = px.pie(
            names=["PRP", "SJT", "TT", "HPHII"],
            values=[PRP_P/1000, SJT_P/1000, TT_P/1e6, HPHII_P/1e6],
            hole=0.7,
            title=f"Real-Time Power: {total_power_11kV:.2f} MW"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Real-time power data not available.")

# --------------------------------------------------
# CARDS
# --------------------------------------------------
def create_11kV_card(title, energy, power, link):
    return f"""
    <div class="energy-card-container">
        <div class="energy-card-header">{title}</div>
        <div class="energy-card-body">
            <p><b>Energy:</b> {energy:.2f} units</p>
            <p><b>Power:</b> {power:.2f} MW</p>
            <a href="{link}" target="_blank">View Meter</a>
        </div>
    </div>
    """

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(create_11kV_card("PRP 11 kV", PRP_E, PRP_P/1000, "http://10.30.104.235:8520"), unsafe_allow_html=True)
with c2:
    st.markdown(create_11kV_card("SJT 11 kV", SJT_E, SJT_P/1000, "http://10.30.104.235:8517"), unsafe_allow_html=True)
with c3:
    st.markdown(create_11kV_card("TT 11 kV", TT_E, TT_P/1e6, "http://10.30.104.235:8518"), unsafe_allow_html=True)
with c4:
    st.markdown(create_11kV_card("HPHII 11 kV", HPHII_E, HPHII_P/1e6, "http://10.30.104.235:8519"), unsafe_allow_html=True)
# --------------------------------------------------
# 🔮 NEXT DAY ENERGY FORECAST (FROM STORED TABLE)
# --------------------------------------------------
def fetch_today_forecast(conn):
    cur = safe_cursor(conn)
    cur.execute("""
        SELECT
            prp_energy,
            sjt_energy,
            tt_energy,
            hphii_energy,
            prp_energy_bi,
            sjt_energy_bi,
            tt_energy_bi,
            hphii_energy_bi
        FROM daily_energy_forecast
        WHERE forecast_date = CURDATE()
    """)
    row = cur.fetchone()
    cur.close()
    return row


# 🔥 UPDATED SHIFT FETCH (NOW INCLUDES BILSTM)
def fetch_today_forecast_shifted(conn):
    cur = safe_cursor(conn)
    cur.execute("""
        SELECT
            prp_energy,
            sjt_energy,
            tt_energy,
            hphii_energy,
            prp_energy_bi,
            sjt_energy_bi,
            tt_energy_bi,
            hphii_energy_bi
        FROM daily_energy_forecast_shifted
        WHERE forecast_date = CURDATE()
    """)
    row = cur.fetchone()
    cur.close()
    return row


# --------------------------------------------------
# FETCH TODAY FORECAST
# --------------------------------------------------

forecast = fetch_today_forecast(conn)
shift_forecast = fetch_today_forecast_shifted(conn)

PRP = SJT = TT = HPHII = None
PRP_BI = SJT_BI = TT_BI = HPHII_BI = None
PRP_SHIFT = SJT_SHIFT = TT_SHIFT = HPHII_SHIFT = None
PRP_SHIFT_BI = SJT_SHIFT_BI = TT_SHIFT_BI = HPHII_SHIFT_BI = None

if forecast:
    (
        PRP,
        SJT,
        TT,
        HPHII,
        PRP_BI,
        SJT_BI,
        TT_BI,
        HPHII_BI,
    ) = forecast

if shift_forecast:
    (
        PRP_SHIFT,
        SJT_SHIFT,
        TT_SHIFT,
        HPHII_SHIFT,
        PRP_SHIFT_BI,
        SJT_SHIFT_BI,
        TT_SHIFT_BI,
        HPHII_SHIFT_BI
    ) = shift_forecast

COLOR_SCHEME = {
    "Actual": "#1f3c88",        # dark blue
    "LSTM": "#4a69bd",          # blue
    "BiLSTM": "#38ada9",        # teal
    "LSTM Shift": "#f6b93b",         # yellow-orange
    "BiLSTM Shift": "#6a1b9a",  # purple
    "PRP": "#1f3c88",
    "SJT": "#4a69bd",
    "TT": "#38ada9",
    "HPHII": "#f6b93b"
}

# --------------------------------------------------
# METRICS DISPLAY
# --------------------------------------------------

st.write("---")
st.subheader("🔮 Next Day Energy Forecast (LSTM vs BiLSTM vs Shift vs BiLSTM Shift)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("PRP LSTM", f"{PRP:.2f} units" if PRP else "Not available")
    st.metric("PRP BiLSTM", f"{PRP_BI:.2f} units" if PRP_BI else "Not available")
    st.metric("PRP Shift", f"{PRP_SHIFT:.2f} units" if PRP_SHIFT else "Not available")
    st.metric("PRP BiLSTM Shift", f"{PRP_SHIFT_BI:.2f} units" if PRP_SHIFT_BI else "Not available")

with col2:
    st.metric("SJT LSTM", f"{SJT:.2f} units" if SJT else "Not available")
    st.metric("SJT BiLSTM", f"{SJT_BI:.2f} units" if SJT_BI else "Not available")
    st.metric("SJT Shift", f"{SJT_SHIFT:.2f} units" if SJT_SHIFT else "Not available")
    st.metric("SJT BiLSTM Shift", f"{SJT_SHIFT_BI:.2f} units" if SJT_SHIFT_BI else "Not available")

with col3:
    st.metric("TT LSTM", f"{TT:.2f} units" if TT else "Not available")
    st.metric("TT BiLSTM", f"{TT_BI:.2f} units" if TT_BI else "Not available")
    st.metric("TT Shift", f"{TT_SHIFT:.2f} units" if TT_SHIFT else "Not available")
    st.metric("TT BiLSTM Shift", f"{TT_SHIFT_BI:.2f} units" if TT_SHIFT_BI else "Not available")

with col4:
    st.metric("HPHII LSTM", f"{HPHII:.2f} units" if HPHII else "Not available")
    st.metric("HPHII BiLSTM", f"{HPHII_BI:.2f} units" if HPHII_BI else "Not available")
    st.metric("HPHII Shift", f"{HPHII_SHIFT:.2f} units" if HPHII_SHIFT else "Not available")
    st.metric("HPHII BiLSTM Shift", f"{HPHII_SHIFT_BI:.2f} units" if HPHII_SHIFT_BI else "Not available")


real_values = [
    PRP_E if 'PRP_E' in globals() else 0,
    SJT_E if 'SJT_E' in globals() else 0,
    TT_E if 'TT_E' in globals() else 0,
    HPHII_E if 'HPHII_E' in globals() else 0,
]
fig = go.Figure()
# --------------------------------------------------
# BAR GRAPH – LSTM vs BiLSTM vs SHIFT vs BI-SHIFT
# --------------------------------------------------

import plotly.graph_objects as go

buildings = ["PRP", "SJT", "TT", "HPHII"]

lstm_values = [PRP or 0, SJT or 0, TT or 0, HPHII or 0]
bilstm_values = [PRP_BI or 0, SJT_BI or 0, TT_BI or 0, HPHII_BI or 0]
shift_values = [PRP_SHIFT or 0, SJT_SHIFT or 0, TT_SHIFT or 0, HPHII_SHIFT or 0]
bilstm_shift_values = [PRP_SHIFT_BI or 0, SJT_SHIFT_BI or 0, TT_SHIFT_BI or 0, HPHII_SHIFT_BI or 0]

fig = go.Figure()

fig.add_trace(go.Bar(x=buildings, y=real_values, name="Actual",
                     marker_color=COLOR_SCHEME["Actual"]))

fig.add_trace(go.Bar(x=buildings, y=lstm_values, name="LSTM",
                     marker_color=COLOR_SCHEME["LSTM"]))

fig.add_trace(go.Bar(x=buildings, y=bilstm_values, name="BiLSTM",
                     marker_color=COLOR_SCHEME["BiLSTM"]))

fig.add_trace(go.Bar(x=buildings, y=shift_values, name="LSTM Shift",
                     marker_color=COLOR_SCHEME["LSTM Shift"]))

fig.add_trace(go.Bar(x=buildings, y=bilstm_shift_values, name="BiLSTM Shift",
                     marker_color=COLOR_SCHEME["BiLSTM Shift"]))

fig.update_layout(
    title="Today's Live Actual vs Predicted Energy Comparison",
    xaxis_title="Buildings",
    yaxis_title="Energy (Units)",
    barmode="group",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# FETCH HISTORY + PREDICTIONS
# --------------------------------------------------

def fetch_history_and_predictions(conn, building, energy_table, days=7):

    cur = conn.cursor()

    # --------------------------------------------------
    # FETCH ACTUAL DATA
    # --------------------------------------------------
    cur.execute(f"""
        SELECT day_date, real_energy
        FROM {energy_table}
        ORDER BY day_date DESC
        LIMIT {days}
    """)

    actual_rows = cur.fetchall()

    if not actual_rows:
        return None, None, None, None, None, None

    actual_rows = actual_rows[::-1]

    dates = [row[0] for row in actual_rows]
    actual_values = [float(row[1]) for row in actual_rows]

    # --------------------------------------------------
    # COLUMN MAPPING
    # --------------------------------------------------
    if building == "PRP":
        col_lstm, col_bi = "prp_energy", "prp_energy_bi"
    elif building == "SJT":
        col_lstm, col_bi = "sjt_energy", "sjt_energy_bi"
    elif building == "TT":
        col_lstm, col_bi = "tt_energy", "tt_energy_bi"
    elif building == "HPHII":
        col_lstm, col_bi = "hphii_energy", "hphii_energy_bi"
    else:
        return None, None, None, None, None, None

    # --------------------------------------------------
    # FETCH NORMAL FORECAST
    # --------------------------------------------------
    cur.execute(f"""
        SELECT forecast_date, {col_lstm}, {col_bi}
        FROM daily_energy_forecast
        ORDER BY forecast_date DESC
        LIMIT {days + 1}
    """)

    pred_rows = cur.fetchall()[::-1]

    # 🔥 SHIFT FIX (critical)
    pred_rows = pred_rows[:-1]

    lstm_values = [float(row[1]) if row[1] else None for row in pred_rows]
    bilstm_values = [float(row[2]) if row[2] else None for row in pred_rows]

    # --------------------------------------------------
    # FETCH SHIFT FORECAST
    # --------------------------------------------------
    cur.execute(f"""
        SELECT forecast_date, {col_lstm}, {col_bi}
        FROM daily_energy_forecast_shifted
        ORDER BY forecast_date DESC
        LIMIT {days + 1}
    """)

    shift_rows = cur.fetchall()[::-1]

    # 🔥 SAME SHIFT FIX
    shift_rows = shift_rows[:-1]

    shift_values = [float(row[1]) if row[1] else None for row in shift_rows]
    shift_bi_values = [float(row[2]) if row[2] else None for row in shift_rows]

    cur.close()

    # --------------------------------------------------
    # ALIGN LENGTHS (SAFETY)
    # --------------------------------------------------
    min_len = min(
        len(dates),
        len(actual_values),
        len(lstm_values),
        len(bilstm_values),
        len(shift_values),
        len(shift_bi_values)
    )

    dates = dates[-min_len:]
    actual_values = actual_values[-min_len:]
    lstm_values = lstm_values[-min_len:]
    bilstm_values = bilstm_values[-min_len:]
    shift_values = shift_values[-min_len:]
    shift_bi_values = shift_bi_values[-min_len:]

    return dates, actual_values, lstm_values, bilstm_values, shift_values, shift_bi_values


# --------------------------------------------------
# PLOT ACTUAL vs PREDICTIONS
# --------------------------------------------------
def plot_actual_vs_pred(dates, actual, lstm, bilstm, shift, shift_bi, building):

    import plotly.graph_objects as go
    import numpy as np
    min_len = min(
    len(actual),
    len(lstm),
    len(bilstm),
    len(shift),
    len(shift_bi),
    len(dates)
)

    dates = dates[-min_len:]
    actual = actual[-min_len:]
    lstm = lstm[-min_len:]
    bilstm = bilstm[-min_len:]
    shift = shift[-min_len:]
    shift_bi = shift_bi[-min_len:] 

    fig = go.Figure()

    models = {
        "LSTM": lstm,
        "BiLSTM": bilstm,
        "LSTM Shift": shift,
        "BiLSTM Shift": shift_bi
    }

    colors = COLOR_SCHEME

    # --------------------------------------------------
    # CALCULATE ERROR %
    # --------------------------------------------------
    errors = {name: [] for name in models}

    for i in range(len(actual)):
        for name, values in models.items():
            if values[i] and actual[i] != 0:
                err = abs(values[i] - actual[i]) / actual[i] * 100
            else:
                err = None
            errors[name].append(err)

    # --------------------------------------------------
    # FIND BEST MODEL PER DAY
    # --------------------------------------------------
    best_model_per_day = []

    for i in range(len(actual)):
        best_model = None
        best_error = float('inf')

        for name in models:
            err = errors[name][i]
            if err is not None and err < best_error:
                best_error = err
                best_model = name

        best_model_per_day.append(best_model)

    # --------------------------------------------------
    # ACTUAL BAR
    # --------------------------------------------------
    fig.add_trace(go.Bar(
        x=dates,
        y=actual,
        name="Actual",
        marker_color=colors["Actual"],
        text=[f"{v:.0f}" for v in actual],
        textposition="outside"
    ))

    # --------------------------------------------------
    # MODEL BARS WITH ERROR %
    # --------------------------------------------------
    for name, values in models.items():

        text_labels = []
        marker_colors = []

        for i, v in enumerate(values):
            if v is None:
                text_labels.append("")
                marker_colors.append(colors[name])
                continue

            err = errors[name][i]

            # 🔥 Show value + error %
            label = f"{v:.0f}<br>({err:.1f}%)" if err else f"{v:.0f}"
            text_labels.append(label)

            # 🔥 Highlight BEST model
            if best_model_per_day[i] == name:
                marker_colors.append("green")   # highlight best
            else:
                marker_colors.append(colors[name])

        fig.add_trace(go.Bar(
            x=dates,
            y=values,
            name=name,
            marker_color=marker_colors,
            text=text_labels,
            textposition="outside"
        ))

    # --------------------------------------------------
    # LAYOUT
    # --------------------------------------------------
    fig.update_layout(
        title=f"{building} - Model Comparison (Best Model Highlighted)",
        xaxis_title="Date",
        yaxis_title="Energy (Units)",
        barmode="group",
        template="plotly_white",
        height=480,

        legend=dict(
            orientation="h",
            y=1.05,
            x=0.5,
            xanchor="center"
        ),

        margin=dict(t=70, b=40, l=40, r=40)
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# MODEL PERFORMANCE
# --------------------------------------------------

st.write("## 📊 Model Performance Comparison")

for building, table in [
    ("PRP", "energy_16"),
    ("SJT", "energy_17"),
    ("TT", "energy_18"),
    ("HPHII", "energy_19")
]:

    result = fetch_history_and_predictions(conn, building, table)

    if result[0]:
        dates, actual, lstm, bilstm, shift, shift_bi = result
        plot_actual_vs_pred(dates, actual, lstm, bilstm, shift, shift_bi, building)


# --------------------------------------------------
# CLOSE
# --------------------------------------------------

conn.close()