"""탭 7: 분석 인사이트"""

import os
import streamlit as st
import reference_data as rd
import analysis_engine as ae
from utils import collect_current_for_analysis


def render(tab, load_reference_data):
    with tab:
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
                current = collect_current_for_analysis()

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
                                    default_selected = ins.priority <= 2
                                    prev = st.session_state["insight_selections"].get(key, default_selected)
                                    selected = st.checkbox(
                                        "", value=prev, key=f"chk_{key}",
                                        label_visibility="collapsed"
                                    )
                                    st.session_state["insight_selections"][key] = selected

                                with col_text:
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
                                    "..", "exhibition_reference_data.xlsx"
                                )
                                if not os.path.exists(ref_path):
                                    ref_path = os.path.join(
                                        os.path.dirname(os.path.abspath(__file__)),
                                        "..", "..", "exhibition_reference_data.xlsx"
                                    )
                                rd.add_exhibition_to_reference(
                                    ref_path,
                                    st.session_state["analysis_current"]
                                )
                                st.success(f"✅ 《{st.session_state.exhibition_title}》 데이터가 레퍼런스에 추가되었습니다!")
                                load_reference_data.clear()
                            except Exception as e:
                                st.error(f"❌ 레퍼런스 갱신 실패: {str(e)}")
                        else:
                            st.warning("먼저 '분석 실행'을 눌러주세요.")
