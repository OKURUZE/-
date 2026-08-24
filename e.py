import os
import streamlit as st
import requests
import pandas as pd

# 다크모드 강제 적용을 위한 설정 파일 자동 생성
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[theme]\nbase='dark'\n")

# 페이지 설정
st.set_page_config(page_title="BTC 9분할 물타기 계산기", layout="wide")
st.title("📈 비트코인 9분할 물타기 계산기 (OKX 기준)")

# 실시간 BTC 가격 가져오기 (OKX API)
def get_btc_price():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=3).json()
        return float(response['data'][0]['last'])
    except Exception:
        st.error("가격을 불러오는데 실패했습니다. 네트워크를 확인하세요.")
        return None

# 사용자 입력칸 구성
col1, col2 = st.columns(2)
with col1:
    capital = st.number_input("1. 총 자본금 (USDT)", min_value=10.0, value=32000.0, step=1000.0)
with col2:
    leverage = st.number_input("4. 격리마진 레버리지 (x)", min_value=1, max_value=100, value=20, step=1)

# 실시간 가격 표시
btc_price = get_btc_price()
if btc_price:
    st.info(f"**3. 현재 비트코인 가격 (OKX):** ${btc_price:,.2f}")
else:
    btc_price = 60000.0 
    st.warning("임시 가격($60,000)으로 계산됩니다.")

# 1~9회차 금액 계산 (잔여 자본금 기준)
remaining = capital
original_amounts = []
for i in range(9):
    rate = 0.10 + (0.05 * i)
    amount = remaining * rate
    original_amounts.append(amount)
    remaining -= amount

# 거꾸로 1회차에 배치 (역순 정렬)
reversed_amounts = original_amounts[::-1]

# 데이터 프레임 생성
data = []
cumulative_margin = 0

for i in range(9):
    step_margin = reversed_amounts[i]
    cumulative_margin += step_margin
    
    # 레버리지 적용 포지션 규모 및 비트코인 갯수 계산
    position_size_usd = step_margin * leverage
    btc_qty = position_size_usd / btc_price
    
    # 열 순서 변경: 비트코인 갯수를 회차 바로 옆으로 배치
    data.append({
        "회차": f"{i+1}회차",
        "진입 비트코인 갯수 (BTC)": f"{btc_qty:.5f} 개",
        "실사용 증거금 (USDT)": f"${step_margin:,.2f}",
        "누적 증거금 (USDT)": f"${cumulative_margin:,.2f}",
        f"포지션 규모 ({leverage}x 적용)": f"${position_size_usd:,.2f}"
    })

df = pd.DataFrame(data)

# 테이블 출력
st.write("### 📊 회차별 진입 계획 (역순 적용)")
st.dataframe(df, use_container_width=True)

# 가격 새로고침 버튼
if st.button("🔄 실시간 가격 새로고침"):
    st.rerun()