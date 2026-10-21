import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="크로스 마진 리스크 시뮬레이터", layout="wide")

@st.cache_data(ttl=15)
def get_current_price(symbol):
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        return float(ticker.fast_info['lastPrice'])
    except Exception:
        # 통신 오류 시 코인별 기본값 반환
        fallback = {"BTC": 68000.0, "ETH": 2600.0, "SOL": 150.0}
        return fallback.get(symbol, 100.0)

def clear_price_cache():
    get_current_price.clear()

st.title("⚡ 크로스 마진 실효 레버리지 시뮬레이터")

# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 포지션 및 계좌 설정")

# 1. 타겟 코인에 SOL 추가
coin_choice = st.sidebar.selectbox(
    "타겟 코인", 
    ["BTC", "ETH", "SOL"], 
    on_change=clear_price_cache
)

# 코인별 세부 파라미터 설정 (호가 단위 및 유지증거금률)
coin_params = {
    "BTC": {"step": 100.0, "mmr": 0.004, "max_lev": 125, "fmt": "%.1f"},
    "ETH": {"step": 10.0,  "mmr": 0.005, "max_lev": 100, "fmt": "%.2f"},
    "SOL": {"step": 0.5,   "mmr": 0.008, "max_lev": 100, "fmt": "%.2f"},
}
params = coin_params[coin_choice]

# 실시간 가격 조회 및 수동 갱신 버튼
live_price = get_current_price(coin_choice)
if st.sidebar.button("🔄 실시간 시장가 갱신"):
    clear_price_cache()
    live_price = get_current_price(coin_choice)

entry_price = st.sidebar.number_input(
    f"{coin_choice} 진입 가격 (USDT)", 
    value=round(live_price, 2), 
    step=params["step"],
    format=params["fmt"]
)

total_equity = st.sidebar.number_input("총 시드 (USDT)", value=44204.0, step=100.0)
display_leverage = st.sidebar.slider("화면 설정 배수 (Leverage)", 1, params["max_lev"], min(100, params["max_lev"]))
target_eff_lev = st.sidebar.slider("목표 실효 레버리지 (Effective Lev)", 0.5, 25.0, 10.0, step=0.5)
position_side = st.sidebar.radio("포지션 방향", ["Long (공매수)", "Short (공매도)"])

# --- 핵심 계산 로직 ---
position_notional = total_equity * target_eff_lev          # 포지션 총 규모 (USDT)
coin_qty = position_notional / entry_price                 # 진입 수량 (개)
initial_margin = position_notional / display_leverage      # 필요 개시 증거금 (USDT)
maint_margin = position_notional * params["mmr"]           # 유지 증거금 (USDT)

# 크로스 마진 가용 손실 완충금 (총 시드 - 유지 증거금)
available_loss_buffer = total_equity - maint_margin
price_move_to_liq = available_loss_buffer / coin_qty if coin_qty > 0 else 0

if "Long" in position_side:
    liq_price = max(0.0, entry_price - price_move_to_liq)
    liq_drop_pct = ((liq_price - entry_price) / entry_price) * 100
else:
    liq_price = entry_price + price_move_to_liq
    liq_drop_pct = ((liq_price - entry_price) / entry_price) * 100

# --- 메인 대시보드 출력 ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("실시간/진입 단가", f"${entry_price:,.2f}")
col2.metric(f"진입 수량 ({coin_choice})", f"{coin_qty:,.2f} {coin_choice}")
col3.metric("포지션 총 가치", f"${position_notional:,.0f}")
col4.metric("예상 강제청산가", f"${liq_price:,.2f}", f"{liq_drop_pct:.2f}%", delta_color="inverse")

# --- 청산 방어선 시각화 (Plotly) ---
fig = go.Figure()

fig.add_trace(go.Indicator(
    mode="number+gauge+delta",
    value=entry_price,
    delta={'reference': liq_price, 'position': "top"},
    title={'text': f"<b>{coin_choice} 현재 진입가 vs 강제청산 방어선</b>"},
    gauge={
        'axis': {'range': [min(liq_price * 0.8, entry_price * 0.8), max(liq_price * 1.2, entry_price * 1.2)]},
        'bar': {'color': "#00cc96" if "Long" in position_side else "#ef553b"},
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.85,
            'value': liq_price
        }
    }
))
fig.update_layout(height=320)
st.plotly_chart(fig, use_container_width=True)
