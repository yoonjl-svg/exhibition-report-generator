# 일민미술관 전시보고서 자동 생성 도구

## 프로젝트 개요

일민미술관의 전시 결과보고서를 자동 생성하는 Streamlit 웹 앱.
Streamlit Cloud에 배포 예정 (GitHub 연동).

## 현재 버전: v2

### v1 (완료)
- Streamlit 폼 입력 → python-docx로 Word 보고서 생성
- 8개 탭: 기본정보, 전시주제, 전시구성, 예산/관객, 홍보/언론, 평가, 분석인사이트, 보고서생성
- 차트 생성 (matplotlib): 관객 구성 파이차트, 주간 관객수, 예산 비교

### v2 (구현 완료, 테스트/수정 필요)
v1에 과거 전시 데이터 기반 **자동 비교 분석** 기능을 추가.

핵심 설계 원칙 3가지:
1. **전시 유형별 비교**: 같은 성격의 전시끼리 비교해야 타당한 분석이 나옴
   - 유형 1=정기 기획전(10개), 2=특별전(5개), 3=기타(2개), 0=분석 제외(1개)
   - 유형 0은 모든 분석에서 제외됨 (특수 전시)
   - 유형이 3개 미만이면 전체(유형0 제외) 비교로 자동 전환
2. **교차 인사이트**: 단일 지표가 아닌 지표 간 관계 서사 생성
   - 예: "예산은 적었지만 관객 효율은 역대 최고"
3. **탐색 → 선택 → 생성 워크플로우**: 인사이트를 먼저 탐색하고, 사용자가 선택/수정한 후 보고서에 반영

## 파일 구조

```
exhibition-report-generator/
├── app.py                          # Streamlit 메인 앱 (8개 탭)
├── report_generator.py             # Word 보고서 생성 (python-docx)
├── chart_generator.py              # matplotlib 차트 생성
├── styles.py                       # Word 문서 스타일 (add_bullet_main, add_arrow_note 등)
├── reference_data.py               # [v2] 레퍼런스 데이터 관리
├── analysis_engine.py              # [v2] 비교 분석 엔진
├── exhibition_reference_data.xlsx  # [v2] 과거 18개 전시 데이터 (52컬럼, 유형 분류 포함)
├── requirements.txt                # 의존성 (streamlit, python-docx, matplotlib, pandas, openpyxl, numpy)
├── packages.txt                    # Streamlit Cloud 시스템 패키지
├── .streamlit/config.toml          # Streamlit 테마 설정
└── CLAUDE.md                       # 이 파일
```

## 핵심 모듈 설명

### reference_data.py
- `load_reference()`: Excel Row2=컬럼명, Row3+=데이터 구조로 로드
- `filter_by_type()`: 유형별 필터링 (유형 0 항상 제외)
- `exclude_type_zero()`: 유형 0 전시 제외
- `compute_derived_metrics()`: 파생 지표 계산 (관객당_비용, 수입_예산_비율, 유료_비율, 프로그램_참여율, 보도건당_관객)
- `get_similar_exhibitions()`: 가중 유사도 기반 유사 전시 검색
- `add_exhibition_to_reference()`: 새 전시 데이터를 Excel에 추가
- **중요**: 파생 지표에 자의적 이상값 필터링 없음. 유형 분류로 해결.

### analysis_engine.py
- `generate_all_insights(current_data, ref_df, exhibition_type)`: 메인 진입점
- 7개 카테고리: 관객, 예산, 프로그램, 홍보, 작품, 교차분석, 유사전시
- 교차분석: 예산-관객 효율, 홍보-관객 전환, 프로그램 참여 밀도, 예산 회수율
- `Insight` dataclass: category, title, text, metric_name, priority, selected 등
- 한국어 조사 자동 처리: `_postposition()` 함수 (받침 기반 은/는, 이/가, 으로/로)
- 비교 기준: 평균 사용 (중앙값 아님). 유형 분류가 극단값 문제를 해결하므로 평균이 더 정확.

### styles.py
- `add_bullet_main(doc, label, value, bold_value=False)`: 불릿 포인트
- `add_arrow_note(doc, text)`: "→ text" 형태의 파란색 노트
- `create_table_left_aligned(doc, rows, cols, data, headers, col_widths, first_col_bold)`: 표 생성

## 알려진 이슈 / 향후 작업

- Streamlit Cloud 배포 테스트 필요
- app.py가 73KB로 매우 큼 — 리팩토링 고려
- 유형 3은 2개뿐이라 자체 비교 불가 (전체 비교로 전환됨)
- 레퍼런스 Excel에 새 전시 추가 시 유형 값도 수동 입력 필요
- 보고서 Word 출력물의 분석 섹션 레이아웃 검토 필요

## 스타일 사양 (v1 기준, 반드시 유지해야 할 값)

아래는 v1에서 확정된 Word 보고서 및 차트의 스타일 규격입니다.
v2 수정 작업 시 이 값들이 유실되지 않도록 주의하십시오.

### 1. 폰트 시스템

| 용도 | 폰트 | 크기 |
|------|------|------|
| 한국어(eastAsia) | Noto Sans CJK KR | — |
| 영문(name) | Noto Sans | — |
| 목차 페이지 제목 | — | 16pt |
| 목차 항목 | — | 11pt |
| 대제목 (I. 전시 개요) | bold | 14pt |
| 소제목 (1. 전시) | bold | 12pt |
| 하위 소제목 (1) 1전시실) | bold | 11pt |
| 상세 항목 (① 도면) | bold | 10pt |
| 본문 | — | 10pt |
| 작은 본문 | — | 9pt |
| 표 헤더/셀 | — | 9pt |
| 불릿 (● / -) | — | 10pt |
| 이미지 캡션 | italic, MEDIUM_GRAY | 8pt |
| 페이지 번호 | MEDIUM_GRAY | 9pt |

### 2. 색상 팔레트

| 이름 | 값 | 용도 |
|------|-----|------|
| BLACK | #000000 | 기본 텍스트 |
| DARK_GRAY | #333333 | — |
| MEDIUM_GRAY | #666666 | 캡션, 페이지 번호 |
| LIGHT_GRAY | #BFBFBF | — |
| TABLE_HEADER_BG | #D9D9D9 | 표 헤더 배경 |
| BLUE | #0070C0 | 화살표 주석(→) 텍스트 색 |

### 3. 페이지 설정

- 용지: A4 (21.0cm × 29.7cm)
- 상하좌우 여백: 모두 2.54cm
- 페이지 번호: 우측 하단 (9pt, MEDIUM_GRAY)

### 4. 제목 체계 (계층)

```
I. 대제목  →  14pt bold, space_before=20pt, space_after=10pt, line_spacing=1.3
  1. 소제목  →  12pt bold, space_before=14pt, space_after=6pt, line_spacing=1.3
    1) 하위 소제목  →  11pt bold, space_before=10pt, space_after=4pt, line_spacing=1.3
      ① 상세 항목  →  10pt bold, space_before=8pt, space_after=4pt, line_spacing=1.3
```

- 로마 숫자: ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
- 원문자: ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
- 소제목에 suffix 추가 가능: suffix 부분은 bold=False, 10pt

### 5. 불릿/노트 스타일

**● 메인 불릿** (`add_bullet_main`):
- 형식: `● {label}: {value}` 또는 `● {value}` (label=None일 때)
- space_before=2pt, space_after=2pt, line_spacing=1.4
- left_indent=0.5cm
- ● 및 label: bold, 10pt
- value: bold_value/underline_value 파라미터로 제어
- **특수 용도**: 총예산, 관객수에 bold_value=True, underline_value=True 적용

**- 하위 불릿** (`add_bullet_sub`):
- 형식: `- {text}`
- 10pt, space_before=1pt, space_after=1pt, line_spacing=1.4
- left_indent=1.2cm

**→ 화살표 주석** (`add_arrow_note`):
- 형식: `→ {text}`
- 10pt, BLUE(#0070C0), bold=False
- space_before=2pt, space_after=4pt, line_spacing=1.3
- left_indent=1.0cm

### 6. 표 스타일

**기본 표** (`create_table`):
- 정렬: 표 전체 CENTER, 셀 텍스트 CENTER
- 헤더: 9pt bold, 배경 #D9D9D9, 수직 가운데
- 데이터 셀: 9pt, 수직 가운데
- 셀 여백: space_before=2pt, space_after=2pt
- 테두리: 검정(#000000), 두께 4 (1/8pt 단위), 모든 변 + 내부선

**좌측 정렬 표** (`create_table_left_aligned`):
- 헤더: CENTER (기본 표와 동일)
- 데이터: 첫 열 CENTER, 나머지 열 LEFT
- first_col_bold=True 옵션: 첫 열 bold

**표별 컬럼 너비 (cm)**:

| 표 | 열1 | 열2 | 열3 | 열4 | 열5 |
|----|-----|-----|-----|-----|-----|
| 프로그램 운영 내역 | 2.0 | 5.5 | 2.5 | 1.5 | 4.0 |
| 인쇄물 및 굿즈 | 5.5 | 3.0 | 6.5 | — | — |
| 예산 요약 (계획 대비 집행) | 2.5 | 4.5 | 4.5 | 4.0 | — |
| 예산 상세 집행 내역 | 2.0 | 2.5 | 5.0 | 3.5 | 3.0 |
| 일간지/월간지 보도 | 1.3 | 1.3 | 9.0 | 4.4 | — |
| 온라인 매체 보도 | 1.5 | 1.5 | 7.5 | 5.5 | — |
| 관람객 후기 (긍정/부정) | 1.25 | 11.75 | 2.0 | — | — |
| v2 유사 전시 비교표 | 4.5 | 나머지 균등분배 (총 15cm) | — | — | — |

### 7. 이미지 크기 및 배치

| 용도 | 최대 너비 | 최대 높이 |
|------|-----------|-----------|
| 단일 이미지 | 10cm | 15cm (세로형 제한) |
| 2열 그리드 이미지 | 6cm | — |
| 차트 이미지 | 10cm | — |
| 포스터 이미지 | 8cm | — |

**자동 배치 규칙** (`add_images_auto`):
- 1개: 중앙 단독 배치
- 2개 이상: 2열 그리드 (테두리 없는 표 사용)
  - 셀 여백: top=0, bottom=0, start=28twips, end=28twips
  - 홀수 개일 때 마지막 1장은 중앙 단독 배치
- 단일 이미지 크기: 원본 비율 유지, 세로형이면 높이 제한(15cm) 적용
- 이미지 문단: CENTER 정렬, space_before=4pt, space_after=4pt

### 8. 보고서 구조 및 페이지 나누기

```
[목차 페이지]        ← 제목 + 수평선 + 목차 + 포스터
--- page break ---
[I. 전시 개요]       ← 불릿 리스트 형식
[II. 전시 주제와 내용] ← 에세이 텍스트 (페이지 나누기 없이 I과 이어짐)
--- page break ---
[III. 전시 구성]     ← 전시실, 프로그램, 인력, 인쇄물
--- page break ---
[IV. 전시 결과]      ← 예산, 관객, 차트
--- page break ---
[V. 홍보 방식 및 언론 보도]
--- page break ---
[VI. 평가 및 개선 방안] ← v2: 1.데이터분석 + 2.평가 / v1: 1.평가만
[끝.]
```

**에세이 텍스트 (섹션 II)**:
- `\n\n`으로 문단 분리
- line_spacing=1.5, first_line_indent=0.5cm, space_after=6pt

**수평선**: color=#AAAAAA, 두께=3 (1/8pt 단위), space_before=1pt, space_after=1pt

**보고서 끝**: "끝." 텍스트, 10pt, LEFT, space_before=12pt

### 9. 차트 스타일 (matplotlib)

**공통**:
- 한글 폰트: Noto Sans CJK 계열 (환경별 자동 탐색, fallback: NanumGothic → malgun.ttf → DejaVu Sans)
- DPI: 200
- 배경: white (facecolor='white')
- 상단/우측 spine 제거
- Y축 grid: alpha=0.3
- 제목: 14pt bold, pad=15~20

**색상 팔레트** (차트용):
```
['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47', '#264478', '#9B59B6']
```

**파이차트** (관객 구성):
- figsize=(6, 5)
- 도넛 스타일: wedge width=0.85, edgecolor='white', linewidth=2
- 레이블: autopct → `{pct:.1f}%\n({absolute:,}명)`, fontsize=9
- 범례: 우측 (bbox_to_anchor=(1, 0, 0.5, 1)), fontsize=9
- 시작각도: 90도

**주별 관객 바차트**:
- figsize=(10, 5)
- 바 색상: #4472C4, width=0.6
- 값 표시: 바 상단, fontsize=9, ha='center'

**예산 비교 차트**:
- figsize=(8, 5)
- 그룹 바: 계획=#4472C4, 집행=#ED7D31, width=0.35
- 금액 표시: 만 단위 변환 (≥10000 → "{val/10000:.0f}만"), fontsize=8

### 10. v2 추가 스타일 (데이터 분석 섹션)

**데이터 기반 분석 (`_sub_data_analysis`)**:
- 소제목: `1. 데이터 기반 분석` (suffix="(과거 전시 비교)")
- 카테고리별 그룹: `● {카테고리명}` (bold_value=True)
- 각 인사이트: `→ {인사이트 텍스트}` (add_arrow_note 사용)
- 유사 전시 비교표: `create_table_left_aligned`, first_col_bold=True

**평가 번호**: 인사이트 있으면 `2. 평가`, 없으면 `1. 평가`

## 개발 환경

- Python 3.10+
- 주요 라이브러리: streamlit, python-docx, matplotlib, pandas, openpyxl, numpy, Pillow
- 배포: Streamlit Cloud (GitHub 연동)
- 한국어 전용 (UI, 보고서, 데이터 모두 한국어)
