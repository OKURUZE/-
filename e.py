import os
import streamlit as st
import requests
import pandas as pd

# 다크모드 강제 적용
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[theme]\nbase='dark'\n")

st.set_page_config(page_title="비트코인 물타기 및 평단가 계산기", layout="wide")
st.title("📈 비트코인 물타기 및 평단가 계산기")

# 실시간 BTC 가격 가져오기 (OKX API)
@st.cache_data(ttl=10) # 10초간 가격 캐싱하여 잦은 깜빡임 방지
def get_btc_price():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=3).json()
        return float(response['data'][0]['last'])
    except Exception:
        return 60000.0 # 에러 시 임시 가격

# 사용자 입력칸 구성
col1, col2 = st.columns(2)
with col1:
    capital = st.number_input("총 자본금 (USDT)", min_value=10.0, value=32000.0, step=1000.0)
with col2:
    leverage = st.number_input("격리마진 레버리지 (x)", min_value=1, max_value=100, value=10, step=1)

btc_price = get_btc_price()
st.info(f"**현재 비트코인 가격 (OKX):** ${btc_price:,.2f}")

# 1~9회차 증거금 계산 (잔여 자본금 기준 역순)
remaining = capital
original_amounts = []
for i in range(9):
    rate = 0.10 + (0.05 * i)
    amount = remaining * rate
    original_amounts.append(amount)
    remaining -= amount
reversed_amounts = original_amounts[::-1]

# ★ 핵심: 초기 진입단가(None)를 담은 DataFrame을 Session State에 고정
if "df_data" not in st.session_state:
    initial_data = []
    for i in range(9):
        initial_data.append({
            "회차": f"{i+1}회차",
            "진입 비트코인 갯수 (BTC)": (reversed_amounts[i] * leverage) / btc_price,
            "실사용 증거금 (USDT)": reversed_amounts[i],
            "진입단가 (USDT)": None, 
            "평단가 (USDT)": None
        })
    st.session_state.df_data = pd.DataFrame(initial_data)

st.write("### 📊 회차별 진입 계획 및 누적 평단가")
st.caption("💡 **안내:** 표 안의 **'진입단가 (USDT)'** 빈칸을 클릭하여 예상 타점을 입력하세요.")

# 사용자가 입력할 수 있는 표 (자동으로 st.session_state에 값이 반영됨)
edited_df = st.data_editor(
    st.session_state.df_data,
    column_config={
        "회차": st.column_config.TextColumn("회차", disabled=True),
        "진입 비트코인 갯수 (BTC)": st.column_config.NumberColumn("진입 비트코인 갯수 (BTC)", format="%.5f", disabled=True),
        "실사용 증거금 (USDT)": st.column_config.NumberColumn("실사용 증거금 (USDT)", format="%.2f", disabled=True),
        "진입단가 (USDT)": st.column_config.NumberColumn("진입단가 (USDT)", format="%.2f", min_value=0.0),
        "평단가 (USDT)": st.column_config.NumberColumn("평단가 (USDT)", format="%.2f", disabled=True),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_key" # 이 키를 통해 값이 즉시 업데이트됨
)

# ★ 입력받은 진입단가를 바탕으로 평단가 실시간 재계산
cum_qty = 0
cum_cost = 0
total_margin = sum(reversed_amounts)
total_qty = sum(edited_df["진입 비트코인 갯수 (BTC)"])

# 계산용 빈 리스트
new_avg_prices = []

for index, row in edited_df.iterrows():
    ep = row["진입단가 (USDT)"]
    qty = row["진입 비트코인 갯수 (BTC)"]
    
    # 진입단가에 유효한 숫자가 입력되었을 때만 누적 계산
    if pd.notna(ep) and ep > 0:
        virtual_cost = qty * ep
        cum_qty += qty
        cum_cost += virtual_cost
        avg_price = cum_cost / cum_qty
        new_avg_prices.append(avg_price)
    else:
        new_avg_prices.append(None) # 입력 안 했으면 평단가도 빈칸

# 원본 DataFrame에 계산된 평단가 업데이트
edited_df["평단가 (USDT)"] = new_avg_prices

# 합계 행(마지막 줄)만 별도로 떼어내서 화면에 보여주기 위한 처리
summary_df = pd.DataFrame([{
    "회차": "합계",
    "진입 비트코인 갯수 (BTC)": total_qty,
    "실사용 증거금 (USDT)": total_margin,
    "진입단가 (USDT)": None,
    "평단가 (USDT)": None
}])

# 수정된 본문과 합계를 합쳐서 최종 테이블 모양 완성 (화면에만 표시)
final_display_df = pd.concat([edited_df, summary_df], ignore_index=True)

# 계산된 결과값을 다시 화면에 그리기 위해 Session State 업데이트
st.session_state.df_data = edited_df

st.write("---")
st.write("### 📌 합계 및 계산 결과")
st.dataframe(
    summary_df,
    column_config={
        "회차": st.column_config.TextColumn("회차"),
        "진입 비트코인 갯수 (BTC)": st.column_config.NumberColumn("진입 비트코인 갯수 (BTC)", format="%.5f"),
        "실사용 증거금 (USDT)": st.column_config.NumberColumn("실사용 증거금 (USDT)", format="%.2f"),
        "진입단가 (USDT)": st.column_config.TextColumn(""),
        "평단가 (USDT)": st.column_config.TextColumn(""),
    },
    hide_index=True,
    use_container_width=True
)

if st.button("🧮 표 전체 초기화 (현재가 기준으로 갯수 재계산)", use_container_width=True):
    # 버튼 누르면 세션 날려서 처음부터 다시 세팅
    del st.session_state.df_data
    st.rerun()
