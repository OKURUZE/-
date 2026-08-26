import streamlit as st

# 사이드바 메인 탭 이름과 아이콘 설정
st.set_page_config(page_title="트라이앵글 분석기", page_icon="📐")

st.title("📐 통합 트라이앵글 돌파 분석기")
st.write("대칭, 어센딩, 디센딩 패턴의 1차 목표가, 진성 돌파 조건, 트랩 경고를 통일된 양식으로 정밀 분석합니다.")

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
        # 직관성을 위해 입력창 이름 공통 적용
        high_price = st.number_input("시작점 고가 (상단 추세선/저항선)", value=70000.0, format="%.2f")
        low_price = st.number_input("시작점 저가 (하단 추세선/지지선)", value=66880.0, format="%.2f")
    
    submit_button = st.form_submit_button(label="패턴 분석 및 1차 목표가 계산")

if submit_button:
    initial_width = high_price - low_price
    
    if initial_width <= 0:
        st.error("⚠️ 고가가 저가보다 높아야 합니다. 입력하신 가격을 다시 확인해 주세요.")
    else:
        # 0. 3가지 패턴 공통 수학 계산 로직
        ideal_start = int(bars_to_apex * 0.65)
        ideal_end = int(bars_to_apex * 0.75)
        narrowed_width = initial_width * (1 - (breakout_bar / bars_to_apex))
        
        true_breakout_min = narrowed_width * 0.50
        true_breakout_max = narrowed_width * 1.50
        regressive_min = narrowed_width * 0.33
        regressive_max = narrowed_width * 0.50

        st.success(f"✅ 분석 완료: {pattern_type}")

        # ==========================================
        # 1. 이상적인 돌파 발생 구간 (완전 공통)
        # ==========================================
        st.subheader("🎯 1. 이상적인 돌파 발생 구간 (65% ~ 75%)")
        st.info(f"돌파 구간은 **{ideal_start}번째 ~ {ideal_end}번째 봉** 사이입니다.")
        
        # ==========================================
        # 2. 구조 분석 및 1차 목표가 (패턴별 목표가 적용)
        # ==========================================
        st.subheader("📊 2. 구조 분석 및 1차 목표가 (Target Price)")
        st.write(f"- 처음 삼각수렴 폭: **{initial_width:.2f}**")
        st.write(f"- 돌파 시점({breakout_bar}번째 봉)의 좁아진 추세선 간격: **{narrowed_width:.2f}**")
        
        if "대칭" in pattern_type:
            st.write(f"👉 **목표가:** 상향 돌파 시 `(돌파 가격 + {initial_width:.2f})`, 하향 이탈 시 `(돌파 가격 - {initial_width:.2f})`")
        elif "어센딩" in pattern_type:
            target_price = high_price + initial_width
            st.write(f"👉 **목표가:** 수평 저항선 돌파 시 **{target_price:.2f}**")
        elif "디센딩" in pattern_type:
            target_price = low_price - initial_width
            st.write(f"👉 **목표가:** 수평 지지선 이탈 시 **{target_price:.2f}**")

        # ==========================================
        # 3. 진성 돌파 캔들 조건 (완전 공통)
        # ==========================================
        st.subheader("🚀 3. 진성 돌파 캔들 요구폭 (몸통 기준)")
        st.write(f"- **최소값:** **{true_breakout_min:.2f}** 이상 (이보다 작으면 단순 노이즈 휩쏘 가능성)")
        st.write(f"- **최대값:** **{true_breakout_max:.2f}** 이하 (이보다 크면 단기 에너지 고갈에 의한 되돌림 주의)")
        
        # ==========================================
        # 4. 트랩 경고 (패턴별 치명적 구조 파괴 조건)
        # ==========================================
        st.subheader("🚨 4. 구조 파괴 휩쏘(트랩) 경고")
        if "대칭" in pattern_type:
            st.error(f"**회귀 캔들**의 몸통이 **{regressive_min:.2f} ~ {regressive_max:.2f}** 사이를 기록하며 패턴 안으로 다시 파고들면 가짜 돌파로 확정 짓습니다.")
        elif "어센딩" in pattern_type:
            st.error(f"상향 돌파 후 출현한 캔들의 **종가(Close)**가 수평 저항선인 **{high_price:.2f} 아래로 다시 파고들어 마감**되면 전형적인 불트랩(세력의 물량 넘기기)이므로 즉시 도망치세요.")
        elif "디센딩" in pattern_type:
            st.error(f"하향 이탈 후 출현한 캔들의 **종가(Close)**가 수평 지지선인 **{low_price:.2f} 위로 다시 올라와 마감**되면 전형적인 베어트랩(숏 스퀴즈 유도)이므로 숏 포지션은 즉시 도망치세요.")
