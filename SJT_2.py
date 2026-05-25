# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 11:09:47 2025

@author: Admin
"""

import streamlit as st
import mysql.connector
import pandas as pd
from bokeh.plotting import figure,show
from bokeh.models import HoverTool,ColumnDataSource,Span,FactorRange


st.markdown("""<style>
            [data-testid="stHeader"]{
                background-color:lavender;}
            [data-testid="stAppViewContainer"]{
                background-color:lavender;}
            [data-testid="stSidebar"]{
                background-color:indigo;}
           .st-emotion-cache-6qob1r .st-emotion-cache-1whx7iy p {
               font-size:20px;
               color:white;}
           .st-ak{
                background-color:#d7d1fa;
                color:#331966;}
            .st-emotion-cache-s16by7:hover{
                background-color: #331966;
                color:lavender
                }
            .st-cn{
                color:#331966;}
            .st-cu{
                border-color:indigo;}
            .r{
                height:30px;}
            
            </style>""",unsafe_allow_html=True)
def load_df():
    conndb=mysql.connector.connect(
        host="10.30.104.235",
        user="root",
        password="",
    )
    cursor = conndb.cursor()
    cursor.execute("SHOW DATABASES")
    dbs=[db[0] for db in cursor.fetchall()]
    req_db=[db for db in dbs if db.isdigit() and ((int(db)%10000>=2025 and int(db)/10000>=1))]
    db_list=[]
    for db in req_db:
        conn=mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=db
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'meitest2'")
        table=cursor.fetchone()
        if table:
            cursor.execute("SELECT * FROM meitest2")
            rows=cursor.fetchall()
            columns=[desc[0] for desc in cursor.description]
            temp_df = pd.DataFrame(rows,columns=columns)
            db_list.append(temp_df)
    
    df=pd.concat(db_list)
    df["Datetime"]=df["Datetime"].apply(lambda x: x+":00" if len(x.split(":")) == 2 else x)
    df["Datetime"]=pd.to_datetime(df["Datetime"],dayfirst=True)
    df["Datetime"]=df["Datetime"].apply(lambda x:x.replace(second=0))
    df.sort_values(by=['Datetime'], inplace=True)
    df["RealPower"]=df["RealPower"].astype(float)
    df["ApparentPower"]=df["ApparentPower"].astype(float)
    df["ReactivePower"]=df["ReactivePower"].astype(float)
    df["RealEnergyWH"]=df["RealEnergyWH"].astype(float)
    df["ApparentEnergyVAH"]=df["ApparentEnergyVAH"].astype(float)
    df["ReactiveEnergyVARHP"]=df["ReactiveEnergyVARHP"].astype(float)
    df["ReactiveEnergyVARHN"]=df["ReactiveEnergyVARHN"].astype(float)
    df["LineVoltageVRY"]=df["LineVoltageVRY"].astype(float)
    df["LineVoltageVYB"]=df["LineVoltageVYB"].astype(float)
    df["LineVoltageVBR"]=df["LineVoltageVBR"].astype(float)
    df["PhaseVoltageVRN"]=df["PhaseVoltageVRN"].astype(float)
    df["PhaseVoltageVYN"]=df["PhaseVoltageVYN"].astype(float)
    df["PhaseVoltageVBN"]=df["PhaseVoltageVBN"].astype(float)
    df["LineCurrentIR"]=df["LineCurrentIR"].astype(float)
    df["LineCurrentIY"]=df["LineCurrentIY"].astype(float)
    df["LineCurrentIB"]=df["LineCurrentIB"].astype(float)
    df["hour"]=df["Datetime"].dt.strftime("%Y-%m-%d %H")
    df["hour"]=pd.to_datetime(df["hour"])
    df["date"]=df["Datetime"].dt.date
    df["date"]=pd.to_datetime(df["date"])
    df["month"]=df["Datetime"].dt.strftime("%b %Y")
    df["year"]=df["Datetime"].dt.strftime("%Y")
    df["PowerFactor"]=df["PowerFactor"].replace('-1.00','1.00')
    df["PowerFactor"]=df["PowerFactor"].astype(str)
   #df["PowerFactor"]=df["PowerFactor"]
    
    return df
df=load_df()
def Power():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Power Graph</h4>""",unsafe_allow_html=True)
    Power = st.selectbox("Choose Power", ["RealPower","ApparentPower","ReactivePower"])
    date1 = st.date_input('Starting Date')
    date2 = st.date_input('Ending Date')
    if  pd.to_datetime(date1)<df["date"].min() or pd.to_datetime(date1)>df["date"].max():
        st.warning("The start date is out of range")
    elif pd.to_datetime(date2)>df["date"].max() or pd.to_datetime(date2)<df["date"].min():
        st.warning("The end date is out of range")
    elif pd.to_datetime(date1) not in df["date"].values:
        st.warning("The start date is unavailable here")
    elif pd.to_datetime(date2) not in df["date"].values:
        st.warning("The end date is unavailable here")
    elif pd.to_datetime(date1)>pd.to_datetime(date2):
        st.warning("The start date is greater than the end date")
    else:    
        start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
        end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
        power_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
        source=ColumnDataSource(power_date)
        p = figure(x_axis_type="datetime", title=Power+" Per Minute",width=1000,height=250)
        p.vbar(x="Datetime", top=Power,source=source, width=6000, color="slateblue")
        hover=HoverTool(tooltips=[("Datetime","@Datetime{%Y-%m-%d %H:%M}"),(Power,"@"+Power)],formatters={"@Datetime":"datetime"})
        p.add_tools(hover)
        st.bokeh_chart(p,use_container_width=True)
    
def Energy():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Energy Graph</h4>""",unsafe_allow_html=True)
    Energy1 = st.selectbox("Choose Energy",["RealEnergyKWH","ApparentEnergyKVAH","ReactiveEnergyKVARHN","ReactiveEnergyKVARHP"])
    Energy=Energy1.replace("K","")
    time = st.selectbox("time",["per day","per month"])
    df_nonzero=df[df[Energy]!=0]
    if df_nonzero.empty:
        df_nonzero=df
    if time=="per day":
        first_day=df_nonzero.groupby("date",sort=False)[Energy].first()
        last_day=df_nonzero.groupby("date",sort=False)[Energy].last()
        day_diff=first_day.shift(-1)-first_day
        day_diff.iloc[-1]=last_day.iloc[-1]-first_day.iloc[-1]
        df_day_energy=day_diff.reset_index()
        df_day_energy[Energy]=df_day_energy[Energy].apply(lambda x:1000000+x if(x<0) else x)
        df_day_energy= df_day_energy.set_index('date').reindex(df["date"].unique(),fill_value=0).reset_index()
        source=ColumnDataSource(df_day_energy)
        p = figure(x_axis_type="datetime", title=Energy1+" Per Day",width=1000,height=300)
        p.vbar(x="date", top=Energy,source=source, width=10000000, color="slateblue")
        hover=HoverTool(tooltips=[("Date","@date{%Y-%m-%d}"),(Energy1,"@"+Energy)],formatters={"@date":"datetime"})
    elif time=="per month":
        first_month=df_nonzero.groupby("month",sort=False)[Energy].first()
        last_month=df_nonzero.groupby("month",sort=False)[Energy].last()
        month_diff=first_month.shift(-1)-first_month
        month_diff.iloc[-1]=last_month.iloc[-1]-first_month.iloc[-1]
        month_diff.apply(lambda x:x+1000000 if(x<0) else x)
        df_month_energy=month_diff.reset_index()
        df_month_energy[Energy]=df_month_energy[Energy].apply(lambda x:1000000+x if(x<0) else x)
        df_month_energy= df_month_energy.set_index('month').reindex(df["month"].unique(),fill_value=0).reset_index()
        source=ColumnDataSource(df_month_energy)
        p = figure(x_range=[m for m in df_month_energy["month"]], title=Energy1+" Per Month",width=1000,height=300)
        p.vbar(x="month", top=Energy, width=0.2,source=source,color="slateblue")
        hover=HoverTool(tooltips=[("Month","@month"),(Energy1,"@"+Energy)])
    #else:
        #first_year=df_nonzero.groupby("year",sort=False)[Energy].first()
        #last_year=df_nonzero.groupby("year",sort=False)[Energy].last()
        #year_diff=first_year.shift(-1)-first_year
        #year_diff.iloc[-1]=last_year.iloc[-1]-first_year.iloc[-1]
        #df_year_energy=year_diff.reset_index()
        #source=ColumnDataSource(df_year_energy)
        #p = figure(x_range=[y for y in df_year_energy["year"]], title=Energy+" Per Year",width=1000,height=300)
        #p.vbar(x="year", top=Energy, width=0.2,source=source,color="slateblue")
        #hover=HoverTool(tooltips=[("Year","@year"),(Energy,"@"+Energy)])
    p.add_tools(hover)
    st.bokeh_chart(p,use_container_width=True)
    
def Voltage():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Voltage Graph</h4>""",unsafe_allow_html=True)
    Voltage = st.selectbox("Voltage", ["Line Voltage","Phase Voltage"])
    date1 = st.date_input('Starting Date')
    date2 = st.date_input('Ending Date')
    if  pd.to_datetime(date1)<df["date"].min() or pd.to_datetime(date1)>df["date"].max():
        st.warning("The start date is out of range")
    elif pd.to_datetime(date2)>df["date"].max() or pd.to_datetime(date2)<df["date"].min():
        st.warning("The end date is out of range")
    elif pd.to_datetime(date1) not in df["date"].values:
        st.warning("The start date is unavailable here")
    elif pd.to_datetime(date2) not in df["date"].values:
        st.warning("The end date is unavailable here")
    elif pd.to_datetime(date1)>pd.to_datetime(date2):
        st.warning("The start date is greater than the end date")
    else:
        start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
        end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
        voltage_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
        if Voltage=="Line Voltage":
            source=ColumnDataSource(voltage_date)
            p = figure(x_axis_type="datetime", title="Line Voltage Per Minute",width=1000,height=250)
            p.line(x="Datetime", y="LineVoltageVRY",source=source, line_width=2, color="red")
            p.line(x="Datetime", y="LineVoltageVYB",source=source, line_width=2, color="yellow")
            p.line(x="Datetime", y="LineVoltageVBR",source=source, line_width=2, color="blue")
            hline1=Span(location=440,line_dash="dashed",line_color="red")
            hline2=Span(location=380,line_dash="dashed",line_color="red")
            p.add_layout(hline1)
            p.add_layout(hline2)
            hover=HoverTool(tooltips=[("Datetime","@Datetime{%Y-%m-%d %H:%M}"),("LineVoltageVRY","@LineVoltageVRY"),
                          ("LineVoltageVYB","@LineVoltageVYB"),
                          ("LineVoltageVBR","@LineVoltageVBR")],formatters={"@Datetime":"datetime"})
            p.add_tools(hover)
        else:
            source=ColumnDataSource(voltage_date)
            p = figure(x_axis_type="datetime", title="Phase Voltage Per Minute",width=1000,height=250)
            p.line(x="Datetime", y="PhaseVoltageVRN",source=source, line_width=2, color="red")
            p.line(x="Datetime", y="PhaseVoltageVYN",source=source, line_width=2, color="yellow")
            p.line(x="Datetime", y="PhaseVoltageVBN",source=source, line_width=2, color="blue")
            hline1=Span(location=241.5,line_dash="dashed",line_color="red")
            hline2=Span(location=218.5,line_dash="dashed",line_color="red")
            p.add_layout(hline1)
            p.add_layout(hline2)
            hover=HoverTool(tooltips=[("Datetime","@Datetime{%Y-%m-%d}"),("PhaseVoltageVRN","@PhaseVoltageVRN"),
                          ("PhaseVoltageVYN","@PhaseVoltageVYN"),
                          ("PhaseVoltageVBN","@PhaseVoltageVBN")],formatters={"@Datetime":"datetime"})
            p.add_tools(hover)
        st.bokeh_chart(p,use_container_width=True)
    
def Current():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Current Graph</h4>""",unsafe_allow_html=True)
    date1 = st.date_input('Starting Date')
    date2 = st.date_input('Ending Date')
    if  pd.to_datetime(date1)<df["date"].min() or pd.to_datetime(date1)>df["date"].max():
        st.warning("The start date is out of range")
    elif pd.to_datetime(date2)>df["date"].max() or pd.to_datetime(date2)<df["date"].min():
        st.warning("The end date is out of range")
    elif pd.to_datetime(date1) not in df["date"].values:
        st.warning("The start date is unavailable here")
    elif pd.to_datetime(date2) not in df["date"].values:
        st.warning("The end date is unavailable here")
    elif pd.to_datetime(date1)>pd.to_datetime(date2):
        st.warning("The start date is greater than the end date")
    else:
         start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
         end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
         current_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
         source=ColumnDataSource(current_date)
         p = figure(x_axis_type="datetime", title="Line Current Per Minute",width=1000,height=300)
         p.line(x="Datetime", y="LineCurrentIR",source=source, line_width=2, color="red")
         p.line(x="Datetime", y="LineCurrentIY",source=source, line_width=2, color="yellow")
         p.line(x="Datetime", y="LineCurrentIB",source=source, line_width=2, color="blue")
         hover=HoverTool(tooltips=[("Date","@Datetime{%Y-%m-%d %H:%M}"),("LineCurrentIR","@LineCurrentIR"),
                          ("LineCurrentIY","@LineCurrentIY"),
                          ("LineCurrentIB","@LineCurrentIB")],formatters={"@Datetime":"datetime"})
         p.add_tools(hover)
         st.bokeh_chart(p,use_container_width=True)
         
def PowerFactor():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Power Factor Graph</h4>""",unsafe_allow_html=True)
    date1 = st.date_input('Starting Date')
    date2 = st.date_input('Ending Date')
    if  pd.to_datetime(date1)<df["date"].min() or pd.to_datetime(date1)>df["date"].max():
        st.warning("The start date is out of range")
    elif pd.to_datetime(date2)>df["date"].max() or pd.to_datetime(date2)<df["date"].min():
        st.warning("The end date is out of range")
    elif pd.to_datetime(date1) not in df["date"].values:
        st.warning("The start date is unavailable here")
    elif pd.to_datetime(date2) not in df["date"].values:
        st.warning("The end date is unavailable here")
    elif pd.to_datetime(date1)>pd.to_datetime(date2):
        st.warning("The start date is greater than the end date")
    else:
         start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
         end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
         pf_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
         source=ColumnDataSource(pf_date)
         y_values=['-0.91','-0.92','-0.93','-0.94','-0.95','-0.96','-0.97','-0.98','-0.99','1.00',
                   '0.99','0.98','0.97','0.96','0.95','0.94','0.93','0.92','0.91']
         #y_ticks.sort(reverse=True)
         p = figure(x_axis_type="datetime", title="Power Factor Per Minute",width=2000,height=300,
                    y_axis_label="<-----Leading                Lagging----->",
                    y_range=FactorRange(*y_values))
         #p.yaxis.ticker=FixedTicker(ticks=y_ticks)
         p.dot(x="Datetime",y="PowerFactor", size=20,source=source,color="slateblue",line_dash="dotted")
         hover=HoverTool(tooltips=[("Date","@Datetime{%Y-%m-%d %H:%M}"),("PowerFactor","@PowerFactor")]
                         ,formatters={"@Datetime":"datetime"})
         p.add_tools(hover)
         st.bokeh_chart(p,use_container_width=True)
def Frequency():
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Frequency Graph</h4>""",unsafe_allow_html=True)
    date1 = st.date_input('Starting Date')
    date2 = st.date_input('Ending Date')
    if  pd.to_datetime(date1)<df["date"].min() or pd.to_datetime(date1)>df["date"].max():
        st.warning("The start date is out of range")
    elif pd.to_datetime(date2)>df["date"].max() or pd.to_datetime(date2)<df["date"].min():
        st.warning("The end date is out of range")
    elif pd.to_datetime(date1) not in df["date"].values:
        st.warning("The start date is unavailable here")
    elif pd.to_datetime(date2) not in df["date"].values:
        st.warning("The end date is unavailable here")
    elif pd.to_datetime(date1)>pd.to_datetime(date2):
        st.warning("The start date is greater than the end date")
    else:
         start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
         end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
         freq_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
         source=ColumnDataSource(freq_date)
         p = figure(x_axis_type="datetime", title="Frequency Per Minute",width=2000,height=300)
         p.vbar(x="Datetime", top="Frequency", width=6000,source=source,color="slateblue")
         hline1=Span(location=52.5,line_dash="dashed",line_color="red")
         hline2=Span(location=47.5,line_dash="dashed",line_color="red")
         p.add_layout(hline1)
         p.add_layout(hline2)
         hover=HoverTool(tooltips=[("Date","@Datetime{%Y-%m-%d %H:%M}"),("Frequency","@Frequency")]
                         ,formatters={"@Datetime":"datetime"})
         p.add_tools(hover)
         st.bokeh_chart(p,use_container_width=True)
def live_data():
    #st.title("Live Data")
    
    st.markdown(f"""
                <h4 style="margin-left:-20%;margin-top:-10%;">Live Data</h4>
                <i style="margin-left:-20%;">Datetime: {df.iloc[-1]["Datetime"]}</i>
                <table style="width:1000px;border:0px;margin-left:-20%;">
                <tr style="border:0px;">
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;">
                <p style="background-color:red;"><b>Real Power P<sub>r</sub> in Watts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["RealPowerR"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white">
                <p style="background-color:	rgb(255, 200, 10);"><b>Real Power P<sub>y</sub> in Watts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["RealPowerY"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white">
                <p style="background-color:royalblue;"><b>Real Power P<sub>b</sub> in Watts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["RealPowerB"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white">
                <p style="background-color:green;"><b>3ph Real Power P in Watts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["RealPower"]}</b></p>
                </div>
                </td>
                </tr>
                
                <tr style="border:0px">
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:red;"><b>Reactive Power Q<sub>r</sub> in VAR</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ReactivePowerR"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:	rgb(255, 200, 10);"><b>Reactive Power Q<sub>y</sub> in VAR</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ReactivePowerY"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
               <p style="background-color:royalblue;"><b>Reactive Power Q<sub>b</sub> in VAR</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ReactivePowerB"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:green;"><b>3ph Reactive Power Q in VAR</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ReactivePower"]}</b></p>
                </div>
                </td>
                </tr>
                
                <tr style="border:0px">
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:red;"><b>Apparent Power S<sub>r</sub> in VA</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ApparentPowerR"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:	rgb(255, 200, 10);"><b>Apparent Power S<sub>y</sub> in VA</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ApparentPowerY"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:royalblue;"><b>Apparent Power S<sub>b</sub> in VA</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ApparentPowerB"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:green;"><b>3ph Apparent Power S in VA</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["ApparentPower"]}</b></p>
                </div>
                </td>
                </tr>
                
                <tr style="border:0px">
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:red;"><b>Current I<sub>r</sub> in Amps</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineCurrentIR"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:	rgb(255, 200, 10);"><b>Current I<sub>y</sub> in Amps</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineCurrentIY"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
               <p style="background-color:royalblue;"><b>Current I<sub>b</sub> in Amps</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineCurrentIB"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:green;"><b>Power Factor</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["PowerFactor"]}</b></p>
                </div>
                </td>
                </tr>
                
                <tr style="border:0px">
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:red;"><b>Line Voltage V<sub>ry</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineVoltageVRY"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:	rgb(255, 200, 10);"><b>Line Voltage V<sub>yb</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineVoltageVYB"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
              <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:royalblue;"><b>Line Voltage V<sub>br</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["LineVoltageVBR"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
               <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:green;"><b>Frequency in Hz</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["Frequency"]}</b></p>
                </div>
                </td>
                </tr>
                
                <tr style="border:0px">
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:red;"><b>Phase Voltage V<sub>rn</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["PhaseVoltageVRN"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:	rgb(255, 200, 10);"><b>Phase Voltage V<sub>yn</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["PhaseVoltageVYN"]}</b></p>
                </div>
                </td>
                <td style="border:0px">
                <div style="text-align:center;color:white;box-shadow: 0px 0px 2px lightgrey;background-color:white;margin-top:-5%;">
                <p style="background-color:royalblue;"><b>Phase Voltage V<sub>bn</sub> in Volts</b></p>
                <p style="color:grey;"><b>{df.iloc[-1]["PhaseVoltageVBN"]}</b></p>
                </div>
                </td>
                </tr>
                </table>""",unsafe_allow_html=True)
    
page = st.sidebar.selectbox("Parameters", ("Live Data","Energy", "Power", "Voltage", "Current","Power Factor","Frequency"))

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
    
