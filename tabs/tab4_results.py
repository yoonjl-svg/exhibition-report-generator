"""탭 4: 예산/관객"""

import os
import streamlit as st
from utils import add_item, remove_item, parse_amount
from chart_generator import create_visitor_pie_chart, create_weekly_visitors_chart, create_budget_comparison_chart


def render(tab):
    with tab:
        st.markdown('<div class="section-header">Ⅳ. 전시 결과</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════
        # 데이터 흐름 우선순위:
        # - 총 사용 예산의 원본: 전시비+부대비 자동합산 > 직접 입력
        # - 관객 수의 원본: 입장권별 합계 (탭4) > 직접 입력 (탭1)
        # - 일평균 관객의 원본: 총관객수÷전시일수 자동계산 (항상)
        # ══════════════════════════════════════════

        # ── 기본 정보 탭 → 예산/관객 탭 자동 동기화 ──
        if st.session_state.total_budget_overview:
            st.session_state.budget_total_spent = st.session_state.total_budget_overview
        if st.session_state.visitor_count:
            st.session_state.revenue_visitors = st.session_state.visitor_count
        if st.session_state.total_revenue_overview:
            st.session_state.revenue_total = st.session_state.total_revenue_overview
        if st.session_state.visitor_count and st.session_state.exhibition_days:
            try:
                _v = int(st.session_state.visitor_count.replace("명", "").replace(",", "").strip())
                _d = int(st.session_state.exhibition_days)
                if _v > 0 and _d > 0:
                    st.session_state.revenue_daily_average = f"{_v // _d}명"
            except (ValueError, TypeError):
                pass

        # 지출 구성 텍스트 자동 생성
        _auto_breakdown = ""
        if st.session_state.budget_exhibition or st.session_state.budget_supplementary:
            _parts = []
            if st.session_state.budget_exhibition:
                _parts.append(f"전시비 {st.session_state.budget_exhibition}")
            if st.session_state.budget_supplementary:
                _parts.append(f"부대비 {st.session_state.budget_supplementary}")
            _auto_breakdown = f"지출 구성: {' / '.join(_parts)}"
            st.session_state.budget_breakdown_notes[0] = _auto_breakdown

        # ── 예산 ──
        st.subheader("1. 예산 및 지출")

        st.text_input(
            "지출 총액 (자동 산출)", value=st.session_state.budget_total_spent, disabled=True
        )

        st.markdown("**지출 구성 설명** (- 불릿으로 표시됨)")
        for i, note in enumerate(st.session_state.budget_breakdown_notes):
            cols = st.columns([10, 1])
            with cols[0]:
                if i == 0 and _auto_breakdown:
                    st.text_input(
                        "구성 1 (자동 산출)", value=note, key=f"bdn_{i}",
                        label_visibility="collapsed", disabled=True
                    )
                else:
                    st.session_state.budget_breakdown_notes[i] = st.text_input(
                        f"구성 {i+1}", value=note, key=f"bdn_{i}",
                        label_visibility="collapsed",
                        placeholder="예: 추가 지출 구성 설명"
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

        # B10: 예산 차트 라이브 미리보기
        _chart_cats, _chart_planned, _chart_actual = [], [], []
        for item in st.session_state.budget_summary:
            cat = item.get("category", "").strip()
            if cat:
                _p = parse_amount(item.get("planned", ""))
                _a = parse_amount(item.get("actual", ""))
                if _p > 0 or _a > 0:
                    _chart_cats.append(cat)
                    _chart_planned.append(_p)
                    _chart_actual.append(_a)
        if _chart_cats:
            _chart_path = create_budget_comparison_chart(_chart_cats, _chart_planned, _chart_actual)
            st.image(_chart_path, width=500)
            os.remove(_chart_path)

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
            st.text_input(
                "총 관객 수 (자동 산출)", value=st.session_state.revenue_visitors, disabled=True
            )
            st.text_input(
                "일평균 관객 (자동 산출)", value=st.session_state.revenue_daily_average, disabled=True
            )
            st.session_state.revenue_ticket = st.text_input(
                "입장 수입", value=st.session_state.revenue_ticket, placeholder="예: 42,574,000원"
            )
        with col_rev2:
            st.session_state.revenue_partnership = st.text_input(
                "제휴 수입", value=st.session_state.revenue_partnership
            )

        # A5: 총수입 ← 입장수입 + 제휴수입 자동 합산
        _ticket_rev = parse_amount(st.session_state.revenue_ticket)
        _partner_rev = parse_amount(st.session_state.revenue_partnership)
        if _ticket_rev > 0 or _partner_rev > 0:
            _rev_sum = _ticket_rev + _partner_rev
            st.session_state.revenue_total = f"{_rev_sum:,}원"
            st.session_state.total_revenue_overview = st.session_state.revenue_total

        st.text_input(
            "총 수입 (자동 산출)", value=st.session_state.revenue_total, disabled=True
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

        # A4: 입장권별 합산 → 관객 수 자동 반영
        # 관객 수의 원본: 입장권별 합계 (탭4) > 직접 입력 (탭1)
        _ticket_sum = (st.session_state.visitor_general + st.session_state.visitor_student
                       + st.session_state.visitor_invitation + st.session_state.visitor_artpass
                       + st.session_state.visitor_discount)
        if _ticket_sum > 0:
            st.session_state.visitor_count = f"{_ticket_sum:,}명"
            st.session_state.revenue_visitors = st.session_state.visitor_count
            st.caption(f"입장권별 합계: {_ticket_sum:,}명 → 관객 수에 반영됨")

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

        # B7: 유형별 관객 합계 검증
        _vtype_sum = (st.session_state.vtype_individual + st.session_state.vtype_art_univ
                      + st.session_state.vtype_other_group + st.session_state.vtype_opening)
        if _vtype_sum > 0 and _ticket_sum > 0 and _vtype_sum != _ticket_sum:
            st.warning(f"유형별 합계({_vtype_sum:,}명)와 입장권별 합계({_ticket_sum:,}명)가 다릅니다.")

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

        # B6: 주별 관객 수 합계 검증
        if st.session_state.weekly_visitors:
            _weekly_sum = sum(st.session_state.weekly_visitors.values())
            if _ticket_sum > 0 and _weekly_sum != _ticket_sum:
                st.warning(f"주별 합계({_weekly_sum:,}명)와 입장권별 합계({_ticket_sum:,}명)가 다릅니다.")
            elif _weekly_sum > 0:
                st.caption(f"주별 합계: {_weekly_sum:,}명")

        # 주별 바 차트 미리보기
        if st.session_state.weekly_visitors:
            chart_path = create_weekly_visitors_chart(st.session_state.weekly_visitors)
            st.image(chart_path, width=600)
            os.remove(chart_path)

        st.session_state.visitor_analysis = st.text_area(
            "관객 분석 코멘트",
            value=st.session_state.visitor_analysis,
            height=100,
            placeholder="예: 개인 관객이 전체의 80%를 차지하며..."
        )
