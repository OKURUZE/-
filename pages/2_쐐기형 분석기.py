import streamlit as st

# 사이드바 2번 탭 이름과 아이콘 설정
st.set_page_config(page_title="쐐기형 분석기", page_icon="📉")

st.title("📉 쐐기형 패턴(Wedge) 분석기")
st.write("하락/상승 쐐기형 패턴의 100% 회귀 목표가, 손절 라인, 리테스트 방어 한계치를 정밀 분석합니다.")

# 💡 쐐기형은 방향성이 중요하므로 라디오 버튼으로 직관적으로 선택하게 구성
wedge_type = st.radio(
    "🔍 분석할 쐐기형 패턴을 선택하세요",
    ("하락 쐐기형 (Falling Wedge - 상방 돌파 기대)", 
     "상승 쐐기형 (Rising Wedge - 하방 이탈 기대)")
)

with st.form("wedge_form"):
    col1, col2 = st.columns(2)
    with col1:
        bars_to_apex = st.number_input("시작점 ~ 꼭짓점 총 봉수", min_value=10, value=80)
        # 쐐기형은 꼭짓점 가까이 꽉 채우는 경향이 있어 기본값을 75%로 설정
        default_breakout = int(bars_to_apex * 0.75)
        breakout_bar = st.number_input("실제/예상 돌파 발생 캔들 위치", min_value=1, max_value=int(bars_to_apex), value=default_breakout)
    
    with col2:
        start_high = st.number_input("시작점 고가 (패턴 최고점)", value=72000.0, format="%.2f")
        start_low = st.number_input("시작점 저가 (패턴 최저점)", value=64000.0, format="%.2f")
        # 💡 쐐기형 전용 입력칸: 기계적 손절가를 잡기 위한 직전 파동 위치
        last_swing = st.number_input("돌파 직전 마지막 파동의 저점(또는 고점)", value=65000.0, format="%.2f")
    
    submit_button = st.form_submit_button(label="쐐기형 분석 및 목표가 계산")

if submit_button:
    initial_width = start_high - start_low
    
    if initial_width <= 0:
        st.error("⚠️ 시작점 고가가 저가보다 높아야 합니다. 입력하신 가격을 확인해 주세요.")
    else:
        # 쐐기형 전용 수학 계산 로직 (65% ~ 85%)
        ideal_start = int(bars_to_apex * 0.65)
        ideal_end = int(bars_to_apex * 0.85)
        narrowed_width = initial_width * (1 - (breakout_bar / bars_to_apex))
        
        # 리테스트(풀백) 허용 최대 한계치 (좁아진 폭의 50%)
        retest_limit = narrowed_width * 0.50

        st.success(f"✅ 분석 완료: {wedge_type}")

        # ==========================================
        # 1. 이상적인 돌파 발생 구간 (쐐기형 전용: 65~85%)
        # ==========================================
        st.subheader("🎯 1. 이상적인 돌파 발생 구간 (65% ~ 85%)")
        st.info(f"쐐기형은 수렴 끝부분까지 꽉 채우며 밀어붙이는 성질이 있습니다. 가장 신뢰도 높은 돌파 구간은 시작점으로부터 **{ideal_start}번째 ~ {ideal_end}번째 봉** 사이입니다.")
        
        # ==========================================
        # 2. 1차 목표가 및 기계적 손절가 (방향에 따른 분기)
        # ==========================================
        st.subheader("📊 2. 1차 목표가 및 패턴 무효화(손절) 라인")
        if "하락" in wedge_type:
            st.write(f"👉 **1차 목표가:** 패턴이 시작된 최초 고점인 **{start_high:,.2f}** (100% 회귀)")
            st.write(f"🛑 **기계적 손절가:** 상방 돌파 전 마지막으로 다졌던 최저점 **{last_swing:,.2f}** 하향 이탈 시 즉시 손절 (패턴 구조 파괴)")
        else:
            st.write(f"👉 **1차 목표가:** 패턴이 시작된 최초 저점인 **{start_low:,.2f}** (100% 회귀)")
            st.write(f"🛑 **기계적 무효화:** 하방 이탈 전 마지막으로 올렸던 최고점 **{last_swing:,.2f}** 상향 돌파 시 즉시 도망 (숏 스퀴즈 위험)")

        # ==========================================
        # 3. 리테스트 방어 한계치 (트랩 경고)
        # ==========================================
        st.subheader("🛡️ 3. 리테스트(되돌림) 방어 한계치")
        st.write(f"- 돌파 시점의 좁아진 추세선 간격: **{narrowed_width:.2f}**")
        st.error(f"쐐기형은 돌파 후 다시 추세선을 확인하러 오는 리테스트 확률이 약 70%로 매우 높습니다.\n\n단, 캔들이 뚫고 나온 추세선 안쪽으로 다시 **{retest_limit:.2f} (좁아진 폭의 50%) 이상 깊게 파고들며 종가 마감**할 경우, 리테스트 실패 및 휩쏘(트랩)로 확정 짓고 관망해야 합니다.")
