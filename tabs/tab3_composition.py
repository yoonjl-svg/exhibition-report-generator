"""탭 3: 전시 구성"""

import streamlit as st
from datetime import date
from utils import add_item, remove_item


def render(tab):
    with tab:
        st.markdown('<div class="section-header">Ⅲ. 전시 구성</div>', unsafe_allow_html=True)

        # ── 기본 정보 탭 → 전시 구성 탭 자동 동기화 ──
        if st.session_state.staff_paid_count:
            st.session_state.staff_main_count = st.session_state.staff_paid_count
        if st.session_state.staff_volunteer_count:
            st.session_state.staff_volunteers_count = st.session_state.staff_volunteer_count

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
