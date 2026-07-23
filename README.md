# AI 사주 : 이현

양력 입력을 기준으로 사주 분석 결과를 제공하는 MVP 출시본입니다.

## 실행

```bash
python -m saju_web.app
```

로컬에서 특정 포트를 지정하려면 다음처럼 실행합니다.

```bash
python -m saju_web.app --host 127.0.0.1 --port 8765
```

호스팅 환경에서는 `PORT` 환경변수를 자동으로 읽습니다.

## 로컬 검증

현재 상품 계약과 엔진 근거 보존 회귀 검사는 다음 명령으로 실행합니다.

```bash
python -m unittest tests.test_release_contract -v
```

서버를 켠 뒤 다음 명령으로 출시본이 정상 응답하는지 확인합니다.

```bash
python scripts/operational_check.py http://127.0.0.1:8775 --concurrency 2
```

서버 검증 항목은 다음과 같습니다.

- 첫 화면 HTML 응답
- 분석 API와 상세 결과 응답
- 양력 입력 정상 처리
- 7개 분야별 총운, 시기운, 올해운, 내년운, 종합 근거 계약
- 알려진 생시와 생시 미상 처리

## 서버 배포

공개 서비스는 Google Cloud Run과 Google Cloud HTTPS 로드밸런서로 운영합니다. 현재 애플리케이션은 `/api/judgment`에서 서버 분석을 생성하므로 정적 호스팅만으로는 실행할 수 없습니다.

스테이징 배포, 0% 트래픽 후보 검증, 무중단 운영 승격, Cloud Run 리비전 복구 절차는 `CLOUD_RUN_DEPLOYMENT.md`를 확인합니다.

## 출시 범위

- 양력 생년월일 입력
- 태어난 시간 지지 선택
- 성별 선택
- 사주 유형 분석 화면
- 만세력 기반 사주 산출
- 성격, 재물, 직업, 연애, 결혼, 명예, 대인관계 총운
- 시기운, 올해운, 내년운, 종합 근거

음력 입력은 이번 MVP 출시본에서 제외했습니다.
