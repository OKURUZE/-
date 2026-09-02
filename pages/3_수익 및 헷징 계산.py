import streamlit as st
import requests

# 페이지 기본 설정 (가로로 넓게 쓰기)
st.set_page_config(page_title="BTC 멀티커런시 계산기", layout="wide")

st.title("📊 BTC 멀티커런시 종합 헤징 계산기")
st.caption("2초마다 실시간 비트코인 시세를 반영하여 모든 수치가 자동 갱신됩니다.")

# 1. 사용자 입력 영역 (고정 영역)
st.subheader("📝 포지션 입력")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🪙 현물 (Spot)")
    spot_entry_price = st.number_input("현물 평단가 (USDT)", min_value=0.0, value=60000.0, step=100.0)
    spot_quantity = st.number_input("현물 보유 수량 (BTC)", min_value=0.0, value=1.0, step=0.01)

with col2:
    st.markdown("### 📈 선물 (Futures)")
    position_side = st.radio("포지션 방향", ["Short (숏)", "Long (롱)"], horizontal=True)
    fut_entry_price = st.number_input("선물 평단가 (USDT)", min_value=0.0, value=60000.0, step=100.0)
    fut_leverage = st.number_input("선물 레버리지 (x)", min_value=1.0, value=10.0, step=1.0)
    fut_quantity = st.number_input("선물 비트 수량 (레버리지가 적용된 총 수량)", min_value=0.0, value=1.0, step=0.01)

st.divider()
st.subheader("💡 실시간 종합 분석 현황")

# 2. 실시간 데이터 표시 영역 (2초마다 새로고침)
@st.fragment(run_every=2)
def display_realtime_data():
    try:
        # 바이낸스 퍼블릭 데이터 전용 API
        url = "https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        current_price = float(response.json()['price'])
        
        # --- 1. 기본 수익금 계산 ---
        spot_profit = (current_price - spot_entry_price) * spot_quantity
        
        if "Short" in position_side:
            fut_profit = (fut_entry_price - current_price) * fut_quantity
        else:
            fut_profit = (current_price - fut_entry_price) * fut_quantity
            
        total_profit = spot_profit + fut_profit
        
        # --- 2. 멀티커런시 담보 & 증거금 계산 ---
        haircut_ratio = 0.90
        # 2-1. 현물 담보 가용 금액 (할인율만 적용된 순수 현물 가치)
        available_margin = spot_quantity * current_price * haircut_ratio 
        
        # 2-2. 선물 포지션 필요 증거금 (레버리지 칠 때 필요한 보증금 = 개시 증거금)
        used_margin = (fut_quantity * current_price) / fut_leverage if fut_leverage > 0 else 0
        
        # 2-3. 진짜 순 담보 가치 (현물 담보 가치 + 선물 손익 합산)
        net_equity = available_margin + fut_profit 
        
        # 2-4. 유지 증거금 (사망선, 통상 0.5% 적용)
        maintenance_margin = (fut_quantity * current_price) * 0.005 
        
        # --- 화면 표시 UI (상세 지표 모두 부활) ---
        
        # [상단] 현재가 및 최종 수익
        top1, top2 = st.columns(2)
        with top1:
            st.metric(label="🌐 비트코인 현재가 (USDT)", value=f"${current_price:,.2f}")
        with top2:
            st.metric(label="🔥 최종 합산 수익 (Net Profit)", value=f"${total_profit:,.2f}", 
                      delta="현물 수익금 + 선물 수익금")
            
        st.write("---")
        
        # [중단] 수익금 상세 내역 및 담보 비교
        mid1, mid2 = st.columns(2)
        with mid1:
            st.markdown("#### 🪙 현물 상세 현황")
            st.metric(label="현물 미실현 수익금", value=f"${spot_profit:,.2f}")
            st.info(f"**현물 담보 가용 금액 (90% 적용):**\n\n### ${available_margin:,.2f}")
            
        with mid2:
            st.markdown("#### 📈 선물 상세 현황")
            st.metric(label="선물 미실현 수익금", value=f"${fut_profit:,.2f}")
            st.warning(f"**선물 포지션 필요 증거금 (개시 증거금):**\n\n### ${used_margin:,.2f}")
            
        st.write("---")
        
        # [하단] 청산 마지노선 비교
        bot1, bot2 = st.columns(2)
        with bot1:
            st.metric(label="⚖️ 진짜 순 담보 가치 (Net Equity)", value=f"${net_equity:,.2f}")
            st.caption("현물 담보 가용 금액에서 선물 손익을 실시간으로 더하고 뺀 실제 내 돈")
        with bot2:
            st.metric(label="⚠️ 유지 증거금 (청산 마지노선)", value=f"${maintenance_margin:,.2f}")
            st.caption("순 담보 가치가 이 금액 밑으로 떨어지면 강제 청산 발생")
            
        # --- 청산 엔진 시뮬레이션 알림 ---
        st.write("") # 간격 띄우기
        if net_equity <= maintenance_margin:
            st.error("💀 강제 청산 발생! (순 담보가 유지 증거금 밑으로 추락했습니다. 현물이 시장가로 강제 매각됩니다.)")
        elif net_equity <= used_margin:
            # HTML과 CSS를 사용해 경고창의 배경색(빨간색)과 글자색(흰색)을 직접 지정
            st.markdown(
                """
                <div style="background-color: #D32F2F; color: white; padding: 16px; border-radius: 8px;">
                    <strong>🚨 마진콜 위험!</strong> (순 담보가 필요 증거금 밑으로 떨어졌습니다. 레버리지를 낮추거나 테더를 입금해야 합니다.)
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            safety_buffer = net_equity - used_margin
            st.success(f"✅ 안전 상태입니다. (마진콜 경고선까지 약 ${safety_buffer:,.2f}의 여유 담보가 남아있습니다.)")
                
    except Exception as e:
        st.error(f"데이터 통신 에러가 발생했습니다: {e}")

# 실시간 뷰 함수 실행
display_realtime_data()
