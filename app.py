import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# --- වෙබ් පිටුවේ සැකසුම් ---
st.set_page_config(page_title="KALI V12 ULTIMATE", page_icon="💎", layout="wide")

st.title("🚀 KALI V12 PRO - ULTIMATE AI TRADING BOT")
st.markdown("##### Developed by Chief Engineer | 100% Live Market Data")

# --- Coin List (20 Coins) ---
crypto_list = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
    'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'TRX/USDT', 'DOT/USDT',
    'LINK/USDT', 'LTC/USDT', 'SHIB/USDT', 'DAI/USDT', 'BCH/USDT',
    'NEAR/USDT', 'ATOM/USDT', 'PEPE/USDT', 'APT/USDT', 'UNI/USDT'
]

@st.cache_data(ttl=60)
def fetch_and_analyze_data():
    exchange = ccxt.bybit({'enableRateLimit': True})
    summary_data = []
    all_dfs = {}

    for coin in crypto_list:
        try:
            ohlcv = exchange.fetch_ohlcv(coin, timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 1. Essential Indicators
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            df['Vol_MA'] = df['Volume'].rolling(window=10).mean()

            # 2. Leading Indicators (Stochastic & MFI)
            low_14 = df['Low'].rolling(window=14).min()
            high_14 = df['High'].rolling(window=14).max()
            df['%K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
            df['%D'] = df['%K'].rolling(window=3).mean()

            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            money_flow = typical_price * df['Volume']
            pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=14).sum()
            neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=14).sum()
            mfr = pos_flow / neg_flow
            df['MFI'] = 100 - (100 / (1 + mfr))

            # 3. Candlestick Patterns
            df['Body'] = abs(df['Close'] - df['Open'])
            df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
            
            is_hammer = (df['Lower_Wick'].iloc[-1] > (2 * df['Body'].iloc[-1])) and (df['Upper_Wick'].iloc[-1] < (0.5 * df['Body'].iloc[-1]))
            is_star = (df['Upper_Wick'].iloc[-1] > (2 * df['Body'].iloc[-1])) and (df['Lower_Wick'].iloc[-1] < (0.5 * df['Body'].iloc[-1]))

            # 4. Values Extraction
            curr_p = float(df['Close'].iloc[-1])
            curr_rsi = float(df['RSI'].iloc[-1])
            curr_mfi = float(df['MFI'].iloc[-1])
            curr_k = float(df['%K'].iloc[-1])
            curr_d = float(df['%D'].iloc[-1])
            last_ema = float(df['EMA9'].iloc[-1])
            curr_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Vol_MA'].iloc[-1])

            # 5. KALI ULTIMATE BRAIN LOGIC
            score = 0
            if curr_p > last_ema: score += 1
            if curr_k > curr_d and curr_k < 80: score += 1
            if curr_mfi > 50: score += 1
            if curr_vol > avg_vol: score += 1

            std_dev = df['Close'].rolling(window=20).std().iloc[-1]
            est_move = std_dev * 1.5 # Target move
            
            pattern = "-"
            signal = "⚪ NEUTRAL"
            tp = curr_p
            sl = curr_p

            if is_hammer and curr_rsi < 60:
                signal, pattern = "🟢 STRONG BUY (REVERSAL)", "🔨 Hammer"
                tp = curr_p + est_move
                sl = curr_p - (est_move / 2)
            elif is_star and curr_rsi > 40:
                signal, pattern = "🔴 STRONG SELL (REVERSAL)", "🌠 Shooting Star"
                tp = curr_p - est_move
                sl = curr_p + (est_move / 2)
            elif score >= 3 and curr_rsi < 70:
                signal, pattern = "🟢 BUY (TREND)", "-"
                tp = curr_p + est_move
                sl = curr_p - (est_move / 2)
            elif score <= 1 and curr_rsi > 30:
                signal, pattern = "🔴 SELL (TREND)", "-"
                tp = curr_p - est_move
                sl = curr_p + (est_move / 2)

            all_dfs[coin] = df # Save for charting

            summary_data.append({
                'Coin': coin,
                'Price': f"${curr_p:,.4f}",
                'Signal': signal,
                'Pattern': pattern,
                'Take Profit': f"${tp:,.4f}",
                'Stop Loss': f"${sl:,.4f}",
                'MFI': f"{curr_mfi:.1f}",
                'Stoch %K': f"{curr_k:.1f}",
                'RSI': f"{curr_rsi:.1f}"
            })
            
        except Exception as e:
            continue

    return pd.DataFrame(summary_data), all_dfs

# --- වෙබ් පිටුවේ ප්‍රධාන කොටස (UI) ---

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Master Dashboard")
    if st.button("🔄 Refresh Data (Live)"):
        st.cache_data.clear()
        
    with st.spinner("KALI is scanning all 20 coins..."):
        df_summary, all_charts = fetch_and_analyze_data()
        
        # Style the dataframe
        def color_signals(val):
            if 'BUY' in str(val): return 'background-color: #d4edda; color: #155724; font-weight: bold'
            if 'SELL' in str(val): return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
            return ''
            
        styled_df = df_summary.style.map(color_signals, subset=['Signal'])
        st.dataframe(styled_df, use_container_width=True, height=600)

with col2:
    st.subheader("📈 Chart Viewer")
    selected_coin = st.selectbox("Select Coin to View Chart:", list(all_charts.keys()) if 'all_charts' in locals() else crypto_list)
    
    if 'all_charts' in locals() and selected_coin in all_charts:
        chart_df = all_charts[selected_coin]
        
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(chart_df.index[-48:], chart_df['Close'].iloc[-48:], label='Price', color='blue')
        ax.plot(chart_df.index[-48:], chart_df['EMA9'].iloc[-48:], label='EMA 9', color='orange', linestyle='--')
        ax.set_title(f"{selected_coin} (Last 48h)", color='white')
        ax.legend()
        ax.grid(True, alpha=0.2)
        
        # Streamlit dark mode fix for matplotlib
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        
        st.pyplot(fig)

sl_tz = pytz.timezone('Asia/Colombo')
st.caption(f"Last Updated: {datetime.now(sl_tz).strftime('%Y-%m-%d | %I:%M:%S %p')} (Sri Lanka Time)")
