# Cloud Run 병행 이전 절차

## 원칙

현재 공개 서비스 `https://aisajuleehyeon.com`과 Cloudtype 배포는 그대로 유지합니다. 먼저 서울 리전의 별도 Cloud Run 스테이징 URL에 같은 코드를 올리고, 엔진 결과와 화면 계약을 검증한 뒤에만 도메인 전환을 검토합니다.

현재 서버는 분석 작업 상태와 상세 결과 토큰을 프로세스 메모리에 보관합니다. 따라서 1차 스테이징은 다음 값으로 고정합니다.

```text
리전: asia-northeast3 (서울)
CPU / 메모리: 2 vCPU / 2 GiB
최소 / 최대 인스턴스: 1 / 1
컨테이너 동시성: 20
요청 제한시간: 300초
CPU 할당: 인스턴스 기반(--no-cpu-throttling)
분석 워커: 2
```

`POST /api/judgment`가 `202`를 반환한 뒤에도 백그라운드 분석이 계속되어야 하므로 1차 구조에서는 인스턴스 기반 CPU 할당이 필요합니다. 최대 인스턴스를 1로 두는 이유는 상태 조회나 상세 결과 요청이 다른 인스턴스로 분산되는 것을 막기 위해서입니다.

## 1. 필요한 준비

이 컴퓨터에는 Google Cloud CLI 577.0.0이 설치되어 있습니다. Docker는 필수가 아니며, 이미지는 Cloud Build에서 만듭니다. 현재 남은 계정 준비는 Google Cloud 로그인, 결제가 연결된 프로젝트 선택입니다.

PowerShell에서 다음을 실행합니다.

```powershell
gcloud auth login
gcloud init
```

Google Cloud Console에서 결제가 연결된 프로젝트를 만들거나 기존 프로젝트를 선택합니다. 아래의 `PROJECT_ID`는 프로젝트 이름이 아니라 고유 프로젝트 ID입니다.

## 2. API와 이미지 저장소 준비

저장소 루트에서 다음을 실행합니다.

```powershell
Set-Location "C:\Users\niceh\OneDrive\문서\사주 운세 서비스 시스템 구축\release_solar_mvp"
.\deploy\cloudrun\bootstrap.ps1 -ProjectId PROJECT_ID
```

이 스크립트는 Cloud Run, Cloud Build, Artifact Registry API를 활성화하고 서울 리전에 `aisaju` Docker 저장소를 만듭니다. Cloudtype, 가비아 DNS, 공개 도메인은 건드리지 않습니다.

그 뒤 전체 출시 전 검사를 실행합니다.

```powershell
.\deploy\cloudrun\preflight.ps1 -ProjectId PROJECT_ID
```

이 검사는 소스 상태, 전체 회귀 테스트, 결제 연결, 필수 API, 현재 Cloudtype DNS 복구 기준을 함께 확인합니다.

## 3. 스테이징 배포

```powershell
.\deploy\cloudrun\deploy-staging.ps1 -ProjectId PROJECT_ID
```

실행 결과에 다음과 같은 별도 URL이 표시됩니다.

```text
https://aisaju-leehyeon-staging-....a.run.app
```

이 단계에서도 실제 사용자 도메인의 트래픽은 계속 Cloudtype으로 갑니다.

## 4. 자동 검증

```powershell
.\deploy\cloudrun\verify-staging.ps1 -ProjectId PROJECT_ID
```

검증은 두 단계로 실행됩니다.

1. 스테이징의 첫 화면, 정적 캐시, 분석 API, 알려진 생시와 생시 미상, 7개 총운·시기운·올해운·내년운·종합 근거 계약을 확인합니다.
2. 공개 Cloudtype과 Cloud Run에서 같은 4개 명식을 분석하고 `chart`와 `report` 전체를 정규화한 SHA-256 해시가 같은지 비교합니다.

결과가 다르면 첫 불일치 경로를 출력하고 실패로 종료합니다. 차이가 있는 상태에서는 도메인을 전환하지 않습니다.

검증을 마치고 스테이징을 당장 사용하지 않을 때는 최소 인스턴스를 0으로 낮춰 대기 비용을 막습니다.

```powershell
.\deploy\cloudrun\pause-staging.ps1 -ProjectId PROJECT_ID
```

서비스와 이미지가 삭제되지는 않으며, 다음 요청에서는 콜드 스타트 후 다시 실행됩니다. `deploy-staging.ps1`을 다시 실행하면 검증용 설정인 최소 인스턴스 1로 돌아옵니다.

## 5. 수동 검증

자동 검증을 통과한 뒤 Cloud Run 스테이징 URL에서 다음을 직접 확인합니다.

- 모바일 360px, 390px, 430px 화면
- 생시 입력과 생시 모름
- 쿠팡 방문 후 뒤로가기와 결과 복귀
- Google 웹 전면 광고와 쿠팡 팝업의 중복 여부
- 분야별 총운, 시기운, 올해운, 내년운, 종합 근거 이동
- 종합 근거 전체 출력과 숨은 복사 버튼
- 같은 입력을 반복했을 때 캐시 응답

## 6. 1차 구조의 한계

이 스테이징은 현재 Cloudtype 서버를 그대로 컨테이너화한 과도기 구조입니다. 인스턴스가 재시작되면 진행 중인 메모리 작업이 사라질 수 있고, 최대 인스턴스를 1보다 크게 늘릴 수 없습니다. 따라서 공개 전환 전후의 짧은 과도기에는 쓸 수 있지만, 유입 증가에 맞춰 자동 확장하는 최종 구조는 아닙니다.

최종 구조에서는 다음을 분리합니다.

```text
Cloud Run web-api -> Firestore 작업 상태
Cloud Tasks -> 비공개 analysis-worker
Cloud Storage -> 압축된 상세 결과
```

이 분리를 마친 뒤 web-api와 worker를 각각 확장해야 합니다.

## 7. 도메인과 인증서

서울 리전 `asia-northeast3`은 Cloud Run의 간편 도메인 매핑 지원 리전이 아닙니다. 또한 해당 기능 자체가 Preview이며 운영용으로 권장되지 않습니다. 따라서 외부 글로벌 HTTPS 로드밸런서, 서버리스 NEG, Certificate Manager DNS 인증을 사용합니다.

DNS 인증은 `_acme-challenge` CNAME만 먼저 추가하므로 기존 Cloudtype 트래픽을 유지한 채 인증서를 `ACTIVE`로 만들 수 있습니다.

```powershell
.\deploy\cloudrun\prepare-certificate.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\promote-production.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\prepare-edge.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\verify-edge.ps1 -ProjectId PROJECT_ID
```

실제 전환 순서와 복구 기준은 `CLOUD_RUN_CUTOVER_2026-07-23.md`를 따릅니다.

## 8. 전환 승인 조건

아래 조건을 모두 통과하기 전에는 DNS를 변경하지 않습니다.

- 로컬 회귀 검사 전부 통과
- 스테이징 운영 검사 전부 통과
- Cloudtype과 Cloud Run 결과 해시 4/4 일치
- 모바일 핵심 화면 이상 없음
- 쿠팡 방문·복귀 정상
- 광고 중복 노출 없음
- 분석 실패와 장기 고착 없음
- Cloudtype으로 즉시 되돌릴 롤백 절차 확인
- Google 관리 인증서 `ACTIVE`
- DNS 전환 전 로드밸런서 강제 해석 검사 통과
- 전환 직전 Cloudtype의 `jobs.running=0`, `jobs.queued=0` 연속 2회 확인

도메인 전환은 별도 작업으로 진행하며, 이 문서의 스테이징 스크립트에는 DNS나 프로덕션 서비스 변경 명령이 들어 있지 않습니다.
