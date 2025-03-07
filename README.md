![image](https://github.com/user-attachments/assets/dbd711bf-b004-4c38-88ca-d6071473ff1c)


## 🧠 마음챙김 챗봇 (Mindful Chatbot) - 팀 "포옹" 🤗

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/hwkims/phd) <!-- 나중에 CI/CD 설정 후 실제 배지 URL로 변경 -->
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) <!-- 라이선스에 맞게 변경 -->
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![FastAPI Version](https://img.shields.io/badge/fastapi-0.109.0%2B-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI Version](https://img.shields.io/badge/openai-1.0.0%2B-orange.svg)](https://platform.openai.com/docs/guides/gpt)

### 🌟 프로젝트 소개

**"마음챙김 챗봇"** 은 현대인의 정신 건강 문제 해결을 돕기 위해 개발된 AI 기반 심리 상담 챗봇 서비스입니다.  바쁜 일상, 경제적인 부담, 심리적인 장벽 등으로 인해 정신 건강 서비스를 이용하기 어려운 분들에게 24시간 언제 어디서든 쉽고 편하게 접근 가능한 맞춤형 솔루션을 제공합니다.

**주요 특징:**

*   **🗣️ 자연스러운 대화:**  OpenAI의 최신 언어 모델인 **GPT-4o**를 기반으로, 친구와 대화하듯 자연스럽고 편안한 대화를 제공합니다.
*   **🧠 MBTI 기반 심층 분석:**  MBTI 성격 유형 검사를 기반으로 사용자의 4대 기능(관계-정서, 정보-인지, 가치-판단, 실행-관리)과 16가지 세부 지표를 분석하여, 더욱 심층적인 심리 상태를 파악합니다.
*   **📊 개인 맞춤형 조언:**  심리 분석 결과를 바탕으로, 사용자의 특성과 상황에 맞는 개인별 맞춤형 조언과 정보를 제공합니다.
*   **📈 시각화된 분석 결과:**  Chart.js를 활용하여 심리 분석 결과를 보기 쉬운 그래프 형태로 제공하여, 자신의 심리 상태를 한눈에 파악할 수 있습니다.
*   **🏥 주변 병원 정보:**  Leaflet을 이용하여 현재 위치 기반 주변 정신과 병원 정보를 제공합니다. (추후 확장 예정)
*   **💻 웹 기반 서비스:** 별도의 설치 없이 웹 브라우저를 통해 언제 어디서든 접근 가능합니다.
*   **📱 반응형 디자인:** PC, 모바일, 태블릿 등 다양한 기기에서 최적화된 화면을 제공합니다.
*   **🌐 Vultr & DuckDNS:** 클라우드 서버(Vultr)에 배포되어 안정적인 서비스를 제공하고, DuckDNS를 통해 동적 도메인을 사용합니다. (현재 미적용)

### ✨ 기능별 파이프라인

```
[음성 입력 (Web Speech API, STT)] → [텍스트 입력] → [자연어 처리 (OpenAI API, GPT-4o)] →
[챗봇 응답 생성 (OpenAI API, GPT-4o)] → [심리 분석 (MBTI 기반, OpenAI API)] → [대화 요약 (OpenAI API)] →
[결과 시각화 (Chart.js)] → [음성 출력 (OpenAI API, TTS)] → [병원 정보 제공 (Leaflet, 추후 확장)]
```
### 🛠️ 기술 스택

*   **Frontend:**
    *   HTML, CSS, JavaScript
    *   Chart.js (심리 분석 결과 시각화)
    *   Leaflet (지도 기반 병원 정보, 추후 확장)
*   **Backend:**
    *   Python
    *   FastAPI (RESTful API 서버)
*   **AI:**
    *   OpenAI API (GPT-4o, TTS)
*   **Deployment:**
    *    Vultr (클라우드 서버, 현재 미적용)
    *   DuckDNS (동적 DNS, 현재 미적용)

### 🚀 프로젝트 구조

```
phd/
├── backend/         # FastAPI 백엔드 코드
│   ├── main.py      # FastAPI 메인 애플리케이션
│   └── ...
├── frontend/        # 프론트엔드 코드 (HTML, CSS, JavaScript)
│   ├── index.html   # 메인 페이지
│   ├── style.css    # 스타일시트
│   ├── script.js    # 자바스크립트 코드
│   ├── images/      # 이미지 파일 (프로필 이미지 등)
│   └── ...
├── .env             # 환경 변수 파일 (OpenAI API 키 등)
├── requirements.txt # Python 패키지 의존성 목록
└── README.md        # 이 파일
```

### 💻 개발 환경 설정 및 실행 방법

1.  **저장소 복제:**
    ```bash
    git clone https://github.com/hwkims/phd.git
    cd phd
    ```

2.  **Python 가상 환경 설정 (선택 사항이지만 권장):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **필요 패키지 설치:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정:**
    *   `.env` 파일 생성 (backend 폴더 내)
    *   다음 내용 추가 (실제 값으로 변경):
        ```
        OPENAI_API_KEY=your_openai_api_key
        ```

5.  **FastAPI 서버 실행:**
    ```bash
    cd backend
    uvicorn main:app --reload --host=0.0.0.0 --port=8000
    ```
    *   `--reload`: 코드 변경 시 자동 재시작
    *   `--host=0.0.0.0`: 외부 접근 허용
    *    `--port=8000`: 포트 8000 사용

6.  **웹 브라우저에서 접속:**
    *   `http://localhost:8000` 또는 서버 IP 주소와 포트 번호 (예: `http://your_server_ip:8000`)

### 🤝 기여 방법 (Contributing)

프로젝트에 기여하고 싶으신 분들은 다음 가이드라인을 따라주세요:

1.  **Issue 등록:** 버그, 개선 사항, 기능 제안 등을 Issue로 등록해주세요.
2.  **Fork & Clone:** 저장소를 Fork하고, 로컬 환경에 Clone합니다.
3.  **Branch 생성:** 새로운 기능 개발 또는 버그 수정을 위한 Branch를 생성합니다. (예: `feature/new-feature`, `bugfix/fix-bug`)
4.  **코드 작성:** 코드를 작성하고, 변경 사항을 commit합니다. (commit 메시지 규칙 준수)
5.  **Pull Request:** 변경 사항을 main (또는 develop) branch로 Pull Request합니다.
6.  **코드 리뷰:** 코드 리뷰를 통해 코드 품질을 확인하고, 필요한 경우 수정합니다.
7.  **Merge:** 코드 리뷰가 완료되면, 변경 사항이 main branch에 merge됩니다.

### 📝 TODO

*   [ ] 사용자 인증 및 계정 관리 시스템
*   [ ] 대화 기록 저장 및 조회
*   [ ] 음성 인식(STT) 기능 구현
*   [ ] 심리 분석 알고리즘 고도화 및 MBTI 외 다른 심리 검사 도구 연동
*   [ ] 챗봇 페르소나 다양화
*   [ ] 감정 일기 기능
*   [ ] 사용자 맞춤형 추천 활동(명상, 운동 등) 제공
*   [ ] 전문가(심리 상담사) 연계 시스템 구축
*   [ ] Vultr 서버 배포 및 DuckDNS 설정
*   [ ] HTTPS 적용
*   [ ] 테스트 코드 작성 및 CI/CD 구축
*   [ ] 사용자 피드백 기반 지속적인 개선

### 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. ( *`LICENSE` 파일은 아직 없으므로, 필요하다면 추가해야 합니다.*)

### 📞 연락처

*   **개발자:** 김현우 (hwkims@naver.com)
*   **팀:** 포옹

---

**Disclaimer:** 이 챗봇은 심리 상담 전문가를 대체할 수 없으며, 의학적 진단이나 치료를 제공하지 않습니다.  심각한 정신 건강 문제가 있는 경우 반드시 전문가와 상담하세요.
