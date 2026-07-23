# 출시본 구성 메모

이 폴더는 GitHub 업로드와 서버 배포를 위한 양력 전용 MVP 구성입니다.

## 포함

- `saju_web/`: 웹 서버, API 어댑터, 정적 페이지
- `saju_web/static/assets/`: 동양화풍 UI 이미지 자산
- `saju_analysis_engine/`: 사주 분석 엔진
- `saju_analysis_engine/data/`: 엔진 실행에 필요한 JSON, JSONL, CSV 데이터
- `saju_analysis_engine/data/명리 핵심어 파일 2/`: 종합 근거 화면에 그대로 사용하는 검증 원문 17개
- `saju_birth_engine/`: 양력 기준 명식 산출 엔진
- `tests/`: 현재 상품 화면·엔진 근거·연간 지표 계약 회귀 검사
- `Dockerfile`, `.dockerignore`, `.gcloudignore`: Cloud Run 컨테이너와 Cloud Build 전송 계약
- `deploy/cloudrun/`: 스테이징, 0% 트래픽 후보 검증, 동일 이미지 무중단 승격, Cloud Run 리비전 복구 절차
- `scripts/cloudrun_parity_check.py`: 운영·스테이징·후보 리비전의 전체 결과 해시 비교
- `CLOUD_RUN_DEPLOYMENT.md`: Cloud Run 단독 운영과 배포 실행표
- `web_app.py`: 로컬 실행용 진입점
- `Procfile`, `render.yaml`, `runtime.txt`: 서버 배포 준비 파일

## 제외

- 개발 보고서와 작업 메모
- PDF 원자료
- 임시 JSON, 임시 스크린샷, 브라우저 프로필
- 테스트 캐시와 `__pycache__`
- 실험용 HTML과 레거시 콘셉트 페이지

## 출시 정책

이번 MVP는 양력 입력만 지원합니다.

음력 변환은 원본 엔진에 남아 있으나 Windows PowerShell/.NET 의존성이 있으므로, 서버 배포용 출시본에서는 입력 단계에서 제외했습니다.
