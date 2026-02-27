"""
공통 헬퍼 함수
"""

import os
import tempfile
import json
import streamlit as st
from datetime import date


def add_item(key, template):
    """리스트에 새 항목 추가"""
    st.session_state[key].append(template.copy())


def remove_item(key, index):
    """리스트에서 항목 제거"""
    if len(st.session_state[key]) > 1:
        st.session_state[key].pop(index)


def parse_amount(s):
    """금액 문자열에서 숫자 추출 (예: '42,574,000원' → 42574000)"""
    if not s:
        return 0
    s = str(s).replace(",", "").replace("원", "").replace("약 ", "").strip()
    try:
        return int(s)
    except ValueError:
        return 0


def parse_num(s):
    """범용 숫자 파싱 (명, 원, %, 개, 회 등 단위 제거)"""
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

    # 일평균 관객 수 자동 산출
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
        "material_photos": [],
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


def collect_current_for_analysis() -> dict:
    """현재 입력된 데이터를 분석용 flat dict로 변환"""

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
        "도슨트 참여 인원": None,
        "언론 보도 건수": press_count or None,
        "SNS 게시 건수": None,
        "뉴스레터 오픈율": None,
        "출품 작품 수_총": None,
        "참여 작가 수_총(팀)": len([a.strip() for a in st.session_state.artists.split(",") if a.strip()]) or None,
    }
