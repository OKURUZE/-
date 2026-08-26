import streamlit as st

st.set_page_config(page_title="쐐기형 분석기", page_icon="📉")

st.title("📉 쐐기형 패턴(Wedge) 분석기")
st.write("하락/상승 쐐기형 패턴의 100% 회귀 목표가, 손절 라인, 리테스트 방어 한계치를 정밀 분석합니다.")

# 패턴 선택
wedge_type = st.radio(
    "🔍 분석할 쐐기형 패턴을 선택하세요",
    ("하락 쐐기형 (Falling Wedge)", "상승 쐐기형 (Rising Wedge)")
)

# 💡 선택한 패턴에 따라 라벨 텍스트를 동적으로 변수화
if "하락" in wedge_type:
    start_high_label = "시작점 고가 (A 파동의 꼭대기)"
    start_low_label = "시작점 저가 (B 파동의 바닥)"
    last_swing_label = "돌파 직전 마지막 파동의 최저점"
    direction_text = "상방 돌파"
else:
    start_high_label = "시작점 고가 (A 파동의 꼭대기)" # A파동은 항상 고점부터 시작하는 기준으로 통일
    start_low_label = "시작점 저가 (B 파동의 바닥)"
    last_swing_label = "이탈 직전 마지막 파동의 최고점"
    direction_text = "하방 이탈"

with st.form("wedge_form"):
    col1, col2 = st.columns(2)
    with col1:
        bars_to_apex = st.number_input("시작점 ~ 꼭짓점 총 봉수", min_value=10, value=80)
        default_breakout = int(bars_to_apex * 0.75)
        breakout_bar = st.number_input(f"예상/실제 {direction_text} 캔들 위치", min_value=1, max_value=int(bars_to_apex), value=default_breakout)
    
    with col2:
        # 💡 위에서 설정한 변수를 label에 적용
        start_high = st.number_input(start_high_label, value=72000.0, format="%.2f")
        start_low = st.number_input(start_low_label, value=64000.0, format="%.2f")
        last_swing = st.number_input(last_swing_label, value=65000.0, format="%.2f")
    
    submit_button = st.form_submit_button(label=f"쐐기형 분석 및 {direction_text} 목표가 계산")

if submit_button:
    initial_width = start_high - start_low
    
    if initial_width <= 0:
        st.error("⚠️ 시작점 고가가 저가보다 높아야 합니다. 입력하신 가격을 확인해 주세요.")
    else:
        ideal_start = int(bars_to_apex * 0.65)
        ideal_end = int(bars_to_apex * 0.85)
        narrowed_width = initial_width * (1 - (breakout_bar / bars_to_apex))
        retest_limit = narrowed_width * 0.50

        st.success(f"✅ 분석 완료: {wedge_type}")

        # 1. 돌파 구간
        st.subheader(f"🎯 1. 이상적인 {direction_text} 발생 구간 (65% ~ 85%)")
        st.info(f"가장 신뢰도 높은 {direction_text} 타점은 시작점으로부터 **{ideal_start}번째 ~ {ideal_end}번째 봉** 사이입니다.")
        
        # 2. 목표가 및 손절가
        st.subheader("📊 2. 1차 목표가 및 패턴 무효화 라인")
        if "하락" in wedge_type:
            st.write(f"👉 **1차 목표가:** 패턴이 시작된 최초 고점인 **{start_high:,.2f}** (100% 회귀)")
            st.write(f"🛑 **기계적 손절가:** 마지막으로 다졌던 최저점 **{last_swing:,.2f}** 하향 이탈 시 즉시 손절")
        else:
            st.write(f"👉 **1차 목표가:** 패턴이 시작된 최초 저점인 **{start_low:,.2f}** (100% 회귀)")
            st.write(f"🛑 **기계적 무효화:** 마지막으로 올렸던 최고점 **{last_swing:,.2f}** 상향 돌파 시 즉시 관망")

        # 3. 리테스트 방어 한계치
        st.subheader("🛡️ 3. 리테스트 방어 한계치")
        st.error(f"돌파 시점의 좁아진 폭: **{narrowed_width:.2f}**\n\n돌파 후 캔들이 다시 뚫고 나온 추세선 안쪽으로 **{retest_limit:.2f} 이상 깊게 파고들며 마감**하면 트랩(가짜 돌파)으로 판단합니다.")
