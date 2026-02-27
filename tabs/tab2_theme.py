"""탭 2: 전시 주제"""

import streamlit as st


def render(tab):
    with tab:
        st.markdown('<div class="section-header">Ⅱ. 전시 주제와 내용</div>', unsafe_allow_html=True)

        st.info("전시에 대한 설명 에세이를 작성해주세요. 문단 구분은 빈 줄로 합니다.")

        st.session_state.theme_text = st.text_area(
            "전시 에세이",
            value=st.session_state.theme_text,
            height=400,
            placeholder="전시의 주제, 배경, 의의 등을 자유롭게 작성해주세요..."
        )
