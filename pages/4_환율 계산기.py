import streamlit as st
import yfinance as yf

st.set_page_config(page_title="실시간 환율 계산기", page_icon="💱")

# 환율 데이터 가져오기 (API 호출 최적화를 위해 60초 캐싱)
@st.cache_data(ttl=60)
def get_exchange_rates():
    # Yahoo Finance에서 실시간 환율 종가 가져오기
    usd_krw = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
    jpy_krw = yf.Ticker("JPYKRW=X").history(period="1d")['Close'].iloc[-1]
    usd_jpy = yf.Ticker("USDJPY=X").history(period="1d")['Close'].iloc[-1]
    return usd_krw, jpy_krw, usd_jpy

st.title("💱 실시간 환율 변환기")

try:
    with st.spinner("실시간 환율 데이터를 불러오는 중입니다..."):
        usd_krw, jpy_krw, usd_jpy = get_exchange_rates()
    
    # 1. 실시간 달러/엔 환율 표시 (한국 표준에 맞춰 엔화는 100엔 기준으로 표시)
    st.subheader("현재 환율 (실시간)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="1 달러(USD)", value=f"{usd_krw:,.2f} 원")
    with col2:
        st.metric(label="100 엔(JPY)", value=f"{jpy_krw * 100:,.2f} 원")
        
    st.divider()

    # 2. 달러(USD) 입력칸 및 변환 결과
    st.subheader("🇺🇸 달러(USD) 입력")
    usd_input = st.number_input("달러(USD) 금액을 입력하세요:", min_value=0.0, value=1.0, format="%.2f")
    
    usd_to_krw = usd_input * usd_krw
    usd_to_jpy = usd_input * usd_jpy
    
    st.info(f"**{usd_input:,.2f} USD** = **{usd_to_krw:,.0f} 원** / **{usd_to_jpy:,.2f} 엔**")
    
    st.divider()

    # 3. 엔(JPY) 입력칸 및 변환 결과
    st.subheader("🇯🇵 엔(JPY) 입력")
    jpy_input = st.number_input("엔(JPY) 금액을 입력하세요:", min_value=0.0, value=100.0, format="%.2f")
    
    jpy_to_krw = jpy_input * jpy_krw
    jpy_to_usd = jpy_input / usd_jpy
    
    st.success(f"**{jpy_input:,.2f} JPY** = **{jpy_to_krw:,.0f} 원** / **{jpy_to_usd:,.2f} 달러**")
    
except Exception as e:
    st.error("환율 데이터를 불러오는 중 오류가 발생했습니다. 야후 파이낸스 서버 문제일 수 있으니 잠시 후 새로고침 해주세요.")
