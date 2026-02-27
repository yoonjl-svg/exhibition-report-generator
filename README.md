# 일민미술관 전시보고서 자동 생성기

웹 폼에 전시 정보를 입력하면 Word(.docx) 보고서를 자동으로 생성하는 도구입니다.

## 기능

- **7단계 입력 폼**: 기본 정보, 전시 주제, 전시 구성, 예산/관객, 홍보/언론, 평가, 보고서 생성
- **차트 자동 생성**: 관객 구성 파이차트, 월별 방문객 바 차트, 예산 비교 차트
- **Word 문서 출력**: 기존 보고서 형식에 맞춘 .docx 파일 생성
- **데이터 저장/불러오기**: JSON으로 입력 데이터 저장 및 재사용

## 보고서 구조 (6개 섹션)

1. **전시 개요** - 전시 제목, 기간, 참여 작가, 기획진, 예산, 관객 수 등
2. **전시 주제와 내용** - 전시 에세이
3. **전시 구성** - 전시실별 정보, 연계 프로그램, 운영인력, 인쇄물
4. **전시 결과** - 예산 집행, 관객 수/수익, 관객 구성 (차트 자동 생성)
5. **홍보 방식 및 언론 보도** - 홍보, 언론보도 리스트, 멤버십
6. **평가 및 개선 방안** - 평가 항목, 관객 후기

## 설치 및 실행

### 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 한글 폰트 설치 (Ubuntu/Debian)
sudo apt-get install fonts-noto-cjk fonts-noto-cjk-extra

# 2-1. 한글 폰트 설치 (macOS)
# brew install --cask font-noto-sans-cjk-kr
# 또는 https://fonts.google.com/noto/specimen/Noto+Sans+KR 에서 다운로드

# 2-2. 한글 폰트 설치 (Windows)
# https://fonts.google.com/noto/specimen/Noto+Sans+KR 에서 다운로드 후 설치

# 3. Streamlit 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 됩니다.

### Streamlit Community Cloud 배포

1. 이 폴더를 GitHub 리포지토리에 업로드합니다
2. [share.streamlit.io](https://share.streamlit.io)에서 배포합니다
3. `packages.txt` 파일이 자동으로 한글 폰트를 설치합니다
4. 팀원들에게 배포된 URL을 공유합니다

## 파일 구조

```
exhibition-report-generator/
├── app.py                 # Streamlit 메인 앱
├── report_generator.py    # Word 보고서 생성 엔진
├── chart_generator.py     # 차트 자동 생성
├── styles.py              # 문서 스타일 정의
├── requirements.txt       # Python 의존성
├── packages.txt           # Streamlit Cloud용 시스템 패키지
├── .streamlit/
│   └── config.toml        # Streamlit 테마 설정
└── README.md              # 이 파일
```

## 사용 방법

1. 각 탭을 순서대로 이동하며 전시 정보를 입력합니다
2. 관객 수 데이터를 입력하면 차트가 자동으로 미리보기됩니다
3. 마지막 '보고서 생성' 탭에서 Word 파일을 다운로드합니다
4. 필요 시 JSON으로 데이터를 저장하여 나중에 다시 불러올 수 있습니다

## 기술 스택

- **Streamlit** - 웹 UI 프레임워크
- **python-docx** - Word 문서 생성
- **matplotlib** - 차트 생성
- **Pillow** - 이미지 처리
