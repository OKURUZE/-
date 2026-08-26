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
st.title("📈 비트코인 물타기 및 평단가 계산기")

# 실시간 BTC 가격 가져오기 (OKX API)
def get_btc_price():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=3).json()
        return float(response['data'][0]['last'])
    except Exception:
        return None

# 사용자 입력칸 구성
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

# 진입단가를 전부 빈칸(None)으로 초기화
if "user_entry_prices" not in st.session_state:
    st.session_state.user_entry_prices = [None] * 9

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
cum_qty = 0      
cum_cost = 0     
total_margin = 0 
total_display_qty = 0

for i in range(9):
    step_margin = reversed_amounts[i]
    total_margin += step_margin
    ep = st.session_state.user_entry_prices[i]
    
    # 1. 포지션 규모 계산
    position_size_usd = step_margin * leverage
    
    # 2. 비트코인 갯수는 무조건 '현재 비트코인 가격'을 기준으로 고정 계산
    btc_qty = position_size_usd / btc_price if btc_price > 0 else 0
    total_display_qty += btc_qty
    
    # 3. 평단가 계산: 진입단가(ep)가 입력되어 있을 때만 계산
    if ep is not None and ep > 0:
        # 입력한 진입단가(ep)에 고정된 코인 갯수(btc_qty)를 곱해 해당 회차의 '가상 포지션 가치'를 구함
        virtual_cost = btc_qty * ep 
        cum_qty += btc_qty
        cum_cost += virtual_cost
        avg_price = cum_cost / cum_qty if cum_qty > 0 else None
    else:
        avg_price = None # 평단가는 비워둠
        
    data.append({
        "회차": f"{i+1}회차",
        "진입 비트코인 갯수 (BTC)": btc_qty,
        "실사용 증거금 (USDT)": step_margin,
        "진입단가 (USDT)": ep,
        "평단가 (USDT)": avg_price
    })

# 합계 행 추가 
data.append({
    "회차": "합계",
    "진입 비트코인 갯수 (BTC)": total_display_qty,
    "실사용 증거금 (USDT)": total_margin,
    "진입단가 (USDT)": None, 
    "평단가 (USDT)": None    
})

df = pd.DataFrame(data)

st.write("### 📊 회차별 진입 계획 및 누적 평단가")
st.caption("💡 **안내:** 표 안의 **'진입단가 (USDT)'** 빈칸에 예상 타점을 입력하고 **[Enter]** 키를 누르세요. (진입 갯수는 고정되며 평단가만 계산됩니다.)")

# 인터랙티브 표(Data Editor) 출력 
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

# 표에서 '진입단가'가 수정되었는지 감지 (NaN 값은 None으로 변환)
edited_prices_raw = edited_df["진입단가 (USDT)"].tolist()[:-1]
clean_prices = [None if pd.isna(p) else float(p) for p in edited_prices_raw]

if clean_prices != st.session_state.user_entry_prices:
    st.session_state.user_entry_prices = clean_prices
    st.rerun()

st.write("---")

if st.button("🧮 실시간 비트코인 현재가 새로고침", use_container_width=True):
    st.rerun()
