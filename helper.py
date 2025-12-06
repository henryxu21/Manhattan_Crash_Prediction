import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import geopandas as gpd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pmdarima as pm


@st.cache_data
def read_clean_data(file):
    raw_df = pd.read_csv(file, low_memory=False)
    raw_df['time_index'] = pd.to_datetime(raw_df['CRASH DATE'] + ' ' + raw_df['CRASH TIME'], format = '%m/%d/%Y %H:%M')
    # 1) Daily crash counts by borough (one row per borough/day)
    daily_counts_borough = (
        raw_df
          .groupby(["BOROUGH", pd.Grouper(key="time_index", freq="D")])
          .size()
          .rename("daily_crashes")
          .reset_index()                       # <-- important so 'time_index' is a column again
    )
    # 2) Monthly average of daily crashes by borough
    monthly_avg_borough = (
        daily_counts_borough
          .groupby(["BOROUGH", pd.Grouper(key="time_index", freq="MS")])  # 'MS' = month start
          ["daily_crashes"].mean()
          .reset_index()
          .rename(columns={"time_index": "month", "daily_crashes": "avg_daily_crashes"})
    )
    # 3) Keep 2021–through last full month 2025-08
    monthly_avg_borough = monthly_avg_borough[
        (monthly_avg_borough["month"] >= "2021-01-01") &
        (monthly_avg_borough["month"] <= "2025-08-31")
    ]
    monthly_avg_borough.set_index('month', inplace=True)
    return monthly_avg_borough

@st.cache_data
def ets_additive_forecast(df, periods):
    model = ExponentialSmoothing(df, trend='add', seasonal='add', seasonal_periods=12, freq='MS').fit()
    forecast = model.forecast(periods)
    return forecast

@st.cache_data
def ets_multiplicative_forecast(df, periods):
    model = ExponentialSmoothing(df, trend='add', seasonal='mul', seasonal_periods=12, freq='MS').fit()
    forecast = model.forecast(periods)
    return forecast

@st.cache_data
def arima_forecast(df, periods):
    model = pm.auto_arima(
    df,  # your training series
    start_p=0, start_q=0,
    test='adf',                            # use Augmented Dickey–Fuller test
    max_p=3, max_q=3, m=12,                # monthly seasonality (period = 12)
    start_P=0, seasonal=True,              # enable seasonal component
    d=1, D=1, trace=True,                  # differencing orders and verbose output
    error_action='ignore',
    suppress_warnings=True,
    stepwise=True)
    forecast = model.predict(n_periods=periods)
    return forecast




def forecast_boro(clean_df, borough, model_option, periods, ele_num):
    borough_df = clean_df[clean_df['BOROUGH'] == borough.upper()]
    borough_df = borough_df.drop('BOROUGH', axis=1)
    borough_df.index = pd.to_datetime(borough_df.index)
    if model_option == "ETS Additive":
        forecast = ets_additive_forecast(borough_df, periods)
    elif model_option == "ETS Multiplicative":
        forecast = ets_multiplicative_forecast(borough_df, periods)
    elif model_option == "ARIMA":
        forecast = arima_forecast(borough_df, periods)
    else:
        forecast = None
    forecast.index = pd.date_range(start=forecast.index.min(), periods=periods, freq='MS')
    return int(forecast.loc[borough_df.index.max() + pd.DateOffset(months=ele_num)]), forecast

@st.cache_data
def nyc_map(file):
    nyc_map_plot = gpd.read_file(file)
    return nyc_map_plot

def plot_boroughs(df, borough, fig, ax):
    borough_df = df[df['BOROUGH'] == borough.upper()]
    borough_df = borough_df.groupby(pd.Grouper(freq='MS')).count()
    ax.plot(borough_df.index, borough_df['COUNT'], label=borough)
    return fig, ax

def heatmap_plot(df, dict_data, fig, ax):
    df['BoroName'] = df['BoroName'].str.upper()
    test_df = pd.DataFrame.from_dict(dict_data, orient='index', columns=['Data'])
    test_df = test_df.reset_index().rename(columns={'index': 'BoroName'})
    merged = df.merge(test_df, on='BoroName')
    ax = merged.plot(column='Data', legend=True, cmap='Reds',ax=ax)
    for idx, row in merged.iterrows():
        # Get the centroid of the geometry for label placement
        centroid = row.geometry.centroid
        ax.annotate(text=row['BoroName'], xy=(centroid.x, centroid.y),
                    horizontalalignment='center', fontsize=4, color='black')
    return fig, ax
