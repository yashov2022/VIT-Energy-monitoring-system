# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 13:01:34 2025

@author: Admin
"""

import streamlit as st
import mysql.connector
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Span, FactorRange

# Set page config for a wider layout and custom title/icon
st.set_page_config(layout="wide", page_title="Power Monitoring Dashboard", page_icon="⚡")

# Custom CSS for styling the Streamlit app to match the image
st.markdown(
    """
    <style>
    /* Main app container background */
    .st-emotion-cache-18ni7ap { /* Main app container */
        background-color: #f0f2f6; /* Light grey background */
    }
    .st-emotion-cache-1cypcdb { /* Another part of the main container */
        background-color: #f0f2f6;
    }
    .st-emotion-cache-13ln4j2 { /* More main container styling */
        background-color: #f0f2f6;
    }
    .st-emotion-cache-1f8r84e { /* Another internal Streamlit element */
        background-color: #f0f2f6;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #31336c; /* Dark blue from the image */
        padding-top: 2rem;
        box-shadow: 2px 0 5px rgba(0,0,0,0.1); /* Subtle shadow for sidebar */
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 { /* Sidebar header/title */
        color: #e6e6fa; /* Light white for text */
        font-size: 1.5rem;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 p { /* Paragraphs in sidebar */
        color: #e6e6fa;
        font-size: 1.2rem;
    }

    /* Selectbox styling in sidebar */
    .st-emotion-cache-1n1v2ua { /* The selectbox itself */
        background-color: #4b58a1; /* A slightly lighter blue for the selectbox */
        color: white;
        border-radius: 5px;
        border: none;
    }
    
    .st-emotion-cache-1n1v2ua:hover {
        background-color: #5d6cb9; /* Darker on hover */
    }
    
    .st-emotion-cache-16txt4y p { /* Selectbox label in sidebar */
        font-size: 20px;
        color: white;
    }

    /* Headers and titles */
    h1, h2, h3, h4, h5, h6 {
        color: #31336c; /* Dark blue for titles */
        font-weight: bold;
    }
    
    h4 {
        margin-top: -10px; /* Adjust as needed */
        margin-bottom: 20px;
    }
    
    /* Live Data Page Specific */
    .live-data-title {
        color: #31336c;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 5px;
        margin-top: 0;
    }
    
    .last-updated {
        text-align: right; 
        color: #6c757d; /* Muted grey for timestamp */
        font-size: 0.9rem; 
        margin-top: -30px; 
        margin-bottom: 20px;
    }

    /* Live data cards */
    .data-card {
        text-align: center;
        padding: 0; /* Remove padding from card body to make header flush */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow */
        margin-bottom: 20px;
        transition: transform 0.2s;
        background-color: white; /* White background for the card body */
        border: 1px solid #e0e0e0; /* Light border */
    }
    
    .data-card:hover {
        transform: translateY(-5px); /* Lift effect on hover */
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); /* Slightly stronger shadow on hover */
    }
    
    .data-card-header {
        color: white;
        font-weight: bold;
        padding: 8px 5px; /* Adjust padding for header */
        border-radius: 9px 9px 0 0; /* Rounded top corners, slightly less than card radius */
        font-size: 0.9rem; /* Smaller font for header text */
    }
    
    .data-card-value {
        font-size: 1.8rem; /* Larger font for values */
        font-weight: bold;
        color: #31336c; /* Dark blue for values */
        padding: 10px 0;
        /* background-color: white; - already set on .data-card */
        border-radius: 0 0 10px 10px; /* Rounded bottom corners */
    }

    /* Color-coded headers for live data (matching image) */
    .red-header { background-color: #ef5350; } /* Material Red */
    .yellow-header { background-color: #ffca28; } /* Material Amber */
    .blue-header { background-color: #42a5f5; } /* Material Blue */
    .green-header { background-color: #66bb6a; } /* Material Green */

    /* Other elements */
    .stDateInput input { /* Date input fields */
        border: 2px solid #31336c;
        border-radius: 5px;
    }
    
    /* Bokeh chart title alignment */
    .bk-root .bk-plot-title {
        text-align: center !important;
        font-weight: bold !important;
        color: #31336c !important;
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
            cursor.execute("SHOW TABLES LIKE 'meitest9'") # Changed from meitest6 to meitest9 as in your provided code
            table = cursor.fetchone()
            if table:
                cursor.execute("SELECT * FROM meitest9")
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
        
        # Correctly converting columns to numeric, handling potential errors for robustness
        for col in ["RealPower", "ApparentPower", "ReactivePower", "RealEnergyWH", "ApparentEnergyVAH",
                    "ReactiveEnergyVARHP", "ReactiveEnergyVARHN", "LineVoltageVRY", "LineVoltageVYB",
                    "LineVoltageVBR", "PhaseVoltageVRN", "PhaseVoltageVYN", "PhaseVoltageVBN",
                    "LineCurrentIR", "LineCurrentIY", "LineCurrentIB", "Frequency",
                    "RealPowerR", "RealPowerY", "RealPowerB",
                    "ReactivePowerR", "ReactivePowerY", "ReactivePowerB",
                    "ApparentPowerR", "ApparentPowerY", "ApparentPowerB"]:
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
        
    # Input validation for dates
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
        return
    elif pd.to_datetime(date1).date() < df["date"].min().date() or pd.to_datetime(date2).date() > df["date"].max().date():
        st.error("The selected date range is out of the available data range.")
        return

    # Filter data for the selected date range
    # Ensure correct filtering when date1/date2 might not perfectly align with start/end of day in df
    start_dt = pd.to_datetime(date1).normalize()
    end_dt = pd.to_datetime(date2).normalize() + pd.Timedelta(days=1) - pd.Timedelta(minutes=1) # End of selected day
    
    power_date = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)]
    
    if power_date.empty:
        st.warning("No data available for the selected date range.")
        return
            
    source = ColumnDataSource(power_date)
    p = figure(x_axis_type="datetime", title=f"{power_type.replace('Power', ' Power')} per Minute",
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    p.vbar(x="Datetime", top=power_type, source=source, width=pd.Timedelta(seconds=55), color="#4b58a1")
    hover = HoverTool(tooltips=[("Datetime", "@Datetime{%Y-%m-%d %H:%M}"), (f"{power_type}", f"@{power_type}")],
                      formatters={"@Datetime": "datetime"})
    p.add_tools(hover)
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = f"{power_type} in Watts"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)

def Energy():
    st.subheader("Energy Graph")
    energy_type_label = st.selectbox("Choose Energy", ["RealEnergyWH", "ApparentEnergyVAH", "ReactiveEnergyVARHN", "ReactiveEnergyVARHP"])
    energy_col_df = energy_type_label.replace("K", "") # Remove 'K' for column name if present (e.g., RealEnergyKWH -> RealEnergyWH)
    time_period = st.selectbox("Time Period", ["per day", "per month"])
    
    if df.empty:
        st.warning("No data available to display.")
        return
    
    df_nonzero = df[df[energy_col_df] != 0].copy()

    if df_nonzero.empty:
        st.warning(f"No non-zero data found for {energy_type_label}.")
        return

    if time_period == "per day":
        agg_df = df_nonzero.groupby("date", sort=False)[energy_col_df].agg(
            first='first', last='last'
        ).reset_index()
        
        agg_df[energy_col_df] = agg_df['last'] - agg_df['first'].shift(periods=0)
        agg_df[energy_col_df] = agg_df[energy_col_df].apply(lambda x: 1000000 + x if x < 0 else x) # Handle meter rollover
        
        source = ColumnDataSource(agg_df)
        p = figure(x_axis_type="datetime", title=f"{energy_type_label.replace('EnergyWH', ' Energy in Wh').replace('EnergyVAH', ' Energy in VAh').replace('EnergyVARH', ' Energy in VARh')} per Day",
                    height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
        p.vbar(x="date", top=energy_col_df, source=source, width=pd.Timedelta(hours=23), color="#42a5f5")
        hover = HoverTool(tooltips=[("Date", "@date{%Y-%m-%d}"), (f"{energy_type_label}", f"@{energy_col_df}")],
                          formatters={"@date": "datetime"})
        p.add_tools(hover)
        
    elif time_period == "per month":
        agg_df = df_nonzero.groupby("month", sort=False)[energy_col_df].agg(
            first='first', last='last'
        ).reset_index()
        
        agg_df[energy_col_df] = agg_df['last'] - agg_df['first'].shift(periods=0)
        agg_df[energy_col_df] = agg_df[energy_col_df].apply(lambda x: 1000000 + x if x < 0 else x) # Handle meter rollover
        
        source = ColumnDataSource(agg_df)
        p = figure(x_range=agg_df["month"], title=f"{energy_type_label.replace('EnergyWH', ' Energy in Wh').replace('EnergyVAH', ' Energy in VAh').replace('EnergyVARH', ' Energy in VARh')} per Month",
                    height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
        p.vbar(x="month", top=energy_col_df, width=0.8, source=source, color="#ffca28")
        hover = HoverTool(tooltips=[("Month", "@month"), (f"{energy_type_label}", f"@{energy_col_df}")])
        p.add_tools(hover)
    
    p.xaxis.axis_label = time_period.replace("per ", "By ")
    p.yaxis.axis_label = f"{energy_col_df} in Wh/VAh/VARh"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)
    
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
        
    # Input validation for dates
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
        return
    elif pd.to_datetime(date1).date() < df["date"].min().date() or pd.to_datetime(date2).date() > df["date"].max().date():
        st.error("The selected date range is out of the available data range.")
        return
    
    # Filter data for the selected date range
    start_dt = pd.to_datetime(date1).normalize()
    end_dt = pd.to_datetime(date2).normalize() + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)
    voltage_date = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)]

    if voltage_date.empty:
        st.warning("No data available for the selected date range.")
        return
    
    source = ColumnDataSource(voltage_date)
    p = figure(x_axis_type="datetime", title=f"{voltage_type} per Minute",
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    if voltage_type == "Line Voltage":
        p.line(x="Datetime", y="LineVoltageVRY", source=source, line_width=2, color="#ef5350", legend_label="V_RY")
        p.line(x="Datetime", y="LineVoltageVYB", source=source, line_width=2, color="#ffca28", legend_label="V_YB")
        p.line(x="Datetime", y="LineVoltageVBR", source=source, line_width=2, color="#42a5f5", legend_label="V_BR")
        hline1 = Span(location=440, dimension='width', line_color='red', line_dash="dashed", line_width=2)
        hline2 = Span(location=380, dimension='width', line_color='red', line_dash="dashed", line_width=2)
        p.add_layout(hline1)
        p.add_layout(hline2)
        hover = HoverTool(tooltips=[("Datetime", "@Datetime{%Y-%m-%d %H:%M}"), ("V_RY", "@LineVoltageVRY"),
                              ("V_YB", "@LineVoltageVYB"),
                              ("V_BR", "@LineVoltageVBR")], formatters={"@Datetime": "datetime"})
    else: # Phase Voltage
        p.line(x="Datetime", y="PhaseVoltageVRN", source=source, line_width=2, color="#ef5350", legend_label="V_RN")
        p.line(x="Datetime", y="PhaseVoltageVYN", source=source, line_width=2, color="#ffca28", legend_label="V_YN")
        p.line(x="Datetime", y="PhaseVoltageVBN", source=source, line_width=2, color="#42a5f5", legend_label="V_BN")
        hline1 = Span(location=241.5, dimension='width', line_color='red', line_dash="dashed", line_width=2)
        hline2 = Span(location=218.5, dimension='width', line_color='red', line_dash="dashed", line_width=2)
        p.add_layout(hline1)
        p.add_layout(hline2)
        hover = HoverTool(tooltips=[("Datetime", "@Datetime{%Y-%m-%d %H:%M}"), ("V_RN", "@PhaseVoltageVRN"),
                              ("V_YN", "@PhaseVoltageVYN"),
                              ("V_BN", "@PhaseVoltageVBN")], formatters={"@Datetime": "datetime"})
    
    p.add_tools(hover)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Voltage in Volts"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)
    
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
        
    # Input validation for dates
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
        return
    elif pd.to_datetime(date1).date() < df["date"].min().date() or pd.to_datetime(date2).date() > df["date"].max().date():
        st.error("The selected date range is out of the available data range.")
        return

    # Filter data for the selected date range
    start_dt = pd.to_datetime(date1).normalize()
    end_dt = pd.to_datetime(date2).normalize() + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)
    current_date = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)]

    if current_date.empty:
        st.warning("No data available for the selected date range.")
        return
    
    source = ColumnDataSource(current_date)
    p = figure(x_axis_type="datetime", title="Line Current per Minute",
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    p.line(x="Datetime", y="LineCurrentIR", source=source, line_width=2, color="#ef5350", legend_label="I_R")
    p.line(x="Datetime", y="LineCurrentIY", source=source, line_width=2, color="#ffca28", legend_label="I_Y")
    p.line(x="Datetime", y="LineCurrentIB", source=source, line_width=2, color="#42a5f5", legend_label="I_B")
    
    hover = HoverTool(tooltips=[("Datetime", "@Datetime{%Y-%m-%d %H:%M}"), ("I_R", "@LineCurrentIR"),
                              ("I_Y", "@LineCurrentIY"),
                              ("I_B", "@LineCurrentIB")], formatters={"@Datetime": "datetime"})
    p.add_tools(hover)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Current in Amps"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)
        
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
        
    # Input validation for dates
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
        return
    elif pd.to_datetime(date1).date() < df["date"].min().date() or pd.to_datetime(date2).date() > df["date"].max().date():
        st.error("The selected date range is out of the available data range.")
        return

    # Filter data for the selected date range
    start_dt = pd.to_datetime(date1).normalize()
    end_dt = pd.to_datetime(date2).normalize() + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)
    pf_date = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)]
    
    if pf_date.empty:
        st.warning("No data available for the selected date range.")
        return
            
    source = ColumnDataSource(pf_date)
    
    # Ensure y_values are ordered correctly for FactorRange
    # Extract unique power factors and sort them
    unique_pfs = pf_date["PowerFactor"].unique()
    
    # Convert to numeric for sorting, then back to string for FactorRange
    numeric_pfs = pd.to_numeric(unique_pfs, errors='coerce').dropna()
    sorted_numeric_pfs = sorted(numeric_pfs, reverse=True)
    y_values = [f"{x:.2f}" for x in sorted_numeric_pfs] # Format to 2 decimal places

    p = figure(x_axis_type="datetime", title="Power Factor per Minute",
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save",
               y_range=FactorRange(*y_values)) # Use sorted unique values for y_range
    
    p.scatter(x="Datetime", y="PowerFactor", size=10, source=source, color="#66bb6a", marker="circle") # Changed to scatter for dots, marker for better control
    
    hover = HoverTool(tooltips=[("Date", "@Datetime{%Y-%m-%d %H:%M}"), ("Power Factor", "@PowerFactor")],
                              formatters={"@Datetime": "datetime"})
    p.add_tools(hover)
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Power Factor"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)

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
        
    # Input validation for dates
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
        return
    elif pd.to_datetime(date1).date() < df["date"].min().date() or pd.to_datetime(date2).date() > df["date"].max().date():
        st.error("The selected date range is out of the available data range.")
        return

    # Filter data for the selected date range
    start_dt = pd.to_datetime(date1).normalize()
    end_dt = pd.to_datetime(date2).normalize() + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)
    freq_date = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)]
    
    if freq_date.empty:
        st.warning("No data available for the selected date range.")
        return
            
    source = ColumnDataSource(freq_date)
    p = figure(x_axis_type="datetime", title="Frequency per Minute",
               height=400, sizing_mode="stretch_width", tools="pan,box_zoom,reset,save")
    
    p.vbar(x="Datetime", top="Frequency", width=pd.Timedelta(seconds=55), source=source, color="#ef5350")
    
    hline1 = Span(location=52.5, dimension='width', line_color='red', line_dash="dashed", line_width=2)
    hline2 = Span(location=47.5, dimension='width', line_color='red', line_dash="dashed", line_width=2)
    p.add_layout(hline1)
    p.add_layout(hline2)
    
    hover = HoverTool(tooltips=[("Date", "@Datetime{%Y-%m-%d %H:%M}"), ("Frequency", "@Frequency")],
                              formatters={"@Datetime": "datetime"})
    p.add_tools(hover)
    p.xaxis.axis_label = "Date and Time"
    p.yaxis.axis_label = "Frequency in Hz"
    p.title.align = "center"
    st.bokeh_chart(p, use_container_width=True)

def live_data():
    if df.empty:
        st.warning("No live data available to display.")
        return
    
    st.markdown('<h1 class="live-data-title">Live Data</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="last-updated">Last Updated: {df.iloc[-1]["Datetime"].strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

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
        ("Power Factor", "PowerFactor", "", "green-header"), # No unit for Power Factor
        
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
                # Format float values to 2 decimal places if they are not PowerFactor
                if isinstance(value, (float, int)) and key != "PowerFactor":
                    value = f"{value:.2f}"
                
                # HTML structure for the data card
                with cols[j]:
                    st.markdown(
                        f"""
                        <div class="data-card">
                            <div class="data-card-header {header_class}">
                                <b>{title.replace('_', '<sub>')}{'</sub>'}{f' in {unit}' if unit else ''}</b>
                            </div>
                            <div class="data-card-value">
                                <b>{value}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True
                    )

# ---
# Navigation
st.sidebar.title("Parameters")
page = st.sidebar.selectbox(" ", ("Live Data", "Energy", "Power", "Voltage", "Current", "Power Factor", "Frequency"))

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