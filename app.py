import streamlit as st
import helper
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(layout="wide")
st.title("ForeCrash: Crash Forecasting in NYC")




st.sidebar.header("Forecast Model Selection")
model_option = st.sidebar.selectbox("Model Selection", ("ETS Additive", "ETS Multiplicative", "ARIMA"))

# Monthly average of daily crashes by borough
clean_df = helper.read_clean_data('Motor_Vehicle_Collisions_-_Crashes.csv')
clean_df.index = pd.to_datetime(clean_df.index)
# Geopandas dataframe of NYC boroughs
nyc_map = helper.nyc_map('nybb.shp')

# Number of periods to forecast
periods = 12
# List of months to forecast
month_list = []
for i in range(1, periods+1):
    time = clean_df.index.max() + pd.DateOffset(months=i)
    month_list.append(time.strftime('%B %Y'))

st.sidebar.header("------------------------------")
st.sidebar.header("Month Selection")
time_option = st.sidebar.selectbox("Time Selection", month_list)
ele_num = month_list.index(time_option) + 1
boro_list = ['BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND']
forecast_dict = {}
line_dict = {}
for boro in boro_list:
    temp = helper.forecast_boro(clean_df, boro, model_option, periods, ele_num)
    forecast_dict[boro] = temp[0]
    line_dict[boro] = temp[1]

tab1, tab2 = st.tabs(["Map View", "Line View"])

with tab1:
    st.header("Forecasted Number of Crashes by Borough")
    fig, ax = plt.subplots(figsize=(10,2))
    fig, ax = helper.heatmap_plot(nyc_map, forecast_dict, fig, ax)
    ax.set_title(f'Average Daily Crashes for {time_option}')
    ax.axis('off')
    st.pyplot(fig=fig)

    with st.expander("Data Details"):
        st.header("Forecasted Average Daily Crashes")
        data = pd.DataFrame.from_dict(forecast_dict, orient='index', columns=[f'Average Daily Crashes for {time_option}'])
        st.table(data)

with tab2:
    st.header("Forecasted Number of Crashes Over Time")
    fig, ax = plt.subplots(figsize=(10,4))
    for boro, line in line_dict.items():
        ax.plot(line.index, line, label=boro)
        ax.fill_between(line.index, line * 0.92, line * 1.08, color='red',
                              alpha=0.2)
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Crashes')
    ax.set_title(f'Forecasted Average Daily Crashes Post COVID using {model_option} Model')
    fig.legend()
    st.pyplot(fig=fig)

