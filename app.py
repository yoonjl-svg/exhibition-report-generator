"""
일민미술관 전시보고서 자동 생성 도구
Streamlit 웹 앱
"""

import streamlit as st
import os
import sys
from datetime import date

# 모듈 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reference_data as rd

from tabs import tab1_overview, tab2_theme, tab3_composition
from tabs import tab4_results, tab5_promotion, tab6_evaluation
from tabs import tab7_analysis, tab8_generate


# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="일민미술관 전시보고서 생성기",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #333;
        border-bottom: 2px solid #ddd;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 500;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────

def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        "exhibition_title": "",
        "period_start": date.today(),
        "period_end": date.today(),
        "artists": "",
        "chief_curator": "",
        "curators": "",
        "coordinators": "",
        "curatorial_team": "",
        "pr_person": "",
        "sponsors": "",
        "exhibition_days": 0,
        "total_budget_overview": "",
        "budget_exhibition": "",
        "budget_supplementary": "",
        "total_revenue_overview": "",
        "programs_overview": "",
        "staff_paid_count": "",
        "staff_volunteer_count": "",
        "visitor_count": "",
        "theme_text": "",
        "rooms": [{"name": "1전시실", "artists": ""}],
        "related_programs": [{"category": "", "title": "", "date": "", "participants": "", "note": ""}],
        "staff_main_count": "",
        "staff_main_role": "",
        "staff_volunteers_count": "",
        "staff_volunteers_role": "",
        "printed_materials": [{"type": "", "quantity": "", "note": ""}],
        "budget_total_spent": "",
        "budget_breakdown_notes": [""],
        "budget_arrow_notes": [""],
        "budget_summary": [{"category": "", "planned": "", "actual": "", "note": ""}],
        "budget_details": [{"category": "", "subcategory": "", "detail": "", "amount": "", "note": ""}],
        "revenue_visitors": "",
        "revenue_daily_average": "",
        "revenue_visitor_notes": [""],
        "revenue_ticket": "",
        "revenue_partnership": "",
        "revenue_total": "",
        "revenue_revenue_notes": [""],
        "visitor_general": 0,
        "visitor_student": 0,
        "visitor_invitation": 0,
        "visitor_artpass": 0,
        "visitor_discount": 0,
        "visitor_comp_note": "",
        "visitor_ticket_analysis": [""],
        "vtype_individual": 0,
        "vtype_art_univ": 0,
        "vtype_other_group": 0,
        "vtype_opening": 0,
        "weekly_visitors": {},
        "visitor_analysis": "",
        "promo_advertising": "",
        "promo_press_release": "",
        "promo_web_invitation": "",
        "promo_newsletter": "",
        "promo_sns": "",
        "promo_other": "",
        "press_print": [{"outlet": "", "date": "", "title": "", "note": ""}],
        "press_online": [{"outlet": "", "date": "", "title": "", "url": ""}],
        "membership_text": "",
        "eval_positive": [""],
        "eval_negative": [""],
        "eval_improvements": [""],
        "visitor_reviews": [{"category": "", "content": "", "source": ""}],
        "uploaded_images": {},
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────

st.markdown('<div class="main-header">일민미술관 전시보고서 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">전시 정보를 입력하면 보고서를 자동으로 생성합니다</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 레퍼런스 데이터 로드
# ──────────────────────────────────────────────

@st.cache_data
def load_reference_data():
    """레퍼런스 Excel을 캐시하여 로드"""
    ref_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exhibition_reference_data.xlsx")
    if not os.path.exists(ref_path):
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exhibition_reference_data.xlsx")
        if os.path.exists(alt_path):
            ref_path = alt_path
        else:
            return None
    try:
        return rd.load_reference(ref_path)
    except Exception:
        return None


# ──────────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 기본 정보",
    "📝 전시 주제",
    "🏛️ 전시 구성",
    "💰 예산/관객",
    "📢 홍보/언론",
    "📊 평가",
    "🔍 분석 인사이트",
    "⬇️ 보고서 생성"
])

tab1_overview.render(tab1)
tab2_theme.render(tab2)
tab3_composition.render(tab3)
tab4_results.render(tab4)
tab5_promotion.render(tab5)
tab6_evaluation.render(tab6)
tab7_analysis.render(tab7, load_reference_data)
tab8_generate.render(tab8)


# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📌 사용 가이드")
    st.markdown("""
    1. **기본 정보** 탭에서 전시 개요를 입력하세요
    2. **전시 주제** 탭에서 에세이를 작성하세요
    3. **전시 구성** 탭에서 전시실, 프로그램 등을 입력하세요
    4. **예산/관객** 탭에서 결과 데이터를 입력하세요
    5. **홍보/언론** 탭에서 홍보 및 언론 정보를 입력하세요
    6. **평가** 탭에서 평가와 후기를 입력하세요
    7. **보고서 생성** 탭에서 다운로드하세요
    """)

    st.divider()

    st.markdown("### ℹ️ 정보")
    st.markdown("""
    **일민미술관 전시보고서 생성기** v2.0

    기존 보고서 형식을 기반으로
    자동 생성합니다.

    차트(파이/바)는 데이터 입력 시
    자동으로 생성됩니다.
    """)
