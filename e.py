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
st.set_page_config(page_title="비트코인 물타기 및 평단가 계산기", layout="wide")

# 1. 제목 수정
st.title("📈 비트코인 물타기 및 평단가 계산기")

# 실시간 BTC 가격 가져오기 (OKX API)
def get_btc_price():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=3).json()
        return float(response['data'][0]['last'])
    except Exception:
        return None

# 2. 넘버링(숫자) 제거된 사용자 입력칸 구성
col1, col2 = st.columns(2)
with col1:
    capital = st.number_input("총 자본금 (USDT)", min_value=10.0, value=32000.0, step=1000.0)
with col2:
    leverage = st.number_input("격리마진 레버리지 (x)", min_value=1, max_value=100, value=10, step=1)

# 실시간 가격 표시
btc_price = get_btc_price()
if btc_price:
    st.info(f"**현재 비트코인 가격 (OKX):** ${btc_price:,.2f}")
else:
    btc_price = 60000.0 
    st.warning("가격을 불러오는데 실패하여 임시 가격($60,000)이 적용됩니다.")

# 표에서 직접 수정할 수 있도록 진입단가를 메모리(Session State)에 저장
if "user_entry_prices" not in st.session_state:
    st.session_state.user_entry_prices = [btc_price] * 9

# 1~9회차 금액 계산 (잔여 자본금 기준 역순)
remaining = capital
original_amounts = []
for i in range(9):
    rate = 0.10 + (0.05 * i)
    amount = remaining * rate
    original_amounts.append(amount)
    remaining -= amount
reversed_amounts = original_amounts[::-1]

# 데이터 프레임 생성을 위한 계산
data = []
cum_qty = 0      # 누적 비트코인 갯수
cum_cost = 0     # 누적 포지션 가치
total_margin = 0 # 총 사용 증거금

for i in range(9):
    step_margin = reversed_amounts[i]
    ep = st.session_state.user_entry_prices[i] # 사용자가 수정한 진입단가 가져오기
    
    # 레버리지 적용 포지션 규모
    position_size_usd = step_margin * leverage
    
    # 해당 회차의 진입 비트코인 갯수 계산
    btc_qty = position_size_usd / ep if ep and ep > 0 else 0
    
    # 누적 합산
    cum_qty += btc_qty
    cum_cost += position_size_usd
    total_margin += step_margin
    
    # 평단가 = 총 투입된 포지션 규모 / 총 매수된 코인 갯수
    avg_price = cum_cost / cum_qty if cum_qty > 0 else 0
    
    # 3. 기존 열 삭제 및 진입단가, 평단가 열 반영
    data.append({
        "회차": f"{i+1}회차",
        "진입 비트코인 갯수 (BTC)": btc_qty,
        "실사용 증거금 (USDT)": step_margin,
        "진입단가 (USDT)": ep,
        "평단가 (USDT)": avg_price
    })

# 4. 9번(10번째 줄)에 합계 행 추가 (단가부분은 빈칸 처리)
data.append({
    "회차": "합계",
    "진입 비트코인 갯수 (BTC)": cum_qty,
    "실사용 증거금 (USDT)": total_margin,
    "진입단가 (USDT)": None, # 빈칸 처리
    "평단가 (USDT)": None    # 빈칸 처리
})

df = pd.DataFrame(data)

st.write("### 📊 회차별 진입 계획 및 누적 평단가")
st.caption("💡 **안내:** 표 안의 **'진입단가'** 숫자를 클릭하여 원하는 가격으로 수정하고 **[Enter]** 키를 누르면 **자동으로 즉시 계산**됩니다.")

# 인터랙티브 표(Data Editor) 출력 (엑셀처럼 수정 가능)
edited_df = st.data_editor(
    df,
    column_config={
        "회차": st.column_config.TextColumn("회차", disabled=True),
        "진입 비트코인 갯수 (BTC)": st.column_config.NumberColumn("진입 비트코인 갯수 (BTC)", format="%.5f", disabled=True),
        "실사용 증거금 (USDT)": st.column_config.NumberColumn("실사용 증거금 (USDT)", format="%.2f", disabled=True),
        "진입단가 (USDT)": st.column_config.NumberColumn("진입단가 (USDT)", format="%.2f", min_value=0.0),
        "평단가 (USDT)": st.column_config.NumberColumn("평단가 (USDT)", format="%.2f", disabled=True),
    },
    hide_index=True,
    use_container_width=True
)

# 표에서 '진입단가'가 수정되었는지 감지하고, 변경되었다면 즉시 새로고침하여 계산 반영
edited_prices = edited_df["진입단가 (USDT)"].tolist()[:-1] # 마지막 '합계' 행의 데이터는 제외
edited_prices = [p if p is not None else 0 for p in edited_prices] # 값을 실수로 지웠을 때 에러 방지

if edited_prices != st.session_state.user_entry_prices:
    st.session_state.user_entry_prices = edited_prices
    st.rerun()

st.write("---")

# 하단 버튼부
col1, col2 = st.columns(2)
with col1:
    if st.button("🧮 실시간 가격 새로고침 및 수동 계산", use_container_width=True):
        st.rerun()
with col2:
    if st.button("🔄 모든 회차 진입단가를 '현재가'로 초기화", use_container_width=True):
        st.session_state.user_entry_prices = [btc_price] * 9
        st.rerun()
