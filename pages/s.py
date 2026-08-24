import streamlit as st

st.title("📐 통합 트라이앵글 돌파 분석기")
st.write("대칭, 어센딩, 디센딩 트라이앵글 패턴을 선택하여 돌파 신뢰도와 목표가를 정밀하게 분석합니다.")

# 💡 패턴 선택 콤보박스 (폼 바깥에 두어 직관적으로 선택 가능하게 함)
pattern_type = st.selectbox(
    "🔍 분석할 패턴을 선택하세요",
    ("대칭 삼각수렴 (Symmetrical Triangle)", 
     "어센딩 트라이앵글 (Ascending Triangle - 상승형)", 
     "디센딩 트라이앵글 (Descending Triangle - 하락형)")
)

with st.form("advanced_triangle_form"):
    col1, col2 = st.columns(2)
    with col1:
        bars_to_apex = st.number_input("시작점 ~ 꼭짓점 총 봉수", min_value=10, value=63)
        default_breakout = int(bars_to_apex * 0.7)
        breakout_bar = st.number_input("실제/예상 돌파 발생 캔들 위치", min_value=1, max_value=int(bars_to_apex), value=default_breakout)
    
    with col2:
        high_price = st.number_input("시작점 고가 (수평 저항선)", value=70000.0, format="%.2f")
        low_price = st.number_input("시작점 저가 (수평 지지선)", value=66880.0, format="%.2f")
    
    submit_button = st.form_submit_button(label="패턴 분석 및 목표가 계산")

if submit_button:
    initial_width = high_price - low_price
    
    if initial_width <= 0:
        st.error("⚠️ 고가가 저가보다 높아야 합니다. 입력하신 가격을 다시 확인해 주세요.")
    else:
        # 공통 계산: 돌파 타점 범위 및 좁아진 간격
        ideal_start = int(bars_to_apex * 0.65)
        ideal_end = int(bars_to_apex * 0.75)
        narrowed_width = initial_width * (1 - (breakout_bar / bars_to_apex))
        
        st.success(f"✅ 분석 완료: {pattern_type}")

        # 1, 2번 공통 출력
        st.subheader("🎯 1. 이상적인 돌파 발생 구간 (65% ~ 75%)")
        st.info(f"이 패턴의 가장 신뢰도 높은 돌파 구간은 시작점으로부터 **{ideal_start}번째 ~ {ideal_end}번째 봉** 사이입니다.")
        
        st.subheader(f"📊 2. 입력하신 {breakout_bar}번째 봉 기준 구조 분석")
        st.write(f"- 자동 계산된 처음 삼각수렴 폭: **{initial_width:.2f}**")
        st.write(f"- 해당 시점의 좁아진 추세선 간격: **{narrowed_width:.2f}**")
        
        # 💡 3, 4번 패턴별 분기 출력 (선택한 패턴에 따라 다른 결과 제공)
        if "대칭" in pattern_type:
            true_breakout_min = narrowed_width * 0.50
            true_breakout_max = narrowed_width * 1.50
            regressive_min = narrowed_width * 0.33
            regressive_max = narrowed_width * 0.50
            
            st.subheader("🚀 3. 진성 돌파 캔들 (몸통 기준)")
            st.write(f"- **최소값:** **{true_breakout_min:.2f}** 이상 (이보다 작으면 노이즈 휩쏘 가능성)")
            st.write(f"- **최대값:** **{true_breakout_max:.2f}** 이하 (이보다 크면 오버슈팅으로 단기 되돌림 주의)")
            
            st.subheader("🚨 4. 구조 파괴 휩쏘 경고")
            st.error(f"돌파 직후 출현하는 회귀 캔들이 **{regressive_min:.2f} ~ {regressive_max:.2f}** 폭으로 패턴 안으로 파고들면 가짜 돌파로 간주합니다.")
            
        elif "어센딩" in pattern_type:
            target_price = high_price + initial_width
            
            st.subheader("🚀 3. 어센딩 돌파 목표가 (Target Price)")
            st.write(f"수평 저항선인 **{high_price:.2f}** 을(를) 강력하게 상향 돌파할 경우, 1차 목표가는 폭만큼 상승한 **{target_price:.2f}** 입니다.")
            
            st.subheader("🚨 4. 불트랩 (가짜 상승 돌파) 경고")
            st.error(f"돌파 후 출현한 음봉의 **종가(Close)**가 수평 저항선인 **{high_price:.2f} 아래로 다시 파고들어 마감**되면 전형적인 불트랩(세력의 물량 넘기기)이므로 즉시 관망 또는 손절로 대응하세요.")
            
        elif "디센딩" in pattern_type:
            target_price = low_price - initial_width
            
            st.subheader("🚀 3. 디센딩 이탈 목표가 (Target Price)")
            st.write(f"수평 지지선인 **{low_price:.2f}** 을(를) 강력하게 하향 이탈할 경우, 1차 목표가는 폭만큼 하락한 **{target_price:.2f}** 입니다.")
            
            st.subheader("🚨 4. 베어트랩 (가짜 하락 이탈) 경고")
            st.error(f"하향 이탈 후 출현한 양봉의 **종가(Close)**가 수평 지지선인 **{low_price:.2f} 위로 다시 올라와 마감**되면 전형적인 베어트랩(숏 스퀴즈 유도)이므로 숏 포지션은 즉시 도망쳐야 합니다.")
