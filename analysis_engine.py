"""
전시 비교 분석 엔진
- 현재 전시 데이터를 레퍼런스와 비교하여 인사이트 생성
- 규칙 기반 + 한국어 템플릿으로 분석 문장 자동 생성
- 카테고리: 관객, 예산, 프로그램, 홍보, 작품, 유사전시
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from reference_data import (
    compute_stats,
    compute_percentile,
    compute_rank,
    compute_derived_metrics,
    get_similar_exhibitions,
    exclude_type_zero,
    filter_by_type,
    get_type_label,
    get_type_count,
    format_number,
    format_percent,
    FieldStats,
)


# ──────────────────────────────────────────────
# 데이터 구조
# ──────────────────────────────────────────────

@dataclass
class Insight:
    """하나의 분석 인사이트"""
    category: str           # "관객", "예산", "프로그램", "홍보", "작품"
    title: str              # 짧은 제목 (예: "총 관객수 순위")
    text: str               # 보고서에 삽입될 분석 문장
    metric_name: str        # 관련 지표명
    current_value: Optional[float] = None
    reference_avg: Optional[float] = None
    percentile: Optional[int] = None
    rank: Optional[int] = None
    total_count: Optional[int] = None
    priority: int = 2       # 1=높음, 2=보통, 3=낮음
    selected: bool = True   # 기본적으로 선택됨


@dataclass
class SimilarExhibitionRow:
    """유사 전시 비교표의 한 행"""
    title: str
    similarity: float
    metrics: dict = field(default_factory=dict)  # {지표명: 값}


@dataclass
class AnalysisResult:
    """전체 분석 결과"""
    insights: list[Insight] = field(default_factory=list)
    similar_exhibitions: list[SimilarExhibitionRow] = field(default_factory=list)
    similar_comparison_table: Optional[pd.DataFrame] = None


# ──────────────────────────────────────────────
# 한국어 템플릿
# ──────────────────────────────────────────────

def _direction(diff_pct: float) -> str:
    """차이 비율에 따른 방향 표현"""
    if diff_pct > 0:
        return "높은"
    else:
        return "낮은"


def _direction_verb(diff_pct: float) -> str:
    if diff_pct > 0:
        return "상회합니다"
    else:
        return "하회합니다"


def _postposition(word: str, particle_pair: tuple = ("은", "는")) -> str:
    """한국어 조사 자동 선택 (받침 유무 기준)"""
    if not word:
        return particle_pair[1]
    last_char = word.rstrip("0123456789,. 원명건개점%")
    if not last_char:
        # 숫자로 끝나면 마지막 숫자의 받침 판단
        digits_final = {"0": True, "1": True, "2": False, "3": True, "4": False,
                        "5": False, "6": True, "7": True, "8": True, "9": False}
        for c in reversed(word):
            if c in digits_final:
                return particle_pair[0] if digits_final[c] else particle_pair[1]
        return particle_pair[1]
    last_code = ord(last_char[-1])
    if 0xAC00 <= last_code <= 0xD7A3:
        # 한글: 종성 유무 확인
        has_batchim = (last_code - 0xAC00) % 28 != 0
        return particle_pair[0] if has_batchim else particle_pair[1]
    return particle_pair[1]


def _quality_word(diff_pct: float, higher_is_better: bool = True) -> str:
    """차이의 질적 평가"""
    if higher_is_better:
        if diff_pct > 30:
            return "매우 우수한"
        elif diff_pct > 10:
            return "양호한"
        elif diff_pct > -10:
            return "평균 수준의"
        elif diff_pct > -30:
            return "다소 저조한"
        else:
            return "저조한"
    else:  # lower is better (e.g., cost)
        if diff_pct < -30:
            return "매우 효율적인"
        elif diff_pct < -10:
            return "효율적인"
        elif diff_pct < 10:
            return "평균 수준의"
        elif diff_pct < 30:
            return "다소 높은"
        else:
            return "높은"


# ──────────────────────────────────────────────
# 단일 지표 인사이트 생성 헬퍼
# ──────────────────────────────────────────────

def _make_basic_insight(
    category: str,
    title: str,
    metric_name: str,
    current_val: float,
    stats: FieldStats,
    unit: str = "",
    higher_is_better: bool = True,
    priority: int = 2,
    group_label: str = "역대",
) -> Optional[Insight]:
    """기본적인 비교 인사이트를 생성합니다."""
    if current_val is None or stats is None or stats.count < 3:
        return None

    avg = stats.mean
    if avg == 0:
        return None

    diff_pct = (current_val - avg) / abs(avg) * 100
    pct = compute_percentile(stats, current_val)
    rank = compute_rank(stats, current_val, ascending=not higher_is_better)

    quality = _quality_word(diff_pct, higher_is_better)
    current_fmt = format_number(current_val, unit)
    avg_fmt = format_number(avg, unit)

    pp = _postposition(metric_name, ("은", "는"))
    pp_ro = _postposition(current_fmt, ("으로", "로"))
    text = (
        f"이번 전시의 {metric_name}{pp} {current_fmt}{pp_ro}, "
        f"{group_label} 평균({avg_fmt}) 대비 {abs(diff_pct):.1f}% {_direction_verb(diff_pct)} "
        f"({stats.count}개 전시 중 {rank}위)."
    )

    return Insight(
        category=category,
        title=title,
        text=text,
        metric_name=metric_name,
        current_value=current_val,
        reference_avg=avg,
        percentile=pct,
        rank=rank,
        total_count=stats.count,
        priority=priority,
    )


def _make_ratio_insight(
    category: str,
    title: str,
    metric_name: str,
    numerator: float,
    denominator: float,
    ref_ratios: pd.Series,
    unit: str = "",
    higher_is_better: bool = True,
    priority: int = 1,
    group_label: str = "역대",
) -> Optional[Insight]:
    """비율 지표 인사이트를 생성합니다."""
    if (numerator is None or denominator is None
            or denominator == 0 or ref_ratios.dropna().empty):
        return None

    current_ratio = numerator / denominator
    valid = ref_ratios.dropna()
    if len(valid) < 3:
        return None

    avg = float(valid.mean())
    if avg == 0:
        return None

    diff_pct = (current_ratio - avg) / abs(avg) * 100
    quality = _quality_word(diff_pct, higher_is_better)
    current_fmt = format_number(current_ratio, unit)
    avg_fmt = format_number(avg, unit)

    pp = _postposition(metric_name, ("은", "는"))
    text = (
        f"{metric_name}{pp} {current_fmt}으로, "
        f"{group_label} 평균({avg_fmt}) 대비 {abs(diff_pct):.1f}% "
        f"{_direction_verb(diff_pct)} ({quality} 수준)."
    )

    # 백분위 계산
    sorted_vals = sorted(valid.tolist())
    below = sum(1 for v in sorted_vals if v < current_ratio)
    pct = int(below / len(sorted_vals) * 100)

    return Insight(
        category=category,
        title=title,
        text=text,
        metric_name=metric_name,
        current_value=current_ratio,
        reference_avg=avg,
        percentile=pct,
        priority=priority,
    )


# ──────────────────────────────────────────────
# 카테고리별 분석 함수
# ──────────────────────────────────────────────

def _analyze_visitors(current: dict, df: pd.DataFrame, group_label: str = "역대") -> list[Insight]:
    """관객 분석 인사이트"""
    insights = []

    # 총 관객수
    val = current.get("총 관객수")
    if val:
        ins = _make_basic_insight(
            "관객", "총 관객수", "총 관객수", val,
            compute_stats(df, "총 관객수"), unit="명", priority=1,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 일평균 관객수
    val = current.get("일평균 관객수")
    if val:
        ins = _make_basic_insight(
            "관객", "일평균 관객수", "일평균 관객수", val,
            compute_stats(df, "일평균 관객수"), unit="명", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 유료/무료 비율
    paid = current.get("유료 관객수")
    total = current.get("총 관객수")
    if paid and total and total > 0:
        ins = _make_ratio_insight(
            "관객", "유료 관객 비율", "유료 관객 비율",
            paid, total, df["유료_비율"],
            unit="", higher_is_better=True, priority=2,
            group_label=group_label
        )
        if ins:
            # 비율은 퍼센트로 표시 재포맷
            ratio = paid / total
            avg_ratio = float(df["유료_비율"].dropna().mean())
            ins.text = (
                f"유료 관객 비율은 {ratio*100:.1f}%로, "
                f"{group_label} 평균({avg_ratio*100:.1f}%) 대비 "
                f"{abs(ratio - avg_ratio)*100:.1f}%p {'높습니다' if ratio > avg_ratio else '낮습니다'}."
            )
            insights.append(ins)

    # 오프닝 참석
    val = current.get("오프닝 참석 인원")
    if val and val > 0:
        ins = _make_basic_insight(
            "관객", "오프닝 참석", "오프닝 참석 인원", val,
            compute_stats(df, "오프닝 참석 인원"), unit="명", priority=3,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    return insights


def _analyze_budget(current: dict, df: pd.DataFrame, group_label: str = "역대") -> list[Insight]:
    """예산 효율 분석 인사이트"""
    insights = []

    # 총 사용 예산
    val = current.get("총 사용 예산")
    if val:
        ins = _make_basic_insight(
            "예산", "총 사용 예산", "총 사용 예산", val,
            compute_stats(df, "총 사용 예산"), unit="원", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 관객당 비용 (핵심 비율 지표)
    budget = current.get("총 사용 예산")
    visitors = current.get("총 관객수")
    if budget and visitors and visitors > 0:
        ins = _make_ratio_insight(
            "예산", "관객당 비용", "관객당 비용",
            budget, visitors, df["관객당_비용"],
            unit="원", higher_is_better=False, priority=1,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 수입/예산 비율
    revenue = current.get("총수입")
    if budget and revenue and budget > 0:
        ins = _make_ratio_insight(
            "예산", "수입 대비 예산 효율", "수입/예산 비율",
            revenue, budget, df["수입_예산_비율"],
            unit="", higher_is_better=True, priority=1,
            group_label=group_label
        )
        if ins:
            ratio = revenue / budget
            avg_ratio = float(df["수입_예산_비율"].dropna().mean())
            ins.text = (
                f"총수입 대비 예산 비율은 {ratio*100:.1f}%로, "
                f"예산 대비 {ratio*100:.1f}%의 수입을 확보했습니다"
                f" ({group_label} 평균 {avg_ratio*100:.1f}%)."
            )
            insights.append(ins)

    return insights


def _analyze_programs(current: dict, df: pd.DataFrame, group_label: str = "역대") -> list[Insight]:
    """프로그램 밀도 분석 인사이트"""
    insights = []

    # 프로그램 수
    val = current.get("프로그램 총 수")
    if val:
        ins = _make_basic_insight(
            "프로그램", "프로그램 수", "프로그램 수", val,
            compute_stats(df, "프로그램 총 수"), unit="개", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 프로그램 참여 인원
    val = current.get("프로그램 참여 인원")
    if val:
        ins = _make_basic_insight(
            "프로그램", "프로그램 참여 인원", "프로그램 참여 인원", val,
            compute_stats(df, "프로그램 참여 인원"), unit="명", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 프로그램 참여율 (참여인원/총관객)
    participants = current.get("프로그램 참여 인원")
    visitors = current.get("총 관객수")
    if participants and visitors and visitors > 0:
        ins = _make_ratio_insight(
            "프로그램", "프로그램 참여율", "프로그램 참여율(참여인원/총관객)",
            participants, visitors, df["프로그램_참여율"],
            unit="", higher_is_better=True, priority=1,
            group_label=group_label
        )
        if ins:
            ratio = participants / visitors
            avg_ratio = float(df["프로그램_참여율"].dropna().mean())
            ins.text = (
                f"프로그램 참여율(참여인원/총관객)은 {ratio*100:.1f}%로, "
                f"{group_label} 평균({avg_ratio*100:.1f}%) 대비 "
                f"{abs(ratio - avg_ratio)*100:.1f}%p {'높습니다' if ratio > avg_ratio else '낮습니다'}."
            )
            insights.append(ins)

    # 도슨트 참여
    val = current.get("도슨트 참여 인원")
    if val:
        ins = _make_basic_insight(
            "프로그램", "도슨트 참여", "도슨트 참여 인원", val,
            compute_stats(df, "도슨트 참여 인원"), unit="명", priority=3,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    return insights


def _analyze_promotion(current: dict, df: pd.DataFrame, group_label: str = "역대") -> list[Insight]:
    """홍보 효과 분석 인사이트"""
    insights = []

    # 언론 보도 건수
    val = current.get("언론 보도 건수")
    if val:
        ins = _make_basic_insight(
            "홍보", "언론 보도", "언론 보도 건수", val,
            compute_stats(df, "언론 보도 건수"), unit="건", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 보도건당 관객 (관객/보도건수)
    press = current.get("언론 보도 건수")
    visitors = current.get("총 관객수")
    if press and visitors and press > 0:
        ins = _make_ratio_insight(
            "홍보", "보도건당 관객 유입", "보도 1건당 관객",
            visitors, press, df["보도건당_관객"],
            unit="명", higher_is_better=True, priority=1,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # SNS 게시 건수
    val = current.get("SNS 게시 건수")
    if val:
        ins = _make_basic_insight(
            "홍보", "SNS 활동", "SNS 게시 건수", val,
            compute_stats(df, "SNS 게시 건수"), unit="건", priority=3,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    # 뉴스레터 오픈율
    val = current.get("뉴스레터 오픈율")
    if val:
        stats = compute_stats(df, "뉴스레터 오픈율")
        if stats and stats.count >= 3:
            avg = stats.mean
            diff = (val - avg) * 100  # percentage points
            ins = Insight(
                category="홍보",
                title="뉴스레터 오픈율",
                text=(
                    f"뉴스레터 오픈율은 {val*100:.1f}%로, "
                    f"{group_label} 평균({avg*100:.1f}%) 대비 "
                    f"{abs(diff):.1f}%p {'높습니다' if diff > 0 else '낮습니다'}."
                ),
                metric_name="뉴스레터 오픈율",
                current_value=val,
                reference_avg=avg,
                percentile=compute_percentile(stats, val),
                priority=3,
            )
            insights.append(ins)

    return insights


def _analyze_artworks(current: dict, df: pd.DataFrame, group_label: str = "역대") -> list[Insight]:
    """작품 규모 분석 인사이트"""
    insights = []

    val = current.get("출품 작품 수_총")
    if val:
        ins = _make_basic_insight(
            "작품", "출품 작품 수", "출품 작품 수", val,
            compute_stats(df, "출품 작품 수_총"), unit="점", priority=2,
            group_label=group_label
        )
        if ins:
            insights.append(ins)

    return insights


# ──────────────────────────────────────────────
# 유사 전시 비교
# ──────────────────────────────────────────────

COMPARISON_FIELDS = [
    ("총 관객수", "명"),
    ("일평균 관객수", "명"),
    ("총 사용 예산", "원"),
    ("프로그램 총 수", "개"),
    ("언론 보도 건수", "건"),
]


def _build_similar_comparison(
    current: dict, df: pd.DataFrame, top_n: int = 5
) -> tuple[list[SimilarExhibitionRow], Optional[pd.DataFrame]]:
    """유사 전시 비교 데이터 구축"""
    similar_df = get_similar_exhibitions(df, current, top_n=top_n)
    if similar_df.empty:
        return [], None

    rows = []
    for _, row in similar_df.iterrows():
        metrics = {}
        for field, unit in COMPARISON_FIELDS:
            val = row.get(field)
            if pd.notna(val):
                metrics[field] = val
        rows.append(SimilarExhibitionRow(
            title=row["전시 제목"],
            similarity=row.get("_similarity_score", 0),
            metrics=metrics,
        ))

    # 비교표 DataFrame 생성 (보고서 삽입용)
    table_data = {"전시명": [current.get("전시 제목", "현재 전시")]}
    for field, unit in COMPARISON_FIELDS:
        val = current.get(field)
        table_data[field] = [format_number(val, unit) if val else "—"]

    for sim in rows:
        table_data["전시명"].append(sim.title)
        for field, unit in COMPARISON_FIELDS:
            val = sim.metrics.get(field)
            table_data[field].append(format_number(val, unit) if val else "—")

    comparison_df = pd.DataFrame(table_data)
    return rows, comparison_df


def _generate_similar_insight(
    current: dict, similar_rows: list[SimilarExhibitionRow]
) -> Optional[Insight]:
    """유사 전시와의 비교 요약 인사이트 생성"""
    if not similar_rows:
        return None

    names = [r.title for r in similar_rows[:3]]
    names_str = ", ".join(f"《{n}》" for n in names)

    # 총 관객수 비교
    current_visitors = current.get("총 관객수")
    if current_visitors:
        sim_visitors = [
            r.metrics["총 관객수"]
            for r in similar_rows
            if "총 관객수" in r.metrics
        ]
        if sim_visitors:
            avg_visitors = sum(sim_visitors) / len(sim_visitors)
            diff_pct = (current_visitors - avg_visitors) / avg_visitors * 100

            text = (
                f"유사 규모 전시({names_str}) 대비 "
                f"총 관객수가 {abs(diff_pct):.1f}% "
                f"{'높습니다' if diff_pct > 0 else '낮습니다'} "
                f"(유사 전시 평균 {format_number(avg_visitors, '명')}, "
                f"이번 전시 {format_number(current_visitors, '명')})."
            )

            return Insight(
                category="유사전시",
                title="유사 전시 비교",
                text=text,
                metric_name="유사전시 대비 관객수",
                current_value=current_visitors,
                reference_avg=avg_visitors,
                priority=1,
            )
    return None


# ──────────────────────────────────────────────
# 교차 인사이트 (지표 간 관계 서사)
# ──────────────────────────────────────────────

def _analyze_cross_metrics(
    current: dict, df: pd.DataFrame, group_label: str = "역대"
) -> list[Insight]:
    """
    여러 지표를 교차 분석하여 관계성 서사 인사이트를 생성합니다.

    예: "예산은 적었지만 관객 효율은 역대 최고"
    """
    insights = []

    budget = current.get("총 사용 예산")
    visitors = current.get("총 관객수")
    revenue = current.get("총수입")
    press = current.get("언론 보도 건수")
    programs = current.get("프로그램 총 수")
    participants = current.get("프로그램 참여 인원")

    # 필요한 통계
    budget_stats = compute_stats(df, "총 사용 예산")
    visitor_stats = compute_stats(df, "총 관객수")

    def _diff_pct(val, stats):
        if val is None or stats is None or stats.mean == 0:
            return None
        return (val - stats.mean) / abs(stats.mean) * 100

    budget_diff = _diff_pct(budget, budget_stats)
    visitor_diff = _diff_pct(visitors, visitor_stats)

    # ── 1. 예산 vs 관객 효율 ──
    if budget is not None and visitors is not None and budget_diff is not None and visitor_diff is not None:
        cost_per_visitor = budget / visitors if visitors > 0 else None
        cost_stats = compute_stats(df, "관객당_비용") if "관객당_비용" in df.columns else None

        if cost_per_visitor and cost_stats and cost_stats.count >= 3:
            cost_diff = _diff_pct(cost_per_visitor, cost_stats)
            cost_rank = compute_rank(cost_stats, cost_per_visitor, ascending=True)

            # 예산은 적은데 관객이 많은 경우 (효율적)
            if budget_diff < -5 and visitor_diff > 5:
                text = (
                    f"총 사용 예산은 {group_label} 평균 대비 {abs(budget_diff):.0f}% 낮았으나, "
                    f"총 관객수는 오히려 {abs(visitor_diff):.0f}% 높아 "
                    f"관객당 비용 {format_number(cost_per_visitor, '원')}으로 "
                    f"매우 효율적인 운영을 보였습니다 "
                    f"({cost_stats.count}개 전시 중 {cost_rank}위)."
                )
                insights.append(Insight(
                    category="교차분석", title="예산 대비 관객 효율",
                    text=text, metric_name="예산-관객 효율",
                    current_value=cost_per_visitor,
                    reference_avg=cost_stats.mean if cost_stats else None,
                    priority=1,
                ))
            # 예산은 많은데 관객이 적은 경우 (비효율)
            elif budget_diff > 10 and visitor_diff < -5:
                text = (
                    f"총 사용 예산은 {group_label} 평균 대비 {abs(budget_diff):.0f}% 높았으나, "
                    f"총 관객수는 {abs(visitor_diff):.0f}% 낮아 "
                    f"관객당 비용이 {format_number(cost_per_visitor, '원')}에 달했습니다. "
                    f"향후 예산 효율 개선이 필요합니다."
                )
                insights.append(Insight(
                    category="교차분석", title="예산 대비 관객 효율",
                    text=text, metric_name="예산-관객 비효율",
                    current_value=cost_per_visitor,
                    reference_avg=cost_stats.mean if cost_stats else None,
                    priority=1,
                ))

    # ── 2. 홍보(보도) vs 관객 유입 ──
    if press and visitors and press > 0 and visitor_stats and visitor_stats.count >= 3:
        press_stats = compute_stats(df, "언론 보도 건수")
        press_diff = _diff_pct(press, press_stats)

        if press_diff is not None and visitor_diff is not None:
            visitor_per_press = visitors / press

            # 보도는 적은데 관객이 많은 경우
            if press_diff < -10 and visitor_diff > 5:
                text = (
                    f"언론 보도는 {group_label} 평균 대비 {abs(press_diff):.0f}% 적었으나 "
                    f"총 관객수는 {abs(visitor_diff):.0f}% 높아, "
                    f"보도 외 채널(SNS, 구전 등)의 홍보 효과가 컸던 것으로 보입니다."
                )
                insights.append(Insight(
                    category="교차분석", title="홍보 채널 효과",
                    text=text, metric_name="보도-관객 관계",
                    priority=2,
                ))
            # 보도는 많은데 관객이 적은 경우
            elif press_diff > 10 and visitor_diff < -5:
                text = (
                    f"언론 보도는 {group_label} 평균 대비 {abs(press_diff):.0f}% 많았으나 "
                    f"관객 유입으로 충분히 연결되지 않았습니다. "
                    f"보도 건당 관객 {format_number(visitor_per_press, '명')}으로, "
                    f"보도 품질이나 타깃 매체 전략의 재검토가 필요합니다."
                )
                insights.append(Insight(
                    category="교차분석", title="보도 효과 전환",
                    text=text, metric_name="보도-관객 전환율",
                    priority=2,
                ))

    # ── 3. 프로그램 참여 vs 관객 규모 ──
    if participants and visitors and visitors > 0 and visitor_diff is not None:
        participation_rate = participants / visitors
        rate_series = df["프로그램_참여율"].dropna() if "프로그램_참여율" in df.columns else pd.Series()

        if len(rate_series) >= 3:
            avg_rate = float(rate_series.mean())
            rate_diff = (participation_rate - avg_rate) / abs(avg_rate) * 100 if avg_rate != 0 else 0

            # 관객 대비 프로그램 참여가 두드러지게 높은 경우
            if rate_diff > 20:
                text = (
                    f"프로그램 참여율(참여인원/총관객)은 {participation_rate*100:.1f}%로 "
                    f"{group_label} 평균({avg_rate*100:.1f}%)을 크게 상회하여, "
                    f"전시 연계 프로그램이 관객 경험 강화에 효과적으로 기여했습니다."
                )
                insights.append(Insight(
                    category="교차분석", title="프로그램 참여 밀도",
                    text=text, metric_name="프로그램 참여 밀도",
                    current_value=participation_rate,
                    reference_avg=avg_rate,
                    priority=2,
                ))

    # ── 4. 수입 vs 예산 회수율 ──
    if revenue is not None and budget is not None and budget > 0:
        recovery = revenue / budget
        ratio_series = df["수입_예산_비율"].dropna() if "수입_예산_비율" in df.columns else pd.Series()

        if len(ratio_series) >= 3:
            avg_recovery = float(ratio_series.mean())

            if recovery > 1.0 and avg_recovery < 1.0:
                text = (
                    f"총수입({format_number(revenue, '원')})이 총예산({format_number(budget, '원')})을 초과하여 "
                    f"예산 회수율 {recovery*100:.1f}%를 달성했습니다. "
                    f"{group_label} 평균({avg_recovery*100:.1f}%)을 크게 상회하는 수치입니다."
                )
                insights.append(Insight(
                    category="교차분석", title="예산 회수율",
                    text=text, metric_name="예산 회수율",
                    current_value=recovery,
                    reference_avg=avg_recovery,
                    priority=1,
                ))
            elif avg_recovery > 0 and recovery < avg_recovery * 0.5:
                text = (
                    f"예산 회수율은 {recovery*100:.1f}%로, "
                    f"{group_label} 평균({avg_recovery*100:.1f}%)의 절반에 못 미칩니다. "
                    f"수입 구조 다변화를 검토할 필요가 있습니다."
                )
                insights.append(Insight(
                    category="교차분석", title="예산 회수율",
                    text=text, metric_name="예산 회수율",
                    current_value=recovery,
                    reference_avg=avg_recovery,
                    priority=2,
                ))

    return insights


# ──────────────────────────────────────────────
# 메인 분석 함수
# ──────────────────────────────────────────────

def generate_all_insights(
    current_data: dict,
    ref_df: pd.DataFrame,
    exhibition_type=None,
) -> AnalysisResult:
    """
    전체 인사이트를 생성합니다.

    Args:
        current_data: 현재 전시 데이터 (flat dict, 레퍼런스 컬럼명 기준)
        ref_df: 레퍼런스 DataFrame (load_reference로 로드한 것)
        exhibition_type: 전시 유형 (1, 2, 3 등). None이면 전체 비교.

    Returns:
        AnalysisResult: 인사이트 목록 + 유사 전시 비교 데이터
    """
    # 유형 0 제외 후 파생 지표 계산
    df_full = compute_derived_metrics(exclude_type_zero(ref_df))

    # 유형별 필터링 (같은 유형이 3개 미만이면 전체 사용)
    df_typed = filter_by_type(df_full, exhibition_type)
    is_type_filtered = len(df_typed) < len(df_full)

    if is_type_filtered:
        type_label = get_type_label(exhibition_type)
        group_label = f"동일 유형({type_label})"
    else:
        group_label = "역대"

    # 카테고리별 인사이트 생성 (유형 필터링된 데이터로 비교)
    all_insights = []
    all_insights.extend(_analyze_visitors(current_data, df_typed, group_label))
    all_insights.extend(_analyze_budget(current_data, df_typed, group_label))
    all_insights.extend(_analyze_programs(current_data, df_typed, group_label))
    all_insights.extend(_analyze_promotion(current_data, df_typed, group_label))
    all_insights.extend(_analyze_artworks(current_data, df_typed, group_label))

    # 교차 인사이트 (지표 간 관계 서사)
    all_insights.extend(_analyze_cross_metrics(current_data, df_typed, group_label))

    # 유사 전시 비교 (전체 데이터에서 검색)
    similar_rows, comparison_table = _build_similar_comparison(current_data, df_full)
    similar_insight = _generate_similar_insight(current_data, similar_rows)
    if similar_insight:
        all_insights.append(similar_insight)

    # 우선순위로 정렬
    all_insights.sort(key=lambda x: x.priority)

    return AnalysisResult(
        insights=all_insights,
        similar_exhibitions=similar_rows,
        similar_comparison_table=comparison_table,
    )


def get_insights_by_category(result: AnalysisResult) -> dict[str, list[Insight]]:
    """인사이트를 카테고리별로 그룹핑합니다."""
    grouped = {}
    for ins in result.insights:
        if ins.category not in grouped:
            grouped[ins.category] = []
        grouped[ins.category].append(ins)
    return grouped


# ──────────────────────────────────────────────
# 카테고리 표시 순서 및 한국어 라벨
# ──────────────────────────────────────────────

CATEGORY_ORDER = ["관객", "예산", "프로그램", "홍보", "작품", "교차분석", "유사전시"]

CATEGORY_LABELS = {
    "관객": "관객 분석",
    "예산": "예산 효율",
    "프로그램": "프로그램 밀도",
    "홍보": "홍보 효과",
    "작품": "작품 규모",
    "교차분석": "교차 분석 (지표 간 관계)",
    "유사전시": "유사 전시 비교",
}

CATEGORY_ICONS = {
    "관객": "👥",
    "예산": "💰",
    "프로그램": "🎯",
    "홍보": "📢",
    "작품": "🎨",
    "교차분석": "🔗",
    "유사전시": "🔍",
}
