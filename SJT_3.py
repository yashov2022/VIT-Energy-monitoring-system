# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 13:01:28 2025

@author: Admin
"""

import streamlit as st
import mysql.connector
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Span, FactorRange
from bokeh.palettes import Category10

# Set a more appealing page configuration
st.set_page_config(layout="wide", page_title="Power Monitoring Dashboard", page_icon="⚡")

# Custom CSS for a modern, sleek look
st.markdown(
    """
    <style>
    /* Main container and sidebar styling */
    .st-emotion-cache-18ni7ap{
        background-color: #f0f2f6;
    }
    .st-emotion-cache-1cypcdb {
        background-color: #f0f2f6;
    }
    
    .st-emotion-cache-13ln4j2 {
        background-color: #f0f2f6;
    }
    
    [data-testid="stSidebar"] {
        background-color: #31336c;
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 {
        color: #e6e6fa;
        font-size: 1.5rem;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 p {
        color: #e6e6fa;
        font-size: 1.2rem;
    }

    .st-emotion-cache-1f8r84e{
        background-color: #f0f2f6;
    }
    
    .st-emotion-cache-16txt4y{
        padding-left: 20px;
        background-color: #31336c;
    }
    
    .st-emotion-cache-16txt4y p{
        font-size: 20px;
        color: white;
    }

    /* Selectbox styling */
    .st-emotion-cache-1n1v2ua{
        background-color: #4b58a1;
        color: white;
        border-radius: 5px;
        border: none;
    }
    
    .st-emotion-cache-1n1v2ua:hover{
        background-color: #5d6cb9;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #31336c;
    }
    
    h4 {
        margin-top: -10%;
        margin-bottom: 20px;
    }

    /* Live data cards */
    .data-card {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    
    .data-card:hover {
        transform: translateY(-5px);
    }
    
    .data-card-header {
        color: white;
        font-weight: bold;
        padding: 5px;
        border-radius: 5px 5px 0 0;
    }
    
    .data-card-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #31336c;
        padding: 10px 0;
        background-color: white;
        border-radius: 0 0 10px 10px;
    }

    /* Color-coded headers for live data */
    .red-header { background-color: #ef5350; }
    .yellow-header { background-color: #ffca28; }
    .blue-header { background-color: #42a5f5; }
    .green-header { background-color: #66bb6a; }

    /* Other elements */
    .stDateInput input {
        border: 2px solid #31336c;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True
)

def load_df():
    try:
        conndb = mysql.connector.connect(
            host="10.30.104.235",
            user="root",
            password="",
        )
        cursor = conndb.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [db[0] for db in cursor.fetchall()]
        req_db = [db for db in dbs if db.isdigit() and ((int(db) % 10000 >= 2025 and int(db) / 10000 >= 1))]
        db_list = []
        for db in req_db:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database=db
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'meitest3'")
            table = cursor.fetchone()
            if table:
                cursor.execute("SELECT * FROM meitest3")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                temp_df = pd.DataFrame(rows, columns=columns)
                db_list.append(temp_df)
        
        if not db_list:
            st.warning("No data found in the specified databases.")
            return pd.DataFrame()

        df = pd.concat(db_list)
        df["Datetime"] = df["Datetime"].apply(lambda x: x + ":00" if len(x.split(":")) == 2 else x)
        df["Datetime"] = pd.to_datetime(df["Datetime"], dayfirst=True)
        df["Datetime"] = df["Datetime"].apply(lambda x: x.replace(second=0))
        df.sort_values(by=['Datetime'], inplace=True)
        
        # Convert columns to float
        for col in ["RealPower", "ApparentPower", "ReactivePower", "RealEnergyWH", "ApparentEnergyVAH", 
                     "ReactiveEnergyVARHP", "ReactiveEnergyVARHN", "LineVoltageVRY", "LineVoltageVYB", 
                     "LineVoltageVBR", "PhaseVoltageVRN", "PhaseVoltageVYN", "PhaseVoltageVBN", 
                     "LineCurrentIR", "LineCurrentIY", "LineCurrentIB"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df["hour"] = df["Datetime"].dt.strftime("%Y-%m-%d %H")
        df["hour"] = pd.to_datetime(df["hour"])
        df["date"] = df["Datetime"].dt.date
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["Datetime"].dt.strftime("%b %Y")
        df["year"] = df["Datetime"].dt.strftime("%Y")
        
        df["PowerFactor"] = df["PowerFactor"].replace('-1.00', '1.00').astype(str)
        
        return df

    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return pd.DataFrame()

df = load_df()

def create_power_chart(df_data, power_type, start_date, end_date):
    if df_data.empty:
        return None
    
    start_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(start_date).date()].iloc[0]
    end_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(end_date).date()].iloc[-1]
    power_date = df_data[(df_data["Datetime"] >= start_minute["Datetime"]) & (df_data["Datetime"] <= end_minute["Datetime"])]
    
    if power_date.empty:
        st.warning("No data available for the selected date range.")
        return None
    
    source = ColumnDataSource(power_date)
    p = figure(x_axis_type="datetime", title=f"{power_type.replace('Power', ' Power')} per Minute", 
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    p.vbar(x="Datetime", top=power_type, source=source, width=pd.Timedelta(seconds=55), color=Category10[3][0])
    
    hover = HoverTool(
        tooltips=[("Datetime", "@Datetime{%Y-%m-%d %H:%M}"), (f"{power_type}", f"@{power_type}")],
        formatters={"@Datetime": "datetime"}
    )
    p.add_tools(hover)
    
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = f"{power_type} in Watts"
    p.title.align = "center"
    
    return p

def Power():
    st.subheader("Power Graph")
    power_type = st.selectbox("Choose Power Type", ["RealPower", "ApparentPower", "ReactivePower"])
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        chart = create_power_chart(df, power_type, date1, date2)
        if chart:
            st.bokeh_chart(chart, use_container_width=True)

def create_energy_chart(df_data, energy_type, time_period):
    if df_data.empty:
        return None
    
    if time_period == "per day":
        agg_df = df_data.groupby("date", sort=False)[energy_type].agg(
            first='first', last='last'
        ).reset_index()
        
        agg_df[energy_type] = agg_df['last'] - agg_df['first'].shift(periods=0)
        agg_df[energy_type] = agg_df[energy_type].apply(lambda x: 1000000 + x if x < 0 else x)
        
        source = ColumnDataSource(agg_df)
        p = figure(x_axis_type="datetime", title=f"{energy_type.replace('Energy', ' Energy')} per Day", 
                   height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
        p.vbar(x="date", top=energy_type, source=source, width=pd.Timedelta(hours=23), color=Category10[3][1])
        hover = HoverTool(tooltips=[("Date", "@date{%Y-%m-%d}"), (f"{energy_type}", f"@{energy_type}")], 
                          formatters={"@date": "datetime"})
        
    elif time_period == "per month":
        agg_df = df_data.groupby("month", sort=False)[energy_type].agg(
            first='first', last='last'
        ).reset_index()
        
        agg_df[energy_type] = agg_df['last'] - agg_df['first'].shift(periods=0)
        agg_df[energy_type] = agg_df[energy_type].apply(lambda x: 1000000 + x if x < 0 else x)
        
        source = ColumnDataSource(agg_df)
        p = figure(x_range=agg_df["month"], title=f"{energy_type.replace('Energy', ' Energy')} per Month", 
                   height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
        p.vbar(x="month", top=energy_type, width=0.8, source=source, color=Category10[3][1])
        hover = HoverTool(tooltips=[("Month", "@month"), (f"{energy_type}", f"@{energy_type}")])

    p.add_tools(hover)
    p.title.align = "center"
    p.xaxis.axis_label = time_period.replace("per ", "By ")
    p.yaxis.axis_label = f"{energy_type} in kWh"

    return p

def Energy():
    st.subheader("Energy Graph")
    energy_type = st.selectbox("Choose Energy", ["RealEnergyKWH", "ApparentEnergyKVAH", "ReactiveEnergyKVARHN", "ReactiveEnergyKVARHP"])
    time_period = st.selectbox("Time Period", ["per day", "per month"])
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    energy_col = energy_type.replace("K", "")
    df_nonzero = df[df[energy_col] != 0]
    
    if df_nonzero.empty:
        st.warning(f"No non-zero data found for {energy_type}.")
        return

    chart = create_energy_chart(df_nonzero, energy_col, time_period)
    if chart:
        st.bokeh_chart(chart, use_container_width=True)

def create_voltage_chart(df_data, voltage_type, start_date, end_date):
    if df_data.empty:
        return None
    
    start_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(start_date).date()].iloc[0]
    end_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(end_date).date()].iloc[-1]
    voltage_date = df_data[(df_data["Datetime"] >= start_minute["Datetime"]) & (df_data["Datetime"] <= end_minute["Datetime"])]

    if voltage_date.empty:
        st.warning("No data available for the selected date range.")
        return None
    
    source = ColumnDataSource(voltage_date)
    p = figure(x_axis_type="datetime", title=f"{voltage_type} per Minute", 
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    if voltage_type == "Line Voltage":
        p.line(x="Datetime", y="LineVoltageVRY", source=source, line_width=2, color=Category10[3][0], legend_label="V_RY")
        p.line(x="Datetime", y="LineVoltageVYB", source=source, line_width=2, color=Category10[3][1], legend_label="V_YB")
        p.line(x="Datetime", y="LineVoltageVBR", source=source, line_width=2, color=Category10[3][2], legend_label="V_BR")
        hline1 = Span(location=440, dimension='width', line_color='red', line_dash='dashed', line_width=2)
        hline2 = Span(location=380, dimension='width', line_color='red', line_dash='dashed', line_width=2)
        p.add_layout(hline1)
        p.add_layout(hline2)
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@Datetime{%Y-%m-%d %H:%M}"),
                ("V_RY", "@LineVoltageVRY"),
                ("V_YB", "@LineVoltageVYB"),
                ("V_BR", "@LineVoltageVBR")
            ],
            formatters={"@Datetime": "datetime"}
        )
    else:
        p.line(x="Datetime", y="PhaseVoltageVRN", source=source, line_width=2, color=Category10[3][0], legend_label="V_RN")
        p.line(x="Datetime", y="PhaseVoltageVYN", source=source, line_width=2, color=Category10[3][1], legend_label="V_YN")
        p.line(x="Datetime", y="PhaseVoltageVBN", source=source, line_width=2, color=Category10[3][2], legend_label="V_BN")
        hline1 = Span(location=241.5, dimension='width', line_color='red', line_dash='dashed', line_width=2)
        hline2 = Span(location=218.5, dimension='width', line_color='red', line_dash='dashed', line_width=2)
        p.add_layout(hline1)
        p.add_layout(hline2)
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@Datetime{%Y-%m-%d %H:%M}"),
                ("V_RN", "@PhaseVoltageVRN"),
                ("V_YN", "@PhaseVoltageVYN"),
                ("V_BN", "@PhaseVoltageVBN")
            ],
            formatters={"@Datetime": "datetime"}
        )
    
    p.add_tools(hover)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Voltage in Volts"
    p.title.align = "center"
    
    return p

def Voltage():
    st.subheader("Voltage Graph")
    voltage_type = st.selectbox("Choose Voltage Type", ["Line Voltage", "Phase Voltage"])
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        chart = create_voltage_chart(df, voltage_type, date1, date2)
        if chart:
            st.bokeh_chart(chart, use_container_width=True)

def create_current_chart(df_data, start_date, end_date):
    if df_data.empty:
        return None
    
    start_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(start_date).date()].iloc[0]
    end_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(end_date).date()].iloc[-1]
    current_date = df_data[(df_data["Datetime"] >= start_minute["Datetime"]) & (df_data["Datetime"] <= end_minute["Datetime"])]

    if current_date.empty:
        st.warning("No data available for the selected date range.")
        return None
    
    source = ColumnDataSource(current_date)
    p = figure(x_axis_type="datetime", title="Line Current per Minute", 
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    p.line(x="Datetime", y="LineCurrentIR", source=source, line_width=2, color=Category10[3][0], legend_label="I_R")
    p.line(x="Datetime", y="LineCurrentIY", source=source, line_width=2, color=Category10[3][1], legend_label="I_Y")
    p.line(x="Datetime", y="LineCurrentIB", source=source, line_width=2, color=Category10[3][2], legend_label="I_B")
    
    hover = HoverTool(
        tooltips=[
            ("Datetime", "@Datetime{%Y-%m-%d %H:%M}"),
            ("I_R", "@LineCurrentIR"),
            ("I_Y", "@LineCurrentIY"),
            ("I_B", "@LineCurrentIB")
        ],
        formatters={"@Datetime": "datetime"}
    )
    p.add_tools(hover)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Current in Amps"
    p.title.align = "center"
    
    return p

def Current():
    st.subheader("Current Graph")
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        chart = create_current_chart(df, date1, date2)
        if chart:
            st.bokeh_chart(chart, use_container_width=True)

def create_pf_chart(df_data, start_date, end_date):
    if df_data.empty:
        return None
    
    start_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(start_date).date()].iloc[0]
    end_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(end_date).date()].iloc[-1]
    pf_date = df_data[(df_data["Datetime"] >= start_minute["Datetime"]) & (df_data["Datetime"] <= end_minute["Datetime"])]
    
    if pf_date.empty:
        st.warning("No data available for the selected date range.")
        return None
        
    source = ColumnDataSource(pf_date)
    y_values = sorted(pf_date["PowerFactor"].unique(), reverse=True)
    
    p = figure(
        x_axis_type="datetime", 
        title="Power Factor per Minute", 
        height=400, 
        sizing_mode="stretch_width", 
        tools="pan,box_zoom,reset,save",
        y_range=FactorRange(*y_values)
    )
    
    p.dot(x="Datetime", y="PowerFactor", size=10, source=source, color=Category10[3][2])
    
    hover = HoverTool(
        tooltips=[("Date", "@Datetime{%Y-%m-%d %H:%M}"), ("Power Factor", "@PowerFactor")],
        formatters={"@Datetime": "datetime"}
    )
    p.add_tools(hover)
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Power Factor"
    p.title.align = "center"
    
    return p

def PowerFactor():
    st.subheader("Power Factor Graph")
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        chart = create_pf_chart(df, date1, date2)
        if chart:
            st.bokeh_chart(chart, use_container_width=True)

def create_freq_chart(df_data, start_date, end_date):
    if df_data.empty:
        return None
        
    start_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(start_date).date()].iloc[0]
    end_minute = df_data[df_data["Datetime"].dt.date == pd.to_datetime(end_date).date()].iloc[-1]
    freq_date = df_data[(df_data["Datetime"] >= start_minute["Datetime"]) & (df_data["Datetime"] <= end_minute["Datetime"])]
    
    if freq_date.empty:
        st.warning("No data available for the selected date range.")
        return None
        
    source = ColumnDataSource(freq_date)
    p = figure(x_axis_type="datetime", title="Frequency per Minute", 
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    p.vbar(x="Datetime", top="Frequency", width=pd.Timedelta(seconds=55), source=source, color=Category10[3][0])
    
    hline1 = Span(location=52.5, dimension='width', line_color='red', line_dash='dashed', line_width=2)
    hline2 = Span(location=47.5, dimension='width', line_color='red', line_dash='dashed', line_width=2)
    p.add_layout(hline1)
    p.add_layout(hline2)
    
    hover = HoverTool(
        tooltips=[("Date", "@Datetime{%Y-%m-%d %H:%M}"), ("Frequency", "@Frequency")],
        formatters={"@Datetime": "datetime"}
    )
    p.add_tools(hover)
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Frequency in Hz"
    p.title.align = "center"
    
    return p

def Frequency():
    st.subheader("Frequency Graph")
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        chart = create_freq_chart(df, date1, date2)
        if chart:
            st.bokeh_chart(chart, use_container_width=True)

def live_data():
    if df.empty:
        st.warning("No live data available to display.")
        return
        
    st.title("Live Data")
    st.markdown(f'<div style="text-align: right; color: #31336c; font-size: 1.2rem;">Last Updated: {df.iloc[-1]["Datetime"].strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

    data_points = [
        ("Real Power P_r", "RealPowerR", "Watts", "red-header"),
        ("Real Power P_y", "RealPowerY", "Watts", "yellow-header"),
        ("Real Power P_b", "RealPowerB", "Watts", "blue-header"),
        ("3ph Real Power P", "RealPower", "Watts", "green-header"),
        
        ("Reactive Power Q_r", "ReactivePowerR", "VAR", "red-header"),
        ("Reactive Power Q_y", "ReactivePowerY", "VAR", "yellow-header"),
        ("Reactive Power Q_b", "ReactivePowerB", "VAR", "blue-header"),
        ("3ph Reactive Power Q", "ReactivePower", "VAR", "green-header"),
        
        ("Apparent Power S_r", "ApparentPowerR", "VA", "red-header"),
        ("Apparent Power S_y", "ApparentPowerY", "VA", "yellow-header"),
        ("Apparent Power S_b", "ApparentPowerB", "VA", "blue-header"),
        ("3ph Apparent Power S", "ApparentPower", "VA", "green-header"),
        
        ("Current I_r", "LineCurrentIR", "Amps", "red-header"),
        ("Current I_y", "LineCurrentIY", "Amps", "yellow-header"),
        ("Current I_b", "LineCurrentIB", "Amps", "blue-header"),
        ("Power Factor", "PowerFactor", "", "green-header"),
        
        ("Line Voltage V_ry", "LineVoltageVRY", "Volts", "red-header"),
        ("Line Voltage V_yb", "LineVoltageVYB", "Volts", "yellow-header"),
        ("Line Voltage V_br", "LineVoltageVBR", "Volts", "blue-header"),
        ("Frequency", "Frequency", "Hz", "green-header"),
        
        ("Phase Voltage V_rn", "PhaseVoltageVRN", "Volts", "red-header"),
        ("Phase Voltage V_yn", "PhaseVoltageVYN", "Volts", "yellow-header"),
        ("Phase Voltage V_bn", "PhaseVoltageVBN", "Volts", "blue-header")
    ]
    
    num_cols = 4
    for i in range(0, len(data_points), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(data_points):
                title, key, unit, header_class = data_points[i + j]
                value = df.iloc[-1][key]
                with cols[j]:
                    st.markdown(
                        f"""
                        <div class="data-card">
                            <div class="data-card-header {header_class}">
                                <b>{title.replace('_', '<sub>')}{'</sub>'} in {unit}</b>
                            </div>
                            <div class="data-card-value">
                                <b>{value}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True
                    )
            
# Sidebar for navigation
st.sidebar.title("Parameters")
page = st.sidebar.selectbox(" ", ("Live Data", "Energy", "Power", "Voltage", "Current", "Power Factor", "Frequency"))

# Display the selected page
if page == "Live Data":
    live_data()
elif page == "Energy":
    Energy()
elif page == "Power":
    Power()
elif page == "Voltage":
    Voltage()
elif page == "Current":
    Current()
elif page == "Power Factor":
    PowerFactor()
else:
    Frequency()