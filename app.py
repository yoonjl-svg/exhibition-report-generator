"""
일민미술관 전시보고서 자동 생성 도구
Streamlit 웹 앱
"""

import streamlit as st
import os
import sys
import tempfile
import json
from datetime import datetime, date

# 모듈 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_generator import generate_report
from chart_generator import (
    create_visitor_pie_chart,
    create_weekly_visitors_chart,
    create_budget_comparison_chart,
)
import reference_data as rd
import analysis_engine as ae
import pandas as pd

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
        # 상위 폴더에서도 검색
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
# 동적 리스트 관리 헬퍼 함수
# ──────────────────────────────────────────────

def add_item(key, template):
    """리스트에 새 항목 추가"""
    st.session_state[key].append(template.copy())


def remove_item(key, index):
    """리스트에서 항목 제거"""
    if len(st.session_state[key]) > 1:
        st.session_state[key].pop(index)


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


# ══════════════════════════════════════════════
# 탭 1: 기본 정보
# ══════════════════════════════════════════════

with tab1:
    st.markdown('<div class="section-header">Ⅰ. 전시 개요</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.exhibition_title = st.text_input(
            "전시 제목 *", value=st.session_state.exhibition_title,
            placeholder="예: 포에버리즘: 우리를 세상의 끝으로"
        )

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            st.session_state.period_start = st.date_input(
                "전시 시작일 *", value=st.session_state.period_start
            )
        with date_col2:
            st.session_state.period_end = st.date_input(
                "전시 종료일 *", value=st.session_state.period_end
            )

        st.session_state.artists = st.text_area(
            "참여 작가 (쉼표로 구분)",
            value=st.session_state.artists,
            placeholder="예: 작가A, 작가B, 작가C",
            height=80
        )

    with col2:
        st.session_state.chief_curator = st.text_input(
            "책임기획", value=st.session_state.chief_curator
        )
        st.session_state.curators = st.text_input(
            "기획", value=st.session_state.curators
        )
        st.session_state.coordinators = st.text_input(
            "진행", value=st.session_state.coordinators
        )
        st.session_state.curatorial_team = st.text_input(
            "학예팀", value=st.session_state.curatorial_team
        )

    col3, col4 = st.columns(2)
    with col3:
        st.session_state.pr_person = st.text_input(
            "홍보", value=st.session_state.pr_person
        )
        st.session_state.sponsors = st.text_input(
            "후원", value=st.session_state.sponsors,
            placeholder="예: 한국문화예술위원회"
        )
    with col4:
        st.session_state.exhibition_days = st.number_input(
            "전시 일수", min_value=0, value=st.session_state.exhibition_days,
            placeholder="예: 52"
        )
        st.session_state.total_budget_overview = st.text_input(
            "총 사용 예산", value=st.session_state.total_budget_overview,
            placeholder="예: 약 1억 4천 2백만 원(142,438,012원)"
        )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.session_state.budget_exhibition = st.text_input(
            "전시 사용 예산", value=st.session_state.budget_exhibition,
            placeholder="예: 130,773,012원"
        )
    with col_b2:
        st.session_state.budget_supplementary = st.text_input(
            "부대 사용 예산", value=st.session_state.budget_supplementary,
            placeholder="예: 11,665,000원"
        )

    col5, col6, col7 = st.columns(3)
    with col5:
        st.session_state.total_revenue_overview = st.text_input(
            "총수입", value=st.session_state.total_revenue_overview,
            placeholder="예: 12,000,000원"
        )
    with col6:
        st.session_state.staff_paid_count = st.text_input(
            "유급 스태프 수", value=st.session_state.staff_paid_count,
            placeholder="예: 10명"
        )
    with col7:
        st.session_state.staff_volunteer_count = st.text_input(
            "봉사자 수", value=st.session_state.staff_volunteer_count,
            placeholder="예: 12명"
        )

    # 운영 인력 자동 산출
    auto_staff = ""
    paid_str = st.session_state.staff_paid_count.replace("명", "").replace(",", "").strip()
    vol_str = st.session_state.staff_volunteer_count.replace("명", "").replace(",", "").strip()
    try:
        paid_num = int(paid_str) if paid_str else 0
        vol_num = int(vol_str) if vol_str else 0
        if paid_num > 0 or vol_num > 0:
            parts = []
            if paid_num > 0:
                parts.append(f"스태프 {paid_num}명")
            if vol_num > 0:
                parts.append(f"봉사자 {vol_num}명")
            auto_staff = ", ".join(parts)
    except ValueError:
        auto_staff = ""
    if auto_staff:
        st.info(f"📌 운영 인력 (자동 산출): {auto_staff}")

    col8, col9 = st.columns(2)
    with col8:
        st.session_state.visitor_count = st.text_input(
            "관객 수", value=st.session_state.visitor_count,
            placeholder="예: 7,009명"
        )
    with col9:
        # 일평균 관객수 자동 산출
        auto_daily = ""
        visitor_str = st.session_state.visitor_count.replace("명", "").replace(",", "").strip()
        try:
            visitor_num = int(visitor_str) if visitor_str else 0
            days_num = st.session_state.exhibition_days
            if visitor_num > 0 and days_num > 0:
                auto_daily = f"{visitor_num // days_num}명"
        except ValueError:
            auto_daily = ""
        st.text_input("일평균 관객수 (자동 산출)", value=auto_daily, disabled=True)

    st.session_state.programs_overview = st.text_area(
        "프로그램 (개요)",
        value=st.session_state.programs_overview,
        placeholder="예: 아티스트 토크 2회, 큐레이터 투어 3회, 워크숍 1회",
        height=80
    )

    st.markdown("**포스터 이미지** (목차 페이지에 표시됨)")
    poster_file = st.file_uploader("포스터 이미지 업로드", type=["png", "jpg", "jpeg"], key="poster_upload")
    if poster_file:
        st.session_state["poster_file"] = poster_file
        st.image(poster_file, width=200, caption="포스터 미리보기")


# ══════════════════════════════════════════════
# 탭 2: 전시 주제
# ══════════════════════════════════════════════

with tab2:
    st.markdown('<div class="section-header">Ⅱ. 전시 주제와 내용</div>', unsafe_allow_html=True)

    st.info("전시에 대한 설명 에세이를 작성해주세요. 문단 구분은 빈 줄로 합니다.")

    st.session_state.theme_text = st.text_area(
        "전시 에세이",
        value=st.session_state.theme_text,
        height=400,
        placeholder="전시의 주제, 배경, 의의 등을 자유롭게 작성해주세요..."
    )


# ══════════════════════════════════════════════
# 탭 3: 전시 구성
# ══════════════════════════════════════════════

with tab3:
    st.markdown('<div class="section-header">Ⅲ. 전시 구성</div>', unsafe_allow_html=True)

    # ── 전시실 ──
    st.subheader("1. 전시 (전시실별 정보)")

    for i, room in enumerate(st.session_state.rooms):
        with st.expander(f"📌 {room.get('name', f'전시실 {i+1}')}", expanded=(i == 0)):
            col_r1, col_r2 = st.columns([1, 2])
            with col_r1:
                st.session_state.rooms[i]["name"] = st.text_input(
                    "전시실 이름", value=room.get("name", ""),
                    key=f"room_name_{i}"
                )
            with col_r2:
                st.session_state.rooms[i]["artists"] = st.text_input(
                    "참여 작가 (쉼표로 구분)", value=room.get("artists", ""),
                    key=f"room_artists_{i}"
                )

            col_img1, col_img2 = st.columns(2)
            with col_img1:
                floor_plan = st.file_uploader(
                    "도면 이미지", type=["png", "jpg", "jpeg"],
                    key=f"floor_plan_{i}"
                )
                if floor_plan:
                    st.session_state.rooms[i]["floor_plan_file"] = floor_plan

            with col_img2:
                photos = st.file_uploader(
                    "전경 사진", type=["png", "jpg", "jpeg"],
                    key=f"room_photos_{i}", accept_multiple_files=True
                )
                if photos:
                    st.session_state.rooms[i]["photo_files"] = photos

            if i > 0:
                if st.button(f"🗑️ 이 전시실 삭제", key=f"del_room_{i}"):
                    remove_item("rooms", i)
                    st.rerun()

    if st.button("➕ 전시실 추가"):
        n = len(st.session_state.rooms) + 1
        add_item("rooms", {"name": f"{n}전시실", "artists": ""})
        st.rerun()

    st.divider()

    # ── 연계 프로그램 ──
    st.subheader("2. 전시 연계 프로그램")

    for i, prog in enumerate(st.session_state.related_programs):
        cols = st.columns([2, 3, 2, 1.5, 2.5, 0.5])
        with cols[0]:
            st.session_state.related_programs[i]["category"] = st.text_input(
                "구분", value=prog.get("category", ""), key=f"prog_cat_{i}",
                placeholder="예: 아티스트 토크"
            )
        with cols[1]:
            st.session_state.related_programs[i]["title"] = st.text_input(
                "제목", value=prog.get("title", ""), key=f"prog_title_{i}"
            )
        with cols[2]:
            # 일자: date_input 사용
            prog_date_val = prog.get("date", "")
            if isinstance(prog_date_val, str) and prog_date_val:
                try:
                    from datetime import datetime as dt
                    prog_date_val = dt.strptime(prog_date_val, "%Y.%m.%d").date()
                except ValueError:
                    prog_date_val = date.today()
            elif not prog_date_val:
                prog_date_val = date.today()
            selected_date = st.date_input("일자", value=prog_date_val, key=f"prog_date_{i}")
            st.session_state.related_programs[i]["date"] = selected_date.strftime("%Y.%m.%d")
        with cols[3]:
            st.session_state.related_programs[i]["participants"] = st.text_input(
                "참여 인원", value=prog.get("participants", ""), key=f"prog_part_{i}"
            )
        with cols[4]:
            st.session_state.related_programs[i]["note"] = st.text_input(
                "비고", value=prog.get("note", ""), key=f"prog_note_{i}"
            )
        with cols[5]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_prog_{i}"):
                remove_item("related_programs", i)
                st.rerun()

    if st.button("➕ 프로그램 추가"):
        add_item("related_programs", {"category": "", "title": "", "date": "", "participants": "", "note": ""})
        st.rerun()

    # 프로그램 사진
    program_photos = st.file_uploader(
        "프로그램 운영 사진", type=["png", "jpg", "jpeg"],
        accept_multiple_files=True, key="program_photos"
    )

    st.divider()

    # ── 운영인력 ──
    st.subheader("3. 전시 운영 인력")

    st.markdown("**스태프**")
    col_s1a, col_s1b = st.columns(2)
    with col_s1a:
        st.session_state.staff_main_count = st.text_input(
            "스태프 인원", value=st.session_state.staff_main_count,
            placeholder="예: 총 10명"
        )
    with col_s1b:
        st.session_state.staff_main_role = st.text_input(
            "스태프 역할 및 활동", value=st.session_state.staff_main_role,
            placeholder="예: 전시 안내, 작품 모니터링, 관객 응대"
        )

    st.markdown("**봉사단**")
    col_s2a, col_s2b = st.columns(2)
    with col_s2a:
        st.session_state.staff_volunteers_count = st.text_input(
            "봉사단 인원", value=st.session_state.staff_volunteers_count,
            placeholder="예: 총 12명 (제17기)"
        )
    with col_s2b:
        st.session_state.staff_volunteers_role = st.text_input(
            "봉사단 역할 및 활동", value=st.session_state.staff_volunteers_role,
            placeholder="예: 전시 안내 보조, 교육 프로그램 지원"
        )

    st.divider()

    # ── 인쇄물 ──
    st.subheader("4. 인쇄물 및 굿즈")

    for i, mat in enumerate(st.session_state.printed_materials):
        cols = st.columns([3, 2, 3, 0.5])
        with cols[0]:
            st.session_state.printed_materials[i]["type"] = st.text_input(
                "종류", value=mat.get("type", ""), key=f"mat_type_{i}",
                placeholder="예: 리플렛, 포스터, 초청장"
            )
        with cols[1]:
            st.session_state.printed_materials[i]["quantity"] = st.text_input(
                "제작 수량", value=mat.get("quantity", ""), key=f"mat_qty_{i}",
                placeholder="예: 5,000부"
            )
        with cols[2]:
            st.session_state.printed_materials[i]["note"] = st.text_input(
                "비고", value=mat.get("note", ""), key=f"mat_note_{i}"
            )
        with cols[3]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_mat_{i}"):
                remove_item("printed_materials", i)
                st.rerun()

    if st.button("➕ 인쇄물 추가"):
        add_item("printed_materials", {"type": "", "quantity": "", "note": ""})
        st.rerun()

    # 인쇄물 및 굿즈 이미지
    material_photos = st.file_uploader(
        "인쇄물 및 굿즈 이미지", type=["png", "jpg", "jpeg"],
        accept_multiple_files=True, key="material_photos"
    )


# ══════════════════════════════════════════════
# 탭 4: 예산/관객
# ══════════════════════════════════════════════

with tab4:
    st.markdown('<div class="section-header">Ⅳ. 전시 결과</div>', unsafe_allow_html=True)

    # ── 예산 ──
    st.subheader("1. 예산 및 지출")

    st.session_state.budget_total_spent = st.text_input(
        "지출 총액", value=st.session_state.budget_total_spent,
        placeholder="예: 약 1억 4천 2백만 원(142,438,012원)"
    )

    st.markdown("**지출 구성 설명** (- 불릿으로 표시됨)")
    for i, note in enumerate(st.session_state.budget_breakdown_notes):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.budget_breakdown_notes[i] = st.text_input(
                f"구성 {i+1}", value=note, key=f"bdn_{i}",
                label_visibility="collapsed",
                placeholder="예: 지출 구성: 전시비 130,773,012원 / 부대비 11,665,000원"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_bdn_{i}"):
                st.session_state.budget_breakdown_notes.pop(i)
                st.rerun()
    if st.button("➕ 지출 구성 추가"):
        st.session_state.budget_breakdown_notes.append("")
        st.rerun()

    st.markdown("**계획 대비 집행 요약**")
    for i, item in enumerate(st.session_state.budget_summary):
        cols = st.columns([2, 3, 3, 3, 0.5])
        with cols[0]:
            st.session_state.budget_summary[i]["category"] = st.text_input(
                "구분", value=item.get("category", ""), key=f"bs_cat_{i}",
                placeholder="예: 전시비"
            )
        with cols[1]:
            st.session_state.budget_summary[i]["planned"] = st.text_input(
                "계획 (원)", value=item.get("planned", ""), key=f"bs_plan_{i}"
            )
        with cols[2]:
            st.session_state.budget_summary[i]["actual"] = st.text_input(
                "집행 (원)", value=item.get("actual", ""), key=f"bs_act_{i}"
            )
        with cols[3]:
            st.session_state.budget_summary[i]["note"] = st.text_input(
                "비고", value=item.get("note", ""), key=f"bs_note_{i}"
            )
        with cols[4]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_bs_{i}"):
                remove_item("budget_summary", i)
                st.rerun()

    if st.button("➕ 예산 항목 추가 (요약)"):
        add_item("budget_summary", {"category": "", "planned": "", "actual": "", "note": ""})
        st.rerun()

    st.markdown("**상세 예산 집행 내역**")
    for i, item in enumerate(st.session_state.budget_details):
        cols = st.columns([2, 2, 3, 2.5, 2, 0.5])
        with cols[0]:
            st.session_state.budget_details[i]["category"] = st.text_input(
                "사업", value=item.get("category", ""), key=f"bd_cat_{i}",
                placeholder="예: 전시비"
            )
        with cols[1]:
            st.session_state.budget_details[i]["subcategory"] = st.text_input(
                "세목", value=item.get("subcategory", ""), key=f"bd_sub_{i}",
                placeholder="예: 작품 제작비"
            )
        with cols[2]:
            st.session_state.budget_details[i]["detail"] = st.text_input(
                "내역", value=item.get("detail", ""), key=f"bd_detail_{i}",
                placeholder="예: 작가 3인 제작 지원"
            )
        with cols[3]:
            st.session_state.budget_details[i]["amount"] = st.text_input(
                "금액 (원)", value=item.get("amount", ""), key=f"bd_amt_{i}"
            )
        with cols[4]:
            st.session_state.budget_details[i]["note"] = st.text_input(
                "비고", value=item.get("note", ""), key=f"bd_note_{i}"
            )
        with cols[5]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_bd_{i}"):
                remove_item("budget_details", i)
                st.rerun()

    if st.button("➕ 예산 항목 추가 (상세)"):
        add_item("budget_details", {"category": "", "subcategory": "", "detail": "", "amount": "", "note": ""})
        st.rerun()

    st.markdown("**예산 주석** (→ 파란색 화살표로 표시됨)")
    for i, note in enumerate(st.session_state.budget_arrow_notes):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.budget_arrow_notes[i] = st.text_input(
                f"주석 {i+1}", value=note, key=f"ban_{i}",
                label_visibility="collapsed",
                placeholder="예: 전시 예산의 104.2% 사용: 작가 설치비 추가 지출"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_ban_{i}"):
                st.session_state.budget_arrow_notes.pop(i)
                st.rerun()
    if st.button("➕ 예산 주석 추가"):
        st.session_state.budget_arrow_notes.append("")
        st.rerun()

    st.divider()

    # ── 수익 ──
    st.subheader("2. 총 관객 수 및 수익 결산")

    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        st.session_state.revenue_visitors = st.text_input(
            "총 관객 수", value=st.session_state.revenue_visitors, placeholder="예: 7,009명"
        )
        st.session_state.revenue_daily_average = st.text_input(
            "일평균 관객", value=st.session_state.revenue_daily_average, placeholder="예: 135명"
        )
        st.session_state.revenue_ticket = st.text_input(
            "입장 수입", value=st.session_state.revenue_ticket, placeholder="예: 42,574,000원"
        )
    with col_rev2:
        st.session_state.revenue_total = st.text_input(
            "총 수입", value=st.session_state.revenue_total, placeholder="예: 49,574,000원"
        )
        st.session_state.revenue_partnership = st.text_input(
            "제휴 수입", value=st.session_state.revenue_partnership
        )

    st.markdown("**관객 수 관련 메모** (- 불릿으로 표시됨)")
    for i, note in enumerate(st.session_state.revenue_visitor_notes):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.revenue_visitor_notes[i] = st.text_input(
                f"메모 {i+1}", value=note, key=f"rvn_{i}",
                label_visibility="collapsed",
                placeholder="예: 짧은 전시 기간(52일) 대비 양호한 관객 수 기록"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_rvn_{i}"):
                st.session_state.revenue_visitor_notes.pop(i)
                st.rerun()
    if st.button("➕ 관객 메모 추가"):
        st.session_state.revenue_visitor_notes.append("")
        st.rerun()

    st.markdown("**수입 관련 메모** (- 불릿으로 표시됨)")
    for i, note in enumerate(st.session_state.revenue_revenue_notes):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.revenue_revenue_notes[i] = st.text_input(
                f"수입 메모 {i+1}", value=note, key=f"rrn_{i}",
                label_visibility="collapsed",
                placeholder="예: 제휴 수입은 전년 대비 15% 증가"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_rrn_{i}"):
                st.session_state.revenue_revenue_notes.pop(i)
                st.rerun()
    if st.button("➕ 수입 메모 추가"):
        st.session_state.revenue_revenue_notes.append("")
        st.rerun()

    st.divider()

    # ── 관객 구성 ──
    st.subheader("3. 관객 구성")

    st.session_state.visitor_comp_note = st.text_input(
        "관객 구성 주석 (※ 표시됨)", value=st.session_state.visitor_comp_note,
        placeholder="예: 티켓 권종 기준으로 작성"
    )

    st.markdown("**입장권별 관객 수**")
    col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
    with col_v1:
        st.session_state.visitor_general = st.number_input("일반 (명)", min_value=0, value=st.session_state.visitor_general, key="v_general")
    with col_v2:
        st.session_state.visitor_student = st.number_input("학생 (명)", min_value=0, value=st.session_state.visitor_student, key="v_student")
    with col_v3:
        st.session_state.visitor_invitation = st.number_input("초대권 (명)", min_value=0, value=st.session_state.visitor_invitation, key="v_invitation")
    with col_v4:
        st.session_state.visitor_artpass = st.number_input("예술인패스 (명)", min_value=0, value=st.session_state.visitor_artpass, key="v_artpass")
    with col_v5:
        st.session_state.visitor_discount = st.number_input("기타 할인 (명)", min_value=0, value=st.session_state.visitor_discount, key="v_discount")

    # 파이차트 미리보기
    ticket_data = {}
    if st.session_state.visitor_general > 0:
        ticket_data["일반"] = st.session_state.visitor_general
    if st.session_state.visitor_student > 0:
        ticket_data["학생"] = st.session_state.visitor_student
    if st.session_state.visitor_invitation > 0:
        ticket_data["초대권"] = st.session_state.visitor_invitation
    if st.session_state.visitor_artpass > 0:
        ticket_data["예술인패스"] = st.session_state.visitor_artpass
    if st.session_state.visitor_discount > 0:
        ticket_data["기타 할인"] = st.session_state.visitor_discount

    if ticket_data:
        chart_path = create_visitor_pie_chart(ticket_data, title="입장권별 관객 구성")
        st.image(chart_path, width=400)
        os.remove(chart_path)

    st.markdown("**관객 분석 불릿** (굵은 텍스트, → 화살표, - 하위 불릿 혼합)")
    st.info("● 일반 텍스트 → '→'로 시작하면 파란 화살표 → '-'로 시작하면 하위 불릿")
    for i, item in enumerate(st.session_state.visitor_ticket_analysis):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.visitor_ticket_analysis[i] = st.text_input(
                f"분석 {i+1}", value=item, key=f"vta_{i}",
                label_visibility="collapsed",
                placeholder="예: → 예술인패스 관객 대상 특화 프로그램 기획 검토 필요"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_vta_{i}"):
                st.session_state.visitor_ticket_analysis.pop(i)
                st.rerun()
    if st.button("➕ 분석 불릿 추가"):
        st.session_state.visitor_ticket_analysis.append("")
        st.rerun()

    st.markdown("**유형별 관객 수**")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        st.session_state.vtype_individual = st.number_input("개인 (명)", min_value=0, value=st.session_state.vtype_individual, key="vt_ind")
    with col_t2:
        st.session_state.vtype_art_univ = st.number_input("미술대학 단체 (명)", min_value=0, value=st.session_state.vtype_art_univ, key="vt_art")
    with col_t3:
        st.session_state.vtype_other_group = st.number_input("기타 단체 (명)", min_value=0, value=st.session_state.vtype_other_group, key="vt_grp")
    with col_t4:
        st.session_state.vtype_opening = st.number_input("오프닝 리셉션 (명)", min_value=0, value=st.session_state.vtype_opening, key="vt_open")

    st.markdown("**주별 관객 수**")
    st.info("전시 기간에 해당하는 주의 관객 수를 입력하세요.")

    week_cols = st.columns(6)
    week_names = [f"{i}주" for i in range(1, 13)]

    for i, week in enumerate(week_names):
        col_idx = i % 6
        with week_cols[col_idx]:
            val = st.number_input(
                week, min_value=0,
                value=st.session_state.weekly_visitors.get(week, 0),
                key=f"week_{i}"
            )
            if val > 0:
                st.session_state.weekly_visitors[week] = val
            elif week in st.session_state.weekly_visitors:
                del st.session_state.weekly_visitors[week]

    # 주별 바 차트 미리보기
    if st.session_state.weekly_visitors:
        from chart_generator import create_weekly_visitors_chart
        chart_path = create_weekly_visitors_chart(st.session_state.weekly_visitors)
        st.image(chart_path, width=600)
        os.remove(chart_path)

    st.session_state.visitor_analysis = st.text_area(
        "관객 분석 코멘트",
        value=st.session_state.visitor_analysis,
        height=100,
        placeholder="예: 개인 관객이 전체의 80%를 차지하며..."
    )


# ══════════════════════════════════════════════
# 탭 5: 홍보/언론
# ══════════════════════════════════════════════

with tab5:
    st.markdown('<div class="section-header">Ⅴ. 홍보 방식 및 언론 보도</div>', unsafe_allow_html=True)

    # ── 홍보 방식 ──
    st.subheader("1. 홍보 방식")

    st.session_state.promo_advertising = st.text_area(
        "광고", value=st.session_state.promo_advertising, height=80,
        placeholder="예: 서울 주요 지하철역 포스터 게시, 주간지 광고 게재"
    )
    st.session_state.promo_press_release = st.text_area(
        "보도자료", value=st.session_state.promo_press_release, height=80
    )
    st.session_state.promo_web_invitation = st.text_area(
        "웹 초청장", value=st.session_state.promo_web_invitation, height=80
    )
    st.session_state.promo_newsletter = st.text_area(
        "뉴스레터", value=st.session_state.promo_newsletter, height=80
    )
    st.session_state.promo_sns = st.text_area(
        "SNS", value=st.session_state.promo_sns, height=80,
        placeholder="예: 인스타그램 게시물 30회, 페이스북 게시물 15회"
    )
    st.session_state.promo_other = st.text_area(
        "그 외", value=st.session_state.promo_other, height=80
    )

    st.divider()

    # ── 언론보도 ──
    st.subheader("2. 언론보도 리스트")

    st.markdown("**일간지 및 월간지**")
    for i, item in enumerate(st.session_state.press_print):
        cols = st.columns([2, 2, 4, 2, 0.5])
        with cols[0]:
            st.session_state.press_print[i]["outlet"] = st.text_input(
                "매체명", value=item.get("outlet", ""), key=f"pp_out_{i}"
            )
        with cols[1]:
            st.session_state.press_print[i]["date"] = st.text_input(
                "일자", value=item.get("date", ""), key=f"pp_date_{i}"
            )
        with cols[2]:
            st.session_state.press_print[i]["title"] = st.text_input(
                "제목", value=item.get("title", ""), key=f"pp_title_{i}"
            )
        with cols[3]:
            st.session_state.press_print[i]["note"] = st.text_input(
                "비고", value=item.get("note", ""), key=f"pp_note_{i}"
            )
        with cols[4]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_pp_{i}"):
                remove_item("press_print", i)
                st.rerun()

    if st.button("➕ 일간지/월간지 추가"):
        add_item("press_print", {"outlet": "", "date": "", "title": "", "note": ""})
        st.rerun()

    st.markdown("**온라인 매체**")
    for i, item in enumerate(st.session_state.press_online):
        cols = st.columns([2, 2, 3, 3, 0.5])
        with cols[0]:
            st.session_state.press_online[i]["outlet"] = st.text_input(
                "매체명", value=item.get("outlet", ""), key=f"po_out_{i}"
            )
        with cols[1]:
            st.session_state.press_online[i]["date"] = st.text_input(
                "일자", value=item.get("date", ""), key=f"po_date_{i}"
            )
        with cols[2]:
            st.session_state.press_online[i]["title"] = st.text_input(
                "제목", value=item.get("title", ""), key=f"po_title_{i}"
            )
        with cols[3]:
            st.session_state.press_online[i]["url"] = st.text_input(
                "URL", value=item.get("url", ""), key=f"po_url_{i}"
            )
        with cols[4]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_po_{i}"):
                remove_item("press_online", i)
                st.rerun()

    if st.button("➕ 온라인 매체 추가"):
        add_item("press_online", {"outlet": "", "date": "", "title": "", "url": ""})
        st.rerun()

    st.divider()

    # ── 멤버십 ──
    st.subheader("3. 멤버십 커뮤니케이션")
    st.session_state.membership_text = st.text_area(
        "멤버십 관련 내용", value=st.session_state.membership_text, height=100
    )


# ══════════════════════════════════════════════
# 탭 6: 평가
# ══════════════════════════════════════════════

with tab6:
    st.markdown('<div class="section-header">Ⅵ. 평가 및 개선 방안</div>', unsafe_allow_html=True)

    # ── 긍정 평가 ──
    st.subheader("1. 평가")

    st.markdown("**긍정 평가**")
    for i, item in enumerate(st.session_state.eval_positive):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.eval_positive[i] = st.text_input(
                f"항목 {i+1}", value=item, key=f"eval_pos_{i}",
                label_visibility="collapsed",
                placeholder="긍정적인 평가 항목을 입력하세요"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_eval_pos_{i}"):
                st.session_state.eval_positive.pop(i)
                st.rerun()

    if st.button("➕ 긍정 평가 추가"):
        st.session_state.eval_positive.append("")
        st.rerun()

    st.markdown("**부정 평가**")
    for i, item in enumerate(st.session_state.eval_negative):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.eval_negative[i] = st.text_input(
                f"항목 {i+1}", value=item, key=f"eval_neg_{i}",
                label_visibility="collapsed",
                placeholder="부정적인 평가 항목을 입력하세요"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_eval_neg_{i}"):
                st.session_state.eval_negative.pop(i)
                st.rerun()

    if st.button("➕ 부정 평가 추가"):
        st.session_state.eval_negative.append("")
        st.rerun()

    st.markdown("**개선 방안**")
    for i, item in enumerate(st.session_state.eval_improvements):
        cols = st.columns([10, 1])
        with cols[0]:
            st.session_state.eval_improvements[i] = st.text_input(
                f"항목 {i+1}", value=item, key=f"eval_imp_{i}",
                label_visibility="collapsed",
                placeholder="개선이 필요한 사항을 입력하세요"
            )
        with cols[1]:
            if i > 0 and st.button("🗑️", key=f"del_eval_imp_{i}"):
                st.session_state.eval_improvements.pop(i)
                st.rerun()

    if st.button("➕ 개선 방안 추가"):
        st.session_state.eval_improvements.append("")
        st.rerun()

    st.divider()

    # ── 관객 후기 ──
    st.subheader("2. 주요 관객 후기")
    st.info("'분류'에 '긍정' 또는 '부정'을 입력하면 보고서에서 해당 섹션 아래 표로 자동 삽입됩니다.")

    for i, review in enumerate(st.session_state.visitor_reviews):
        cols = st.columns([2, 6, 2, 0.5])
        with cols[0]:
            st.session_state.visitor_reviews[i]["category"] = st.selectbox(
                "분류", options=["긍정", "부정", "건의"],
                index=["긍정", "부정", "건의"].index(review.get("category", "긍정")) if review.get("category", "긍정") in ["긍정", "부정", "건의"] else 0,
                key=f"rev_cat_{i}"
            )
        with cols[1]:
            st.session_state.visitor_reviews[i]["content"] = st.text_input(
                "상세 내용", value=review.get("content", ""), key=f"rev_con_{i}"
            )
        with cols[2]:
            st.session_state.visitor_reviews[i]["source"] = st.text_input(
                "출처", value=review.get("source", ""), key=f"rev_src_{i}",
                placeholder="예: 방명록, SNS"
            )
        with cols[3]:
            st.write("")
            st.write("")
            if i > 0 and st.button("🗑️", key=f"del_rev_{i}"):
                remove_item("visitor_reviews", i)
                st.rerun()

    if st.button("➕ 후기 추가"):
        add_item("visitor_reviews", {"category": "", "content": "", "source": ""})
        st.rerun()


# ══════════════════════════════════════════════
# 탭 7: 보고서 생성
# ══════════════════════════════════════════════

def collect_data():
    """폼 데이터를 report_generator v2에 맞는 구조로 변환"""

    # 전시 기간 포맷
    period = f"{st.session_state.period_start.strftime('%Y.%m.%d')} - {st.session_state.period_end.strftime('%Y.%m.%d')}"

    # 총 사용 예산 포맷
    budget_text = st.session_state.total_budget_overview
    budget_breakdown = []
    if st.session_state.budget_exhibition or st.session_state.budget_supplementary:
        parts = []
        if st.session_state.budget_exhibition:
            parts.append(f"전시 사용 예산 {st.session_state.budget_exhibition}")
        if st.session_state.budget_supplementary:
            parts.append(f"부대 사용 예산 {st.session_state.budget_supplementary}")
        if not budget_text:
            budget_text = " / ".join(parts)
        budget_breakdown = [f"지출 구성: {' / '.join(parts)}"]

    # 운영 인력 자동 산출
    staff_overview = ""
    paid_str = st.session_state.staff_paid_count.replace("명", "").replace(",", "").strip()
    vol_str = st.session_state.staff_volunteer_count.replace("명", "").replace(",", "").strip()
    try:
        paid_n = int(paid_str) if paid_str else 0
        vol_n = int(vol_str) if vol_str else 0
        if paid_n > 0 or vol_n > 0:
            s_parts = []
            if paid_n > 0:
                s_parts.append(f"스태프 {paid_n}명")
            if vol_n > 0:
                s_parts.append(f"봉사자 {vol_n}명")
            staff_overview = ", ".join(s_parts)
    except ValueError:
        staff_overview = ""

    # 일평균 관객수 자동 산출
    auto_daily_avg = ""
    v_str = st.session_state.visitor_count.replace("명", "").replace(",", "").strip()
    try:
        v_num = int(v_str) if v_str else 0
        d_num = st.session_state.exhibition_days
        if v_num > 0 and d_num > 0:
            auto_daily_avg = f"{v_num // d_num}명"
    except ValueError:
        auto_daily_avg = ""

    # 참여 작가 리스트
    artists = [a.strip() for a in st.session_state.artists.split(",") if a.strip()]

    # 예산 차트 데이터
    budget_chart_data = {}
    for item in st.session_state.budget_summary:
        cat = item.get("category", "")
        if cat:
            try:
                planned = int(item.get("planned", "0").replace(",", "").replace("원", ""))
            except ValueError:
                planned = 0
            try:
                actual = int(item.get("actual", "0").replace(",", "").replace("원", ""))
            except ValueError:
                actual = 0
            budget_chart_data[cat] = {"planned": planned, "actual": actual}

    # 운영인력 데이터 (dict 형식: count/role)
    staff_data = {}
    if st.session_state.staff_main_count or st.session_state.staff_main_role:
        staff_data["main_staff"] = {
            "count": st.session_state.staff_main_count,
            "role": st.session_state.staff_main_role,
        }
    if st.session_state.staff_volunteers_count or st.session_state.staff_volunteers_role:
        staff_data["volunteers"] = {
            "count": st.session_state.staff_volunteers_count,
            "role": st.session_state.staff_volunteers_role,
        }
    # 포스터 이미지
    poster_path = None
    poster_file = st.session_state.get("poster_file")
    if poster_file:
        poster_path = os.path.join(tempfile.gettempdir(), "poster_image.png")
        with open(poster_path, "wb") as f:
            f.write(poster_file.getvalue())

    data = {
        "exhibition_title": st.session_state.exhibition_title,
        "exhibition_period": period,
        "poster_image": poster_path,
        "overview": {
            "title": st.session_state.exhibition_title,
            "period": period,
            "artists": artists,
            "chief_curator": st.session_state.chief_curator,
            "curators": st.session_state.curators,
            "coordinators": st.session_state.coordinators,
            "curatorial_team": st.session_state.curatorial_team,
            "pr": st.session_state.pr_person,
            "sponsors": st.session_state.sponsors,
            "total_budget": budget_text,
            "budget_breakdown": budget_breakdown,
            "total_revenue": st.session_state.total_revenue_overview,
            "programs": st.session_state.programs_overview,
            "staff_count": staff_overview,
            "visitors": st.session_state.visitor_count,
        },
        "theme_text": st.session_state.theme_text,
        "rooms": [],
        "related_programs": [p for p in st.session_state.related_programs if p.get("title")],
        "program_photos": [],
        "staff": staff_data,
        "printed_materials": [m for m in st.session_state.printed_materials if m.get("type")],
        "material_photos": [],  # 이미지는 아래에서 처리
        "budget": {
            "total_spent": st.session_state.budget_total_spent,
            "breakdown_notes": [n for n in st.session_state.budget_breakdown_notes if n.strip()],
            "summary": [s for s in st.session_state.budget_summary if s.get("category")],
            "arrow_notes": [n for n in st.session_state.budget_arrow_notes if n.strip()],
            "chart_data": budget_chart_data,
            "details": [d for d in st.session_state.budget_details if d.get("subcategory") or d.get("detail")],
        },
        "revenue": {
            "total_visitors": st.session_state.revenue_visitors,
            "daily_average": st.session_state.revenue_daily_average or auto_daily_avg,
            "visitor_notes": [n for n in st.session_state.revenue_visitor_notes if n.strip()],
            "total_revenue": st.session_state.revenue_total,
            "ticket_revenue": st.session_state.revenue_ticket,
            "partnership_revenue": st.session_state.revenue_partnership,
            "revenue_notes": [n for n in st.session_state.revenue_revenue_notes if n.strip()],
        },
        "visitor_composition": {
            "note": st.session_state.visitor_comp_note,
            "ticket_type": {},
            "ticket_analysis": [t for t in st.session_state.visitor_ticket_analysis if t.strip()],
            "visitor_type": {},
            "weekly_visitors": {k: v for k, v in st.session_state.weekly_visitors.items() if v > 0},
            "analysis": st.session_state.visitor_analysis,
        },
        "promotion": {
            "advertising": st.session_state.promo_advertising,
            "press_release": st.session_state.promo_press_release,
            "web_invitation": st.session_state.promo_web_invitation,
            "newsletter": st.session_state.promo_newsletter,
            "sns": st.session_state.promo_sns,
            "other": st.session_state.promo_other,
        },
        "promotion_photos": [],
        "press_coverage": {
            "print_media": [p for p in st.session_state.press_print if p.get("outlet")],
            "online_media": [p for p in st.session_state.press_online if p.get("outlet")],
        },
        "membership": st.session_state.membership_text,
        "evaluation": {
            "positive": [e for e in st.session_state.eval_positive if e.strip()],
            "negative": [e for e in st.session_state.eval_negative if e.strip()],
            "improvements": [e for e in st.session_state.eval_improvements if e.strip()],
        },
        "visitor_reviews": [r for r in st.session_state.visitor_reviews if r.get("content")],
    }

    # 입장권별 관객 구성 데이터
    if st.session_state.visitor_general > 0:
        data["visitor_composition"]["ticket_type"]["일반"] = st.session_state.visitor_general
    if st.session_state.visitor_student > 0:
        data["visitor_composition"]["ticket_type"]["학생"] = st.session_state.visitor_student
    if st.session_state.visitor_invitation > 0:
        data["visitor_composition"]["ticket_type"]["초대권"] = st.session_state.visitor_invitation
    if st.session_state.visitor_artpass > 0:
        data["visitor_composition"]["ticket_type"]["예술인패스"] = st.session_state.visitor_artpass
    if st.session_state.visitor_discount > 0:
        data["visitor_composition"]["ticket_type"]["기타 할인"] = st.session_state.visitor_discount

    # 유형별 관객 구성 데이터
    vtype_data = {}
    if st.session_state.vtype_individual > 0: vtype_data["개인"] = st.session_state.vtype_individual
    if st.session_state.vtype_art_univ > 0: vtype_data["미술대학 단체"] = st.session_state.vtype_art_univ
    if st.session_state.vtype_other_group > 0: vtype_data["기타 단체"] = st.session_state.vtype_other_group
    if st.session_state.vtype_opening > 0: vtype_data["오프닝 리셉션"] = st.session_state.vtype_opening
    data["visitor_composition"]["visitor_type"] = vtype_data

    # 전시실 데이터 (이미지 처리)
    for room in st.session_state.rooms:
        room_data = {
            "name": room.get("name", ""),
            "artists": room.get("artists", ""),
        }

        # 도면 이미지 저장
        floor_plan_file = room.get("floor_plan_file")
        if floor_plan_file:
            fp_path = os.path.join(tempfile.gettempdir(), f"floor_{room.get('name', 'room')}.png")
            with open(fp_path, "wb") as f:
                f.write(floor_plan_file.getvalue())
            room_data["floor_plan"] = fp_path

        # 전경 사진 저장
        photo_files = room.get("photo_files", [])
        photo_paths = []
        for j, photo in enumerate(photo_files):
            p_path = os.path.join(tempfile.gettempdir(), f"photo_{room.get('name', 'room')}_{j}.png")
            with open(p_path, "wb") as f:
                f.write(photo.getvalue())
            photo_paths.append(p_path)
        room_data["photos"] = photo_paths

        data["rooms"].append(room_data)

    return data


def save_uploaded_images_to_temp(uploaded_files, prefix="img"):
    """업로드된 파일을 임시 경로에 저장하고 경로 리스트 반환"""
    paths = []
    if uploaded_files:
        for i, f in enumerate(uploaded_files):
            path = os.path.join(tempfile.gettempdir(), f"{prefix}_{i}.png")
            with open(path, "wb") as out:
                out.write(f.getvalue())
            paths.append(path)
    return paths


# ══════════════════════════════════════════════
# 탭 7: 분석 인사이트 (신규)
# ══════════════════════════════════════════════

def _collect_current_for_analysis() -> dict:
    """현재 입력된 데이터를 분석용 flat dict로 변환"""

    def parse_num(s):
        if s is None:
            return None
        if isinstance(s, (int, float)):
            return float(s)
        s = str(s).replace(",", "").replace("명", "").replace("원", "")
        s = s.replace("%", "").replace("약 ", "").replace("개", "").replace("회", "").strip()
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    ticket = {}
    if st.session_state.visitor_general > 0:
        ticket["일반"] = st.session_state.visitor_general
    if st.session_state.visitor_student > 0:
        ticket["학생"] = st.session_state.visitor_student
    if st.session_state.visitor_invitation > 0:
        ticket["초대권"] = st.session_state.visitor_invitation
    if st.session_state.visitor_artpass > 0:
        ticket["예술인패스"] = st.session_state.visitor_artpass
    if st.session_state.visitor_discount > 0:
        ticket["기타 할인"] = st.session_state.visitor_discount

    total_visitors = parse_num(st.session_state.revenue_visitors) or parse_num(st.session_state.visitor_count)

    # 유료 관객 = 일반 + 학생 (또는 총 관객 - 초대)
    paid = ticket.get("일반", 0) + ticket.get("학생", 0)

    # 프로그램 참여 인원 합산
    prog_participants = 0
    for prog in st.session_state.related_programs:
        p = parse_num(prog.get("participants"))
        if p:
            prog_participants += p

    # 언론 보도 건수
    press_count = (
        len([p for p in st.session_state.press_print if p.get("outlet")])
        + len([p for p in st.session_state.press_online if p.get("outlet")])
    )

    return {
        "전시 제목": st.session_state.exhibition_title,
        "전시 일수": st.session_state.exhibition_days or None,
        "총 관객수": total_visitors,
        "일평균 관객수": parse_num(st.session_state.revenue_daily_average),
        "유료 관객수": paid if paid > 0 else None,
        "무료/초대 관객수": ticket.get("초대권", 0) or None,
        "학생 관객수(만 24세 이하)": ticket.get("학생", 0) or None,
        "예술인패스 관객수": ticket.get("예술인패스", 0) or None,
        "단체 관객수": (st.session_state.vtype_art_univ + st.session_state.vtype_other_group) or None,
        "오프닝 참석 인원": st.session_state.vtype_opening or None,
        "총 사용 예산": parse_num(st.session_state.total_budget_overview),
        "총수입": parse_num(st.session_state.revenue_total) or parse_num(st.session_state.total_revenue_overview),
        "입장 수입": parse_num(st.session_state.revenue_ticket),
        "프로그램 총 수": len([p for p in st.session_state.related_programs if p.get("title")]) or None,
        "프로그램 참여 인원": prog_participants or None,
        "도슨트 참여 인원": None,  # 별도 입력 필드 없음
        "언론 보도 건수": press_count or None,
        "SNS 게시 건수": None,  # 별도 입력 필드 없음
        "뉴스레터 오픈율": None,  # 별도 입력 필드 없음
        "출품 작품 수_총": None,  # 별도 입력 필드 없음
        "참여 작가 수_총(팀)": len([a.strip() for a in st.session_state.artists.split(",") if a.strip()]) or None,
    }


with tab7:
    st.markdown('<div class="section-header">🔍 분석 인사이트</div>', unsafe_allow_html=True)

    ref_df = load_reference_data()

    if ref_df is None:
        st.warning("⚠️ 레퍼런스 데이터 파일을 찾을 수 없습니다. `exhibition_reference_data.xlsx` 파일을 앱 폴더에 넣어주세요.")
    else:
        # 유형 0(특수 전시) 제외한 분석 대상 수
        analysis_count = len(rd.exclude_type_zero(ref_df))
        excluded_count = len(ref_df) - analysis_count
        info_text = f"📊 레퍼런스: {analysis_count}개 과거 전시 데이터 기반 비교 분석"
        if excluded_count > 0:
            info_text += f" (유형 0으로 분류된 {excluded_count}개 특수 전시 제외)"
        st.info(info_text)

        # 전시 유형 선택
        type_col = "전시 유형"
        has_type_data = type_col in ref_df.columns and ref_df[type_col].notna().any()

        if has_type_data:
            # 유형 0 제외
            valid_types = sorted([t for t in ref_df[type_col].dropna().unique() if int(t) != 0])
            type_options = ["전체 (유형 0 제외)"] + [f"{int(t)}유형 ({rd.get_type_count(ref_df, t)}개 전시)" for t in valid_types]
            selected_type_idx = st.selectbox(
                "비교 대상 전시 유형",
                range(len(type_options)),
                format_func=lambda i: type_options[i],
                help="같은 유형의 전시끼리 비교하면 더 의미 있는 분석이 가능합니다. 유형 값이 3개 미만이면 전체 비교로 전환됩니다.",
                key="analysis_type_select"
            )
            exhibition_type = valid_types[selected_type_idx - 1] if selected_type_idx > 0 else None
        else:
            exhibition_type = None
            st.caption("💡 레퍼런스 Excel의 '전시 유형' 컬럼에 값(1, 2, 3 등)을 채우면 유형별 비교가 가능합니다.")

        # 분석 실행
        if st.button("🔍 분석 실행", type="primary", use_container_width=True,
                      help="현재 입력된 데이터를 과거 전시와 비교합니다"):
            current = _collect_current_for_analysis()

            # 입력 데이터 확인
            has_data = any(v is not None and v != 0 for k, v in current.items() if k != "전시 제목")
            if not has_data:
                st.warning("분석할 데이터가 부족합니다. 예산, 관객, 프로그램 등의 정보를 먼저 입력해주세요.")
            else:
                result = ae.generate_all_insights(current, ref_df, exhibition_type=exhibition_type)
                st.session_state["analysis_result"] = result
                st.session_state["analysis_current"] = current

        # 결과 표시
        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]
            grouped = ae.get_insights_by_category(result)

            if not result.insights:
                st.info("생성된 인사이트가 없습니다. 더 많은 데이터를 입력해주세요.")
            else:
                st.markdown(f"**{len(result.insights)}개의 인사이트가 생성되었습니다.** 체크박스로 보고서에 포함할 항목을 선택하고, 텍스트를 자유롭게 수정할 수 있습니다.")

                # 세션에 선택/수정 상태 초기화
                if "insight_selections" not in st.session_state:
                    st.session_state["insight_selections"] = {}
                if "insight_texts" not in st.session_state:
                    st.session_state["insight_texts"] = {}

                for cat in ae.CATEGORY_ORDER:
                    if cat not in grouped:
                        continue

                    icon = ae.CATEGORY_ICONS.get(cat, "")
                    label = ae.CATEGORY_LABELS.get(cat, cat)

                    with st.expander(f"{icon} {label} ({len(grouped[cat])}건)", expanded=True):
                        for i, ins in enumerate(grouped[cat]):
                            key = f"ins_{cat}_{i}"

                            col_check, col_text = st.columns([0.5, 9.5])

                            with col_check:
                                # 기본값: 우선순위 1,2는 선택, 3은 미선택
                                default_selected = ins.priority <= 2
                                prev = st.session_state["insight_selections"].get(key, default_selected)
                                selected = st.checkbox(
                                    "", value=prev, key=f"chk_{key}",
                                    label_visibility="collapsed"
                                )
                                st.session_state["insight_selections"][key] = selected

                            with col_text:
                                # 백분위/순위 배지
                                badges = []
                                if ins.percentile is not None:
                                    badges.append(f"P{ins.percentile}")
                                if ins.rank and ins.total_count:
                                    badges.append(f"#{ins.rank}/{ins.total_count}")
                                badge_str = " · ".join(badges)

                                st.markdown(
                                    f"**{ins.title}** {f'`{badge_str}`' if badge_str else ''}",
                                )

                                prev_text = st.session_state["insight_texts"].get(key, ins.text)
                                edited = st.text_area(
                                    "분석 문장", value=prev_text,
                                    key=f"txt_{key}",
                                    height=68,
                                    label_visibility="collapsed",
                                )
                                st.session_state["insight_texts"][key] = edited

                # ── 유사 전시 비교표 ──
                if result.similar_comparison_table is not None:
                    st.divider()
                    st.subheader("📋 유사 전시 비교표")
                    st.markdown("현재 전시와 가장 유사한 과거 전시들의 주요 지표 비교입니다.")

                    # 유사도 점수도 표시
                    display_df = result.similar_comparison_table.copy()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                # ── 레퍼런스 갱신 ──
                st.divider()
                st.subheader("📥 레퍼런스 갱신")
                st.markdown("보고서 완성 후, 이번 전시 데이터를 레퍼런스에 추가하면 향후 분석이 더 정확해집니다.")

                if st.button("➕ 이번 전시를 레퍼런스에 추가", use_container_width=True):
                    if "analysis_current" in st.session_state:
                        try:
                            ref_path = os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                "exhibition_reference_data.xlsx"
                            )
                            if not os.path.exists(ref_path):
                                ref_path = os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    "..", "exhibition_reference_data.xlsx"
                                )
                            rd.add_exhibition_to_reference(
                                ref_path,
                                st.session_state["analysis_current"]
                            )
                            st.success(f"✅ 《{st.session_state.exhibition_title}》 데이터가 레퍼런스에 추가되었습니다!")
                            # 캐시 초기화
                            load_reference_data.clear()
                        except Exception as e:
                            st.error(f"❌ 레퍼런스 갱신 실패: {str(e)}")
                    else:
                        st.warning("먼저 '분석 실행'을 눌러주세요.")


with tab8:
    st.markdown('<div class="section-header">보고서 생성</div>', unsafe_allow_html=True)

    # 입력 현황 요약
    st.subheader("입력 현황")

    col_stat1, col_stat2, col_stat3 = st.columns(3)

    with col_stat1:
        has_title = "✅" if st.session_state.exhibition_title else "❌"
        has_theme = "✅" if st.session_state.theme_text else "❌"
        has_rooms = "✅" if any(r.get("name") for r in st.session_state.rooms) else "❌"
        st.markdown(f"""
        **기본 정보**
        - {has_title} 전시 제목
        - {has_theme} 전시 주제
        - {has_rooms} 전시실 구성
        """)

    with col_stat2:
        has_budget = "✅" if st.session_state.budget_total_spent else "❌"
        has_visitors = "✅" if (st.session_state.visitor_general + st.session_state.visitor_student + st.session_state.visitor_invitation + st.session_state.visitor_artpass + st.session_state.visitor_discount > 0) else "❌"
        has_promo = "✅" if any([st.session_state.promo_advertising, st.session_state.promo_sns]) else "❌"
        st.markdown(f"""
        **결과 데이터**
        - {has_budget} 예산 정보
        - {has_visitors} 관객 구성
        - {has_promo} 홍보 정보
        """)

    with col_stat3:
        has_eval = "✅" if any(st.session_state.eval_positive) else "❌"
        has_reviews = "✅" if any(r.get("content") for r in st.session_state.visitor_reviews) else "❌"
        has_insights = "✅" if "analysis_result" in st.session_state else "❌"
        insight_count = len(st.session_state.get("analysis_result", ae.AnalysisResult()).insights) if "analysis_result" in st.session_state else 0
        st.markdown(f"""
        **평가 및 분석**
        - {has_eval} 평가 항목
        - {has_reviews} 관객 후기
        - {has_insights} 분석 인사이트 ({insight_count}건)
        """)

    st.divider()

    # 생성 버튼
    if not st.session_state.exhibition_title:
        st.warning("⚠️ 전시 제목은 필수 항목입니다. '기본 정보' 탭에서 입력해주세요.")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("📄 Word 보고서 생성", type="primary", disabled=not st.session_state.exhibition_title,
                      use_container_width=True):
            with st.spinner("보고서를 생성하고 있습니다..."):
                try:
                    data = collect_data()

                    # 선택된 인사이트 수집
                    selected_insights = []
                    if "analysis_result" in st.session_state:
                        ar = st.session_state["analysis_result"]
                        grouped = ae.get_insights_by_category(ar)
                        for cat in ae.CATEGORY_ORDER:
                            if cat not in grouped:
                                continue
                            for i, ins in enumerate(grouped[cat]):
                                key = f"ins_{cat}_{i}"
                                if st.session_state.get("insight_selections", {}).get(key, ins.priority <= 2):
                                    edited_text = st.session_state.get("insight_texts", {}).get(key, ins.text)
                                    selected_insights.append({
                                        "category": cat,
                                        "category_label": ae.CATEGORY_LABELS.get(cat, cat),
                                        "title": ins.title,
                                        "text": edited_text,
                                    })
                        # 유사 전시 비교표
                        if ar.similar_comparison_table is not None:
                            data["similar_comparison_table"] = ar.similar_comparison_table.values.tolist()
                            data["similar_comparison_headers"] = ar.similar_comparison_table.columns.tolist()

                    data["analysis_insights"] = selected_insights

                    output_path = os.path.join(tempfile.gettempdir(), f"전시보고서_{st.session_state.exhibition_title}.docx")
                    generate_report(data, output_path)

                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Word 파일 다운로드",
                            data=f.read(),
                            file_name=f"전시보고서 - 《{st.session_state.exhibition_title}》.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                    st.success("✅ Word 보고서가 생성되었습니다!")
                except Exception as e:
                    st.error(f"❌ 보고서 생성 중 오류가 발생했습니다: {str(e)}")

    with col_btn2:
        st.button("📋 PDF 보고서 생성", disabled=True, use_container_width=True,
                   help="PDF 변환 기능은 Word 생성 후 별도 도구로 변환할 수 있습니다.")

    st.divider()

    # 데이터 저장/불러오기
    st.subheader("데이터 관리")
    col_save1, col_save2 = st.columns(2)

    with col_save1:
        if st.button("💾 입력 데이터 저장 (JSON)", use_container_width=True):
            data = collect_data()
            # 이미지 경로 제거 (JSON에 저장 불가)
            for room in data.get("rooms", []):
                room.pop("floor_plan", None)
                room.pop("photos", None)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ JSON 다운로드",
                data=json_str,
                file_name=f"전시보고서_데이터_{st.session_state.exhibition_title or 'draft'}.json",
                mime="application/json",
                use_container_width=True
            )

    with col_save2:
        uploaded_json = st.file_uploader("📂 저장된 데이터 불러오기", type=["json"])
        if uploaded_json:
            try:
                loaded = json.loads(uploaded_json.read().decode("utf-8"))
                st.success("데이터를 불러왔습니다! (페이지를 새로고침하면 반영됩니다)")
                # TODO: loaded 데이터를 session_state에 반영하는 로직
            except Exception as e:
                st.error(f"데이터 불러오기 실패: {str(e)}")


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
    **일민미술관 전시보고서 생성기** v1.0

    기존 보고서 형식을 기반으로
    자동 생성합니다.

    차트(파이/바)는 데이터 입력 시
    자동으로 생성됩니다.
    """)
