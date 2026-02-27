"""탭 6: 평가"""

import streamlit as st
from utils import add_item, remove_item


def render(tab):
    with tab:
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
