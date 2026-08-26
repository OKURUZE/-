import streamlit as st

# 사이드바 메인 탭 이름과 아이콘 설정
st.set_page_config(page_title="통합 수렴 분석기", page_icon="📐")

st.title("📐 통합 수렴 분석기")
st.write("수렴 패턴의 1차 목표가, 진성 돌파 조건, 트랩 경고를 직관적이고 빠르게 정밀 분석합니다.")

with st.form("advanced_triangle_form"):
    col1, col2 = st.columns(2)
    with col1:
        bars_to_apex = st.number_input("시작점 ~ 꼭짓점 총 봉수", min_value=10, value=63)
        default_breakout = int(bars_to_apex * 0.7)
        breakout_bar = st.number_input("실제/예상 돌파 발생 캔들 위치", min_value=1, max_value=int(bars_to_apex), value=default_breakout)
    
    with col2:
        high_price = st.number_input("시작점 고가 (상단 추세선/저항선)", value=70000.0, format="%.2f")
        low_price = st.number_input("시작점 저가 (하단 추세선/지지선)", value=66880.0, format="%.2f")
    
    submit_button = st.form_submit_button(label="수렴 분석 및 목표가 계산")

if submit_button:
    initial_width = high_price - low_price
    
    if initial_width <= 0:
        st.error("⚠️ 고가가 저가보다 높아야 합니다. 입력하신 가격을 다시 확인해 주세요.")
    else:
        # 공통 수학 계산 로직
        ideal_start = int(bars_to_apex * 0.65)
        ideal_end = int(bars_to_apex * 0.75)
        narrowed_width = initial_width * (1 - (breakout_bar / bars_to_apex))
        
        true_breakout_min = narrowed_width * 0.50
        true_breakout_max = narrowed_width * 1.50
        regressive_min = narrowed_width * 0.33
        regressive_max = narrowed_width * 0.50

        st.success("✅ 분석 완료")

        # ==========================================
        # 1. 이상적인 돌파 발생 구간
        # ==========================================
        st.subheader("🎯 1. 이상적인 돌파 발생 구간 (65% ~ 75%)")
        st.info(f"돌파 구간은 **{ideal_start}번째 ~ {ideal_end}번째 봉** 사이입니다.")
        
        # ==========================================
        # 2. 1차 목표가 (불필요한 중간 계산 과정 삭제)
        # ==========================================
        st.subheader("📊 2. 1차 목표가 (Target Price)")
        st.write(f"👉 **목표가:** 상향 돌파 시 `(돌파 가격 + {initial_width:.2f})`, 하향 이탈 시 `(돌파 가격 - {initial_width:.2f})`")

        # ==========================================
        # 3. 진성 돌파 캔들 조건
        # ==========================================
        st.subheader("🚀 3. 진성 돌파 캔들 요구폭 (몸통 기준)")
        st.write(f"- **최소값:** **{true_breakout_min:.2f}** 이상 (이보다 작으면 단순 노이즈 휩쏘 가능성)")
        st.write(f"- **최대값:** **{true_breakout_max:.2f}** 이하 (이보다 크면 단기 에너지 고갈에 의한 되돌림 주의)")
        
        # ==========================================
        # 4. 트랩 경고
        # ==========================================
        st.subheader("🚨 4. 구조 파괴 휩쏘(트랩) 경고")
        st.error(f"돌파 직후 출현하는 **회귀 캔들(빨간색)**의 몸통이 좁아진 폭의 33~50%인 **{regressive_min:.2f} ~ {regressive_max:.2f}** 사이를 기록하며 패턴 안으로 다시 파고들면 가짜 돌파로 확정 짓습니다.")
