import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

# --- Streamlit UI ---
st.title("Z-Score Mean Reversion Strategy")
st.write("This app calculates a Z-score-based mean reversion signal for any stock ticker.")

# User inputs
ticker = st.text_input("Enter Ticker Symbol", value="SNAP")
lookback = st.slider("Lookback Window (days)", 10, 60, 20)
z_threshold = st.slider("Z-Score Threshold", 0.5, 3.0, 1.5, 0.1)
days_back = st.slider("Days of Data to Fetch", 30, 365, 120)

if ticker:
    start_date = datetime.date.today() - datetime.timedelta(days=days_back)

    # Fetch data
    data = yf.download(ticker, start=start_date)

    if not data.empty:
        # Select the Close price column for this ticker explicitly
        if isinstance(data.columns, pd.MultiIndex):
            # If MultiIndex, select Close column for ticker
            if ( 'Close', ticker ) in data.columns:
                data = data['Close'][ticker]  # This is a Series
            else:
                # fallback: try just first level 'Close'
                data = data['Close']
        else:
            data = data['Close']

        # Make sure it's a DataFrame for consistency
        data = data.to_frame(name='Close')

        # Calculate rolling mean and std
        data['mean'] = data['Close'].rolling(window=lookback).mean()
        data['std'] = data['Close'].rolling(window=lookback).std()
        data['std'].replace(0, np.nan, inplace=True)

        required_cols = ['Close', 'mean', 'std']
        existing_cols = [col for col in required_cols if col in data.columns]

        st.write(f"Columns in DataFrame after selecting Close: {data.columns.tolist()}")
        st.write(f"Columns to dropna on: {existing_cols}")

        if existing_cols:
            data.dropna(subset=existing_cols, inplace=True)
        else:
            st.warning("No columns found to drop NA on.")

        data['z_score'] = (data['Close'] - data['mean']) / data['std']

        # Generate trading signals based on z-score threshold
        data['signal'] = np.where(data['z_score'] < -z_threshold, 'BUY',
                           np.where(data['z_score'] > z_threshold, 'SELL', 'HOLD'))

        # Show recent signals
        st.subheader("Latest Signals")
        st.dataframe(data[['Close', 'mean', 'std', 'z_score', 'signal']].tail(10))

        # Plotting the data and signals
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(data.index, data['Close'], label='Close Price', alpha=0.7)
        ax.plot(data.index, data['mean'], label=f'{lookback}-day Mean', linestyle='--', alpha=0.7)

        buy_signals = data[data['signal'] == 'BUY']
        sell_signals = data[data['signal'] == 'SELL']

        ax.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label='BUY Signal')
        ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', label='SELL Signal')

        ax.set_title(f"{ticker} Z-Score Mean Reversion")
        ax.legend()
        st.pyplot(fig)

    else:
        st.error("No data found for this ticker.")
