import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 실시간 가격 불러오기 함수 (yfinance 연동) ---
@st.cache_data(ttl=10) # 10초마다 캐시 갱신 (서버 과부하 방지)
def get_current_price(symbol):
    ticker_symbol = f"{symbol}-USD"
    try:
        ticker = yf.Ticker(ticker_symbol)
        # fast_info를 사용하면 딜레이 없이 가장 최근 체결가를 빠르게 가져옵니다.
        current_price = ticker.fast_info['lastPrice']
        return float(current_price)
    except Exception as e:
        # 야후 파이낸스 접속 오류 시 임시 방어 코드
        return 80000.0 if symbol == "BTC" else 3000.0

# --- 2. Streamlit UI 설정 ---
st.set_page_config(page_title="크로스 마진 리스크 시뮬레이터", layout="wide")
st.title("⚡ 크로스 마진 실효 레버리지 시뮬레이터")
st.markdown("안전한 선물 트레이딩을 위한 **[진입 수량]** 및 **[청산 하락폭]** 실시간 계산기")

# --- 3. 사이드바: 기본 설정 입력 ---
st.sidebar.header("📊 기본 설정")

# 코인 선택
coin_choice = st.sidebar.selectbox("타겟 코인 선택", ["BTC", "ETH"])
current_price = get_current_price(coin_choice)
st.sidebar.success(f"현재 {coin_choice} 가격: **${current_price:,.2f}**")

# 시드 및 배수 입력
total_equity = st.sidebar.number_input("지갑 총 시드 (USDT)", min_value=100.0, value=40000.0, step=100.0)
display_leverage = st.sidebar.slider("거래소 화면 설정 배수 (x)", min_value=10, max_value=100, value=100, step=1)

st.sidebar.divider()

# 실효 레버리지 슬라이더
target_eff_lev = st.sidebar.slider("목표 실효 레버리지 (x) - 리스크 조절", min_value=1.0, max_value=20.0, value=10.0, step=0.5)

# --- 4. 백엔드 핵심 계산 로직 ---
# 진입 금액 = 총 시드 * 실효 레버리지
position_notional = total_equity * target_eff_lev

# 권장 진입 수량 (코인 개수)
entry_qty = position_notional / current_price

# 한도 대비 진입 비율(%) = (목표 실효 레버리지 / 설정 배수) * 100
entry_ratio_pct = (target_eff_lev / display_leverage) * 100
entry_ratio_pct = min(entry_ratio_pct, 100.0) # 100% 초과 방지

# 갭(여유 마진) 비율(%) = 100 - 진입 비율
gap_ratio_pct = 100.0 - entry_ratio_pct

# 예상 청산 하락폭(%) = - (100 / 실효 레버리지)
liquidation_drop_pct = -(100 / target_eff_lev)

# 청산 가격 계산
liquidation_price = current_price * (1 + (liquidation_drop_pct / 100))
liquidation_price = max(0, liquidation_price) # 마이너스 가격 방지

# --- 5. 메인 화면 출력 ---
# 1열: 메트릭 요약 카드
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"권장 진입 수량 ({coin_choice})", value=f"{entry_qty:,.4f} 개")
with col2:
    st.metric(label="총 진입 금액 (USDT)", value=f"${position_notional:,.0f}")
with col3:
    # 리스크에 따른 청산폭 색상 경고
    risk_color = "🔴 초고위험 (데스존)" if target_eff_lev >= 10 else "🟡 주의 요망" if target_eff_lev >= 5 else "🟢 안전"
    st.metric(label=f"예상 청산 하락폭 ({risk_color})", value=f"{liquidation_drop_pct:,.1f} %", delta=f"청산가: ${liquidation_price:,.0f}", delta_color="inverse")

st.divider()

# 2열: 차트 및 시각화
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📉 청산가 방어선 시각화")
    fig_price = go.Figure()
    # 방어막(갭) 영역
    fig_price.add_trace(go.Bar(x=["가격 레벨"], y=[current_price - liquidation_price], base=liquidation_price, marker_color='lightgreen', name="안전 구간 (방어막)"))
    # 현재가 마커
    fig_price.add_trace(go.Scatter(x=["가격 레벨"], y=[current_price], mode="markers+text", marker=dict(color='blue', size=15), text=[f"현재가: ${current_price:,.0f}"], textposition="top right", name="현재가"))
    # 청산가 마커
    fig_price.add_trace(go.Scatter(x=["가격 레벨"], y=[liquidation_price], mode="markers+text", marker=dict(color='red', size=15), text=[f"청산가: ${liquidation_price:,.0f}"], textposition="bottom right", name="청산가"))
    
    fig_price.update_layout(yaxis_title="가격 (USD)", showlegend=False, height=350, yaxis_range=[liquidation_price * 0.8, current_price * 1.1])
    st.plotly_chart(fig_price, use_container_width=True)

with col_chart2:
    st.subheader(f"🛡️ {display_leverage}배 설정 한도 대비 수량 비율")
    fig_bar = go.Figure()
    
    # 목표 실효 레버리지가 설정 배수보다 커져서 100%를 초과하는 경우 붉은색 경고 표시
    bar_color = 'royalblue' if entry_ratio_pct < 100 else 'red'
    
    fig_bar.add_trace(go.Bar(y=["비율"], x=[entry_ratio_pct], name="진입 수량 비중", orientation='h', marker_color=bar_color, text=f"{entry_ratio_pct:.1f}%", textposition='inside'))
    if gap_ratio_pct > 0:
        fig_bar.add_trace(go.Bar(y=["비율"], x=[gap_ratio_pct], name="여유 마진 (갭) 비중", orientation='h', marker_color='lightgray', text=f"{gap_ratio_pct:.1f}%", textposition='inside'))
    
    fig_bar.update_layout(barmode='stack', xaxis_title="퍼센트 (%)", xaxis_range=[0, 100], showlegend=True, height=250)
    st.plotly_chart(fig_bar, use_container_width=True)

    if entry_ratio_pct >= 100:
        st.error("🚨 **위험:** 목표 실효 레버리지가 화면 설정 배수를 초과했습니다. 청산 방어막(갭)이 전혀 없는 상태입니다.")
    else:
        st.info(f"💡 **실전 주문 가이드:** 거래소 주문창에서 수량 슬라이더를 **{entry_ratio_pct:.1f}%** 까지만 당기시면 방어막이 유지됩니다.")

st.caption("※ 본 시뮬레이터는 거래소 수수료 및 유지증거금률(MMR)을 제외한 수리적 모델링이며, 롱 포지션을 기준으로 계산되었습니다. 데이터 제공: Yahoo Finance")
