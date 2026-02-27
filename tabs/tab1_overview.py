"""탭 1: 기본 정보 (전시 개요)"""

import streamlit as st
from datetime import date
from utils import parse_amount


def render(tab):
    with tab:
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
            # B8: 참여 작가 수 자동 표시
            _artist_list = [a.strip() for a in st.session_state.artists.split(",") if a.strip()]
            if _artist_list:
                st.caption(f"입력된 작가: {len(_artist_list)}명")

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
            st.session_state.sponsors = st.text_input(
                "후원", value=st.session_state.sponsors,
                placeholder="예: 한국문화예술위원회"
            )
        with col4:
            # 전시 일수: 날짜에서 자동 계산, 날짜 변경 시 재계산, 수동 수정 가능
            _auto_days = (st.session_state.period_end - st.session_state.period_start).days + 1
            _prev_auto = st.session_state.get('_prev_auto_days', 0)
            if _auto_days > 0 and (_prev_auto != _auto_days or st.session_state.exhibition_days == 0):
                st.session_state.exhibition_days = _auto_days
                st.session_state._prev_auto_days = _auto_days
            st.session_state.exhibition_days = st.number_input(
                "전시 일수", min_value=0, value=st.session_state.exhibition_days,
                placeholder="예: 52", help="시작일~종료일 기준 자동 계산. 휴관일 제외 시 직접 수정하세요."
            )

        # ── 데이터 흐름 우선순위 ──
        # 총 사용 예산의 원본: 전시비+부대비 자동합산 > 직접 입력
        col_b1, col_b2, col_b3 = st.columns(3)
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
        with col_b3:
            _budget_sum = parse_amount(st.session_state.budget_exhibition) + parse_amount(st.session_state.budget_supplementary)
            if _budget_sum > 0:
                st.session_state.total_budget_overview = f"{_budget_sum:,}원"
            st.text_input(
                "총 사용 예산 (자동 산출)", value=st.session_state.total_budget_overview, disabled=True
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

        # ── 데이터 흐름 우선순위 ──
        # 관객 수의 원본: 입장권별 합계 (탭4) > 직접 입력 (탭1)
        col8, col9 = st.columns(2)
        with col8:
            st.session_state.visitor_count = st.text_input(
                "관객 수", value=st.session_state.visitor_count,
                placeholder="예: 7,009명"
            )
        with col9:
            # 일평균 관객의 원본: 총관객수÷전시일수 자동계산 (항상)
            auto_daily = ""
            visitor_str = st.session_state.visitor_count.replace("명", "").replace(",", "").strip()
            try:
                visitor_num = int(visitor_str) if visitor_str else 0
                days_num = st.session_state.exhibition_days
                if visitor_num > 0 and days_num > 0:
                    auto_daily = f"{visitor_num // days_num}명"
            except ValueError:
                auto_daily = ""
            st.text_input("일평균 관객 수 (자동 산출)", value=auto_daily, disabled=True)

        # 프로그램: 전시 구성 탭 데이터에서 자동 생성
        _progs = st.session_state.related_programs
        _valid_progs = [p for p in _progs if p.get("category", "").strip() or p.get("title", "").strip()]
        _total_part = 0
        _cat_counts = {}
        for p in _valid_progs:
            cat = p.get("category", "").strip() or p.get("title", "").strip()
            _cat_counts[cat] = _cat_counts.get(cat, 0) + 1
            try:
                _total_part += int(str(p.get("participants", "0")).replace(",", "").replace("명", "").strip() or "0")
            except ValueError:
                pass
        if _cat_counts:
            _cat_strs = [f"{cat} {cnt}회" for cat, cnt in _cat_counts.items()]
            _auto_prog = f"총 {len(_valid_progs)}개 프로그램: " + ", ".join(_cat_strs)
            if _total_part > 0:
                _auto_prog += f" ({_total_part:,}명 참여)"
            st.session_state.programs_overview = _auto_prog

        st.text_input(
            "프로그램 (자동 산출)", value=st.session_state.programs_overview, disabled=True
        )

        st.markdown("**포스터 이미지** (목차 페이지에 표시됨)")
        poster_file = st.file_uploader("포스터 이미지 업로드", type=["png", "jpg", "jpeg"], key="poster_upload")
        if poster_file:
            st.session_state["poster_file"] = poster_file
            st.image(poster_file, width=200, caption="포스터 미리보기")
