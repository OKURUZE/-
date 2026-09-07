import streamlit as st
import yfinance as yf

st.set_page_config(page_title="실시간 환율 계산기", page_icon="💱")

# 환율 데이터 가져오기 (API 호출 최적화를 위해 60초 캐싱)
@st.cache_data(ttl=10)
def get_exchange_rates():
    usd_krw = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
    jpy_krw = yf.Ticker("JPYKRW=X").history(period="1d")['Close'].iloc[-1]
    usd_jpy = yf.Ticker("USDJPY=X").history(period="1d")['Close'].iloc[-1]
    return usd_krw, jpy_krw, usd_jpy

# 세션 상태 초기화 (기본값 설정)
if "usd_str" not in st.session_state:
    st.session_state.usd_str = "1"
if "jpy_str" not in st.session_state:
    st.session_state.jpy_str = "100"

# 입력 시 3자리마다 자동으로 쉼표(,)를 찍어주는 함수
def format_usd():
    raw = st.session_state.usd_str.replace(",", "").strip()
    if not raw:
        return
    try:
        val = float(raw)
        if "." in raw:
            parts = raw.split(".")
            int_part = int(parts[0]) if parts[0] else 0
            st.session_state.usd_str = f"{int_part:,}.{parts[1]}"
        else:
            st.session_state.usd_str = f"{int(val):,}"
    except ValueError:
        pass

def format_jpy():
    raw = st.session_state.jpy_str.replace(",", "").strip()
    if not raw:
        return
    try:
        val = float(raw)
        if "." in raw:
            parts = raw.split(".")
            int_part = int(parts[0]) if parts[0] else 0
            st.session_state.jpy_str = f"{int_part:,}.{parts[1]}"
        else:
            st.session_state.jpy_str = f"{int(val):,}"
    except ValueError:
        pass

st.title("💱 실시간 환율 변환기")

try:
    with st.spinner("실시간 환율 데이터를 불러오는 중입니다..."):
        usd_krw, jpy_krw, usd_jpy = get_exchange_rates()
    
    # 1. 실시간 달러/엔 환율 표시
    st.subheader("현재 환율 (실시간)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="1 달러(USD)", value=f"{usd_krw:,.2f} 원")
    with col2:
        st.metric(label="100 엔(JPY)", value=f"{jpy_krw * 100:,.2f} 원")
        
    st.divider()

    # 2. 달러(USD) 입력칸 및 변환 결과
    st.subheader("🇺🇸 달러(USD) 입력")
    st.text_input("달러(USD) 금액을 입력하세요:", key="usd_str", on_change=format_usd)
    
    # 쉼표를 제거하고 숫자로 계산
    try:
        usd_val = float(st.session_state.usd_str.replace(",", "").strip() or 0)
    except ValueError:
        usd_val = 0.0
        
    usd_to_krw = usd_val * usd_krw
    usd_to_jpy = usd_val * usd_jpy
    
    st.info(f"**{usd_val:,.2f} USD** = **{usd_to_krw:,.0f} 원** / **{usd_to_jpy:,.2f} 엔**")
    
    st.divider()

    # 3. 엔(JPY) 입력칸 및 변환 결과
    st.subheader("🇯🇵 엔(JPY) 입력")
    st.text_input("엔(JPY) 금액을 입력하세요:", key="jpy_str", on_change=format_jpy)
    
    # 쉼표를 제거하고 숫자로 계산
    try:
        jpy_val = float(st.session_state.jpy_str.replace(",", "").strip() or 0)
    except ValueError:
        jpy_val = 0.0
        
    jpy_to_krw = jpy_val * jpy_krw
    jpy_to_usd = jpy_val / usd_jpy
    
    st.success(f"**{jpy_val:,.2f} JPY** = **{jpy_to_krw:,.0f} 원** / **{jpy_to_usd:,.2f} 달러**")
    
except Exception as e:
    st.error("환율 데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 새로고침 해주세요.")
