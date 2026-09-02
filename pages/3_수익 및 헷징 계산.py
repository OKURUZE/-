import streamlit as st
import requests

# 페이지 기본 설정
st.set_page_config(page_title="BTC 현물 수익 계산기", layout="wide")

st.title("📊 비트코인 현물 실시간 수익 계산기")
st.caption("입력창에 값을 넣으면 2초마다 실시간 비트코인 가격을 반영하여 수익금이 자동 갱신됩니다.")

# 1. 사용자 입력 영역 (자동 새로고침 되지 않는 고정 영역)
col1, col2 = st.columns(2)
with col1:
    # 현물 평단가 입력 (기본값 60000)
    entry_price = st.number_input("현물 평단가 (USDT)", min_value=0.0, value=60000.0, step=100.0)
with col2:
    # 보유 수량 입력 (기본값 1.0)
    quantity = st.number_input("보유 수량 (BTC)", min_value=0.0, value=1.0, step=0.01)

st.divider()

# 2. 실시간 데이터 표시 영역
# run_every=2 옵션으로 인해 이 함수 내부만 2초마다 자동으로 다시 실행됨
@st.fragment(run_every=2)
def display_realtime_data():
    try:
        # 바이낸스 API를 통해 비트코인 현재가 호출
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        current_price = float(response.json()['price'])
        
        # 수익금 및 수익률 계산
        profit = (current_price - entry_price) * quantity
        if entry_price > 0:
            profit_rate = (current_price - entry_price) / entry_price * 100
        else:
            profit_rate = 0.0
            
        # 화면에 수치 표시 (st.metric 활용)
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="비트코인 현재가 (USDT)", value=f"${current_price:,.2f}")
        with c2:
            st.metric(
                label="현재 미실현 수익금 (USDT)", 
                value=f"${profit:,.2f}", 
                delta=f"{profit_rate:,.2f}%"
            )
            
    except Exception as e:
        st.error("가격을 불러오는 중 오류가 발생했습니다. 네트워크 상태를 확인하세요.")

# 자동 갱신되는 뷰 함수 실행
display_realtime_data()
