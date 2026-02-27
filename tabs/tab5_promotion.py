"""탭 5: 홍보/언론"""

import streamlit as st
from utils import add_item, remove_item


def render(tab):
    with tab:
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

        # B9: 보도 건수 합계 표시
        _print_count = len([p for p in st.session_state.press_print if p.get("outlet", "").strip()])
        _online_count = len([p for p in st.session_state.press_online if p.get("outlet", "").strip()])
        if _print_count > 0 or _online_count > 0:
            st.caption(f"총 보도 건수: {_print_count + _online_count}건 (일간지/월간지 {_print_count}건 + 온라인 {_online_count}건)")

        st.divider()

        # ── 멤버십 ──
        st.subheader("3. 멤버십 커뮤니케이션")
        st.session_state.membership_text = st.text_area(
            "멤버십 관련 내용", value=st.session_state.membership_text, height=100
        )
