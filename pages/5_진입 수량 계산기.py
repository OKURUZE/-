import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- 1. 실시간 가격 불러오기 함수 (바이낸스 API) ---
@st.cache_data(ttl=10) # 10초마다 캐시 갱신
def get_current_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    try:
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except:
        # API 오류 시 임시 가격 반환
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
total_equity = st.sidebar.number_input("지갑 총 시드 (USDT)", min_value=100.0, value=10000.0, step=100.0)
display_leverage = st.sidebar.slider("거래소 화면 설정 배수 (x)", min_value=10, max_value=100, value=20, step=1)

st.sidebar.divider()

# 실효 레버리지 슬라이더
target_eff_lev = st.sidebar.slider("목표 실효 레버리지 (x) - 리스크 조절", min_value=1.0, max_value=float(display_leverage), value=2.0, step=0.5)

# --- 4. 백엔드 핵심 계산 로직 ---
# 진입 금액 = 총 시드 * 실효 레버리지
position_notional = total_equity * target_eff_lev

# 권장 진입 수량 (코인 개수)
entry_qty = position_notional / current_price

# 한도 대비 진입 비율(%) = (목표 실효 레버리지 / 설정 배수) * 100
entry_ratio_pct = (target_eff_lev / display_leverage) * 100

# 갭(여유 마진) 비율(%) = 100 - 진입 비율
gap_ratio_pct = 100 - entry_ratio_pct

# 예상 청산 하락폭(%) = - (100 / 실효 레버리지)
# 롱 포지션 기준 간단 계산 (유지증거금률 제외)
liquidation_drop_pct = -(100 / target_eff_lev)

# 청산 가격 계산
liquidation_price = current_price * (1 + (liquidation_drop_pct / 100))

# --- 5. 메인 화면 출력 ---
# 1열: 메트릭 요약 카드
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"권장 진입 수량 ({coin_choice})", value=f"{entry_qty:,.4f} 개")
with col2:
    st.metric(label="총 진입 금액 (USDT)", value=f"${position_notional:,.0f}")
with col3:
    # 리스크에 따른 청산폭 색상 경고
    risk_color = "🔴 매우 위험" if target_eff_lev >= 10 else "🟡 주의 요망" if target_eff_lev >= 5 else "🟢 안전"
    st.metric(label=f"예상 청산 하락폭 ({risk_color})", value=f"{liquidation_drop_pct:,.1f} %", delta=f"청산가: ${liquidation_price:,.0f}", delta_color="inverse")

st.divider()

# 2열: 차트 및 시각화
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📉 청산가 방어선 시각화")
    # Plotly 라인/막대 혼합 차트
    fig_price = go.Figure()
    fig_price.add_trace(go.Bar(x=["가격 레벨"], y=[current_price - liquidation_price], base=liquidation_price, marker_color='lightgreen', name="안전 구간 (버퍼)"))
    fig_price.add_trace(go.Scatter(x=["가격 레벨"], y=[current_price], mode="markers+text", marker=dict(color='blue', size=15), text=[f"현재가: ${current_price:,.0f}"], textposition="top right", name="현재가"))
    fig_price.add_trace(go.Scatter(x=["가격 레벨"], y=[liquidation_price], mode="markers+text", marker=dict(color='red', size=15), text=[f"청산가: ${liquidation_price:,.0f}"], textposition="bottom right", name="청산가"))
    
    fig_price.update_layout(yaxis_title="달러 ($)", showlegend=False, height=350, yaxis_range=[liquidation_price * 0.8, current_price * 1.1])
    st.plotly_chart(fig_price, use_container_width=True)

with col_chart2:
    st.subheader(f"🛡️ {display_leverage}배 설정 한도 대비 수량 비율")
    # Plotly 100% 누적 막대 차트 (게이지 효과)
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(y=["비율"], x=[entry_ratio_pct], name="진입 수량 비중", orientation='h', marker_color='royalblue', text=f"{entry_ratio_pct:.1f}%", textposition='inside'))
    fig_bar.add_trace(go.Bar(y=["비율"], x=[gap_ratio_pct], name="여유 마진 (갭) 비중", orientation='h', marker_color='lightgray', text=f"{gap_ratio_pct:.1f}%", textposition='inside'))
    
    fig_bar.update_layout(barmode='stack', xaxis_title="퍼센트 (%)", xaxis_range=[0, 100], showlegend=True, height=250)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.info(f"💡 **실전 주문 가이드:** 거래소 주문창에서 수량 슬라이더를 **{entry_ratio_pct:.1f}%** 까지만 당기시면 목표하신 **{target_eff_lev}배**의 안전한 실효 레버리지로 진입됩니다.")

st.caption("※ 본 시뮬레이터는 거래소 수수료 및 유지증거금률(MMR)을 제외한 수리적 모델링이며, 롱 포지션을 기준으로 계산되었습니다.")
