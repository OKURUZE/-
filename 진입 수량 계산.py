import os
import streamlit as st
import requests
import pandas as pd

# 다크모드 강제 적용
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[theme]\nbase='dark'\n")

st.set_page_config(page_title="코인 물타기 및 평단가 계산기", layout="wide")

# 1. 메인 제목
st.title("📈 코인 물타기 및 평단가 계산기")

# 2. 코인 선택 드롭다운 (우측 정렬을 위해 8.5 : 1.5 비율로 공간 분할)
col_empty, col_drop = st.columns([8.5, 1.5])
with col_drop:
    selected_coin = st.selectbox(
        "코인 선택", 
        ["비트코인 (BTC)", "이더리움 (ETH)"],
        label_visibility="collapsed" # 레이블 글자를 숨겨서 깔끔하게 우측에 붙임
    )

# 선택된 코인에 따라 심볼 할당
symbol = "BTC" if "비트코인" in selected_coin else "ETH"

# ★ 코인을 변경하면 표에 저장된 기존(과거) 데이터를 완전히 초기화하고 새로고침
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = symbol

if st.session_state.current_symbol != symbol:
    st.session_state.current_symbol = symbol
    if "df_data" in st.session_state:
        del st.session_state.df_data
    st.rerun()

# 실시간 가격 가져오기 (선택된 심볼에 맞춰 API 요청)
@st.cache_data(ttl=10) # 10초간 가격 캐싱
def get_coin_price(coin_symbol):
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={coin_symbol}-USDT"
        response = requests.get(url, timeout=3).json()
        return float(response['data'][0]['last'])
    except Exception:
        # 에러 시 임시 가격
        return 60000.0 if coin_symbol == "BTC" else 3000.0

# 사용자 입력칸 구성
col1, col2 = st.columns(2)
with col1:
    capital = st.number_input("총 자본금 (USDT)", min_value=10.0, value=32000.0, step=1000.0)
with col2:
    leverage = st.number_input("격리마진 레버리지 (x)", min_value=1, max_value=100, value=10, step=1)

coin_price = get_coin_price(symbol)
st.info(f"**현재 {selected_coin} 가격 (OKX):** ${coin_price:,.2f}")

# 1~9회차 증거금 계산 (잔여 자본금 기준 역순)
remaining = capital
original_amounts = []
for i in range(9):
    rate = 0.10 + (0.05 * i)
    amount = remaining * rate
    original_amounts.append(amount)
    remaining -= amount
reversed_amounts = original_amounts[::-1]

# 선택된 코인에 따라 표의 열(Column) 이름도 동적으로 변경
qty_col = f"진입 갯수 ({symbol})"

# 세션 스테이트 초기화 (최초 1회 실행)
if "df_data" not in st.session_state:
    initial_data = []
    for i in range(9):
        initial_data.append({
            "회차": f"{i+1}회차",
            qty_col: (reversed_amounts[i] * leverage) / coin_price,
            "실사용 증거금 (USDT)": reversed_amounts[i],
            "진입단가 (USDT)": None, 
            "평단가 (USDT)": None
        })
    st.session_state.df_data = pd.DataFrame(initial_data)

st.write("### 📊 회차별 진입 계획 및 누적 평단가")
st.caption("💡 **안내:** 표 안의 **'진입단가 (USDT)'** 빈칸에 예상 타점을 입력하고 **[Enter]**를 치면 즉시 평단가가 계산됩니다.")

# 표 출력 (사용자 입력 받기)
edited_df = st.data_editor(
    st.session_state.df_data,
    column_config={
        "회차": st.column_config.TextColumn("회차", disabled=True),
        qty_col: st.column_config.NumberColumn(qty_col, format="%.5f", disabled=True),
        "실사용 증거금 (USDT)": st.column_config.NumberColumn("실사용 증거금 (USDT)", format="%.2f", disabled=True),
        "진입단가 (USDT)": st.column_config.NumberColumn("진입단가 (USDT)", format="%.2f", min_value=0.0),
        "평단가 (USDT)": st.column_config.NumberColumn("평단가 (USDT)", format="%.2f", disabled=True),
    },
    hide_index=True,
    use_container_width=True
)

# 수정된 진입단가를 바탕으로 평단가 다시 계산
cum_qty = 0
cum_cost = 0
new_avg_prices = []

for index, row in edited_df.iterrows():
    ep = row["진입단가 (USDT)"]
    qty = row[qty_col]
    
    if pd.notna(ep) and ep > 0:
        virtual_cost = qty * ep
        cum_qty += qty
        cum_cost += virtual_cost
        new_avg_prices.append(cum_cost / cum_qty)
    else:
        new_avg_prices.append(None)

# 계산된 평단가를 데이터프레임에 덮어쓰기
edited_df["평단가 (USDT)"] = new_avg_prices

# 진입단가에 입력(변화)이 감지되면 즉시 데이터를 저장하고 화면을 강제 새로고침
if not edited_df["진입단가 (USDT)"].equals(st.session_state.df_data["진입단가 (USDT)"]):
    st.session_state.df_data = edited_df
    st.rerun()

# 합계(마지막 줄) 계산 
total_qty = edited_df[qty_col].sum()
total_margin = sum(reversed_amounts)

summary_df = pd.DataFrame([{
    "회차": "합계",
    qty_col: total_qty,
    "실사용 증거금 (USDT)": total_margin,
    "진입단가 (USDT)": None,
    "평단가 (USDT)": None
}])

st.write("---")
st.write("### 📌 합계 및 계산 결과")
st.dataframe(
    summary_df,
    column_config={
        "회차": st.column_config.TextColumn("회차"),
        qty_col: st.column_config.NumberColumn(qty_col, format="%.5f"),
        "실사용 증거금 (USDT)": st.column_config.NumberColumn("실사용 증거금 (USDT)", format="%.2f"),
        "진입단가 (USDT)": st.column_config.TextColumn(""),
        "평단가 (USDT)": st.column_config.TextColumn(""),
    },
    hide_index=True,
    use_container_width=True
)

if st.button("🧮 표 전체 초기화 (현재가 기준으로 갯수 재계산)", use_container_width=True):
    del st.session_state.df_data
    st.rerun()
