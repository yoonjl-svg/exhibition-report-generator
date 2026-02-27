"""탭 8: 보고서 생성"""

import os
import json
import tempfile
import streamlit as st
import analysis_engine as ae
from report_generator import generate_report
from utils import collect_data


def _load_json_to_session(loaded):
    """JSON 데이터를 session_state에 매핑"""
    # overview 필드 매핑
    overview = loaded.get("overview", {})
    if overview.get("title"):
        st.session_state.exhibition_title = overview["title"]
    if overview.get("chief_curator"):
        st.session_state.chief_curator = overview["chief_curator"]
    if overview.get("curators"):
        st.session_state.curators = overview["curators"]
    if overview.get("coordinators"):
        st.session_state.coordinators = overview["coordinators"]
    if overview.get("curatorial_team"):
        st.session_state.curatorial_team = overview["curatorial_team"]
    if overview.get("pr"):
        st.session_state.pr_person = overview["pr"]
    if overview.get("sponsors"):
        st.session_state.sponsors = overview["sponsors"]
    if overview.get("total_budget"):
        st.session_state.total_budget_overview = overview["total_budget"]
    if overview.get("total_revenue"):
        st.session_state.total_revenue_overview = overview["total_revenue"]
    if overview.get("programs"):
        st.session_state.programs_overview = overview["programs"]
    if overview.get("visitors"):
        st.session_state.visitor_count = overview["visitors"]
    if overview.get("artists"):
        st.session_state.artists = ", ".join(overview["artists"]) if isinstance(overview["artists"], list) else overview["artists"]

    # theme
    if loaded.get("theme_text"):
        st.session_state.theme_text = loaded["theme_text"]

    # related_programs
    if loaded.get("related_programs"):
        st.session_state.related_programs = loaded["related_programs"]

    # budget
    budget = loaded.get("budget", {})
    if budget.get("total_spent"):
        st.session_state.budget_total_spent = budget["total_spent"]
    if budget.get("breakdown_notes"):
        st.session_state.budget_breakdown_notes = budget["breakdown_notes"]
    if budget.get("summary"):
        st.session_state.budget_summary = budget["summary"]
    if budget.get("arrow_notes"):
        st.session_state.budget_arrow_notes = budget["arrow_notes"]
    if budget.get("details"):
        st.session_state.budget_details = budget["details"]

    # revenue
    revenue = loaded.get("revenue", {})
    if revenue.get("total_visitors"):
        st.session_state.revenue_visitors = revenue["total_visitors"]
    if revenue.get("daily_average"):
        st.session_state.revenue_daily_average = revenue["daily_average"]
    if revenue.get("visitor_notes"):
        st.session_state.revenue_visitor_notes = revenue["visitor_notes"]
    if revenue.get("total_revenue"):
        st.session_state.revenue_total = revenue["total_revenue"]
    if revenue.get("ticket_revenue"):
        st.session_state.revenue_ticket = revenue["ticket_revenue"]
    if revenue.get("partnership_revenue"):
        st.session_state.revenue_partnership = revenue["partnership_revenue"]
    if revenue.get("revenue_notes"):
        st.session_state.revenue_revenue_notes = revenue["revenue_notes"]

    # visitor_composition
    vc = loaded.get("visitor_composition", {})
    ticket_type = vc.get("ticket_type", {})
    if ticket_type.get("일반"):
        st.session_state.visitor_general = ticket_type["일반"]
    if ticket_type.get("학생"):
        st.session_state.visitor_student = ticket_type["학생"]
    if ticket_type.get("초대권"):
        st.session_state.visitor_invitation = ticket_type["초대권"]
    if ticket_type.get("예술인패스"):
        st.session_state.visitor_artpass = ticket_type["예술인패스"]
    if ticket_type.get("기타 할인"):
        st.session_state.visitor_discount = ticket_type["기타 할인"]
    vtype = vc.get("visitor_type", {})
    if vtype.get("개인"):
        st.session_state.vtype_individual = vtype["개인"]
    if vtype.get("미술대학 단체"):
        st.session_state.vtype_art_univ = vtype["미술대학 단체"]
    if vtype.get("기타 단체"):
        st.session_state.vtype_other_group = vtype["기타 단체"]
    if vtype.get("오프닝 리셉션"):
        st.session_state.vtype_opening = vtype["오프닝 리셉션"]
    if vc.get("weekly_visitors"):
        st.session_state.weekly_visitors = vc["weekly_visitors"]
    if vc.get("analysis"):
        st.session_state.visitor_analysis = vc["analysis"]
    if vc.get("note"):
        st.session_state.visitor_comp_note = vc["note"]
    if vc.get("ticket_analysis"):
        st.session_state.visitor_ticket_analysis = vc["ticket_analysis"]

    # promotion
    promo = loaded.get("promotion", {})
    if promo.get("advertising"):
        st.session_state.promo_advertising = promo["advertising"]
    if promo.get("press_release"):
        st.session_state.promo_press_release = promo["press_release"]
    if promo.get("web_invitation"):
        st.session_state.promo_web_invitation = promo["web_invitation"]
    if promo.get("newsletter"):
        st.session_state.promo_newsletter = promo["newsletter"]
    if promo.get("sns"):
        st.session_state.promo_sns = promo["sns"]
    if promo.get("other"):
        st.session_state.promo_other = promo["other"]

    # press_coverage
    press = loaded.get("press_coverage", {})
    if press.get("print_media"):
        st.session_state.press_print = press["print_media"]
    if press.get("online_media"):
        st.session_state.press_online = press["online_media"]

    # membership
    if loaded.get("membership"):
        st.session_state.membership_text = loaded["membership"]

    # evaluation
    evaluation = loaded.get("evaluation", {})
    if evaluation.get("positive"):
        st.session_state.eval_positive = evaluation["positive"]
    if evaluation.get("negative"):
        st.session_state.eval_negative = evaluation["negative"]
    if evaluation.get("improvements"):
        st.session_state.eval_improvements = evaluation["improvements"]

    # visitor_reviews
    if loaded.get("visitor_reviews"):
        st.session_state.visitor_reviews = loaded["visitor_reviews"]

    # printed_materials
    if loaded.get("printed_materials"):
        st.session_state.printed_materials = loaded["printed_materials"]

    # staff
    staff = loaded.get("staff", {})
    if staff.get("main_staff"):
        st.session_state.staff_main_count = staff["main_staff"].get("count", "")
        st.session_state.staff_main_role = staff["main_staff"].get("role", "")
    if staff.get("volunteers"):
        st.session_state.staff_volunteers_count = staff["volunteers"].get("count", "")
        st.session_state.staff_volunteers_role = staff["volunteers"].get("role", "")


def render(tab):
    with tab:
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
                    _load_json_to_session(loaded)
                    st.success("✅ 데이터를 불러왔습니다! 각 탭에서 내용을 확인하세요.")
                    st.rerun()
                except Exception as e:
                    st.error(f"데이터 불러오기 실패: {str(e)}")
