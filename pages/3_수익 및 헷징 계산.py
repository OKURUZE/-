import streamlit as st
import requests

# 페이지 기본 설정 (가로로 넓게 쓰기)
st.set_page_config(page_title="BTC 현물-선물 헤징 계산기", layout="wide")

st.title("📊 BTC 멀티커런시 현물-선물 1:1 헤징 계산기")
st.caption("2초마다 실시간 비트코인 시세를 반영하여 수익금과 담보 가용금액이 자동 갱신됩니다.")

# 1. 사용자 입력 영역 (자동 새로고침 되지 않는 고정 영역)
st.subheader("📝 포지션 입력")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🪙 현물 (Spot)")
    spot_entry_price = st.number_input("현물 평단가 (USDT)", min_value=0.0, value=60000.0, step=100.0)
    spot_quantity = st.number_input("현물 보유 수량 (BTC)", min_value=0.0, value=1.0, step=0.01)

with col2:
    st.markdown("### 📈 선물 (Futures)")
    # 주로 숏 헤징을 하므로 Short을 기본값으로 둠
    position_side = st.radio("포지션 방향", ["Short (숏)", "Long (롱)"], horizontal=True)
    fut_entry_price = st.number_input("선물 평단가 (USDT)", min_value=0.0, value=60000.0, step=100.0)
    fut_leverage = st.number_input("선물 레버리지 (x)", min_value=1.0, value=10.0, step=1.0)
    fut_quantity = st.number_input("선물 비트 수량 (레버리지 적용된 총 포지션 수량)", min_value=0.0, value=1.0, step=0.01)

st.divider()

st.subheader("💡 실시간 수익 및 담보 현황")

# 2. 실시간 데이터 표시 영역 (2초마다 새로고침)
@st.fragment(run_every=2)
def display_realtime_data():
    try:
        # 바이낸스 퍼블릭 데이터 전용 API (차단 방지용)
        url = "https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        current_price = float(data['price'])
        
        # --- 계산 로직 ---
        # 1. 현물 수익금 계산
        spot_profit = (current_price - spot_entry_price) * spot_quantity
        
        # 2. 선물 수익금 계산 (롱/숏 방향에 따라 다르게 적용)
        if "Short" in position_side:
            fut_profit = (fut_entry_price - current_price) * fut_quantity
        else:
            fut_profit = (current_price - fut_entry_price) * fut_quantity
            
        # 3. 최종 상쇄 수익금 (현물 + 선물 합산)
        total_profit = spot_profit + fut_profit
        
        # 4. 담보 가용금액 (OKX 기준 약 95~97% 이나 보수적으로 90% 적용)
        haircut_ratio = 0.90
        available_margin = spot_quantity * current_price * haircut_ratio
        
        # 5. 사용 중인 선물 증거금 (참고용 데이터)
        used_margin = (fut_quantity * current_price) / fut_leverage if fut_leverage > 0 else 0
        
        # --- 화면 표시 UI ---
        st.metric(label="비트코인 현재가 (USDT)", value=f"${current_price:,.2f}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="🪙 현물 미실현 수익금", value=f"${spot_profit:,.2f}")
            # 멀티커런시 모드에서의 담보 가용 금액 강조 표시
            st.info(f"**현물 담보 가용 금액 (90% 인정):**\n\n### ${available_margin:,.2f}")
            
        with c2:
            st.metric(label="📈 선물 미실현 수익금", value=f"${fut_profit:,.2f}")
            # 입력한 레버리지에 따른 필요 증거금 표시
            st.warning(f"**선물 포지션 필요 증거금:**\n\n### ${used_margin:,.2f}")
            
        with c3:
            st.metric(label="🔥 최종 합산 수익 (Net Profit)", value=f"${total_profit:,.2f}")
            
            # 위험/안전 상태 알림 로직 (현물 담보로 선물 증거금을 커버할 수 있는지)
            total_equity_needed = used_margin
            if available_margin >= total_equity_needed:
                st.success(f"✅ 현물 담보가 충분하여 안전 상태입니다.")
            else:
                st.error(f"🚨 현물 담보 부족! 청산 위험이 있습니다.")
                
    except Exception as e:
        st.error(f"데이터 통신 에러가 발생했습니다: {e}")

# 실시간 뷰 함수 실행
display_realtime_data()
