# 2026년 7월 23일 Cloud Run 전환 실행표

## 전환 원칙

- 7월 23일 오후 전까지 `aisajuleehyeon.com`과 `www.aisajuleehyeon.com`은 계속 Cloudtype을 가리킵니다.
- Cloud Run 스테이징, 운영 서비스, 인증서, 로드밸런서를 별도 주소에서 먼저 완성합니다.
- 엔진 결과 전체 해시 4/4, 화면 계약, 생시 미상, 광고·쿠팡 이동 계약 중 하나라도 실패하면 DNS를 바꾸지 않습니다.
- 전환 뒤에도 Cloudtype은 DNS TTL 유예 시간과 진행 중 분석 보호를 위해 7월 24일까지 유지합니다.

## 현재 복구 기준

가비아 DNS에서 현재 두 호스트는 다음 Cloudtype 주소를 가리킵니다.

```text
@    CNAME    mqquvbd6c9bd03f8.sel3.cloudtype.app.    TTL 600
www  CNAME    mqquvbd6c9bd03f8.sel3.cloudtype.app.    TTL 600
```

문제가 생기면 이 두 레코드로 되돌립니다. Cloudtype 서비스 자체는 삭제하거나 중지하지 않습니다.

## 7월 22일 준비

1. Google Cloud 프로젝트를 만들고 결제를 연결합니다.
2. `gcloud auth login`으로 이 컴퓨터를 로그인합니다.
3. 아래 명령을 실행합니다.

```powershell
Set-Location "C:\Users\niceh\OneDrive\문서\사주 운세 서비스 시스템 구축\release_solar_mvp"
Set-ExecutionPolicy -Scope Process Bypass -Force
.\deploy\cloudrun\bootstrap.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\preflight.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\deploy-staging.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\verify-staging.ps1 -ProjectId PROJECT_ID
```

4. 인증서 준비 명령을 실행합니다.

```powershell
.\deploy\cloudrun\prepare-certificate.ps1 -ProjectId PROJECT_ID
```

5. 출력되는 `_acme-challenge...` CNAME 두 개만 가비아에 추가합니다. 이 레코드는 소유권 검증용이며 실제 웹 트래픽을 옮기지 않습니다.
6. 같은 명령을 다시 실행해 인증서가 `ACTIVE`인지 확인합니다.
7. 검증된 스테이징 이미지를 운영 서비스로 그대로 승격하고 로드밸런서를 준비합니다.

```powershell
.\deploy\cloudrun\promote-production.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\prepare-edge.ps1 -ProjectId PROJECT_ID
.\deploy\cloudrun\verify-edge.ps1 -ProjectId PROJECT_ID
```

`verify-edge.ps1`이 통과하기 전에는 가비아의 `@`, `www` 레코드를 변경하지 않습니다.

## 7월 23일 오후 전환

1. Cloudtype `/healthz`에서 `jobs.running`과 `jobs.queued`가 모두 0인지 확인합니다.
2. 60초 뒤 한 번 더 확인해 연속 두 번 0일 때 전환합니다. 이 조건은 진행 중 분석이 DNS 전환 도중 다른 서버로 분리되는 일을 줄입니다.
3. 가비아에서 기존 `@`, `www` Cloudtype CNAME 두 개를 제거합니다.
4. `verify-edge.ps1`이 알려 준 로드밸런서 IP로 다음 A 레코드를 추가합니다.

```text
@    A    LOAD_BALANCER_IP    TTL 300
www  A    LOAD_BALANCER_IP    TTL 300
```

5. DNS가 반영되면 다음을 실행합니다.

```powershell
.\deploy\cloudrun\verify-cutover.ps1 -ProjectId PROJECT_ID
```

6. 모바일에서 입력, 분석 로딩, 쿠팡 이동과 복귀, 7개 총운, 시기운, 올해운, 내년운, 종합 근거를 한 번씩 확인합니다.
7. 최소 30분 동안 오류가 없으면 다음을 실행해 Cloud Run 직접 주소 우회를 막습니다.

```powershell
.\deploy\cloudrun\lock-production.ps1 -ProjectId PROJECT_ID
```

## 즉시 복구 기준

다음 중 하나라도 나타나면 원인 분석보다 DNS 복구를 먼저 합니다.

- Cloud Run `/health` 실패 또는 5xx 반복
- 분석 제출 뒤 3분 이상 완료되지 않음
- Cloudtype과 Cloud Run 결과 해시 불일치
- 종합 근거 누락, 생시 미상인데 시주가 생성됨
- 모바일 쿠팡 복귀 뒤 결과가 사라짐
- 인증서 경고 또는 `www` 접속 실패

가비아에서 A 레코드 두 개를 제거하고 위의 Cloudtype CNAME 두 개를 복원한 뒤 다음을 실행합니다.

```powershell
.\deploy\cloudrun\verify-rollback.ps1
```

## 구조상 남는 한계

현재 분석 작업과 상세 결과는 프로세스 메모리에 있습니다. 따라서 첫 Cloud Run 운영판은 `min=1`, `max=1`, 인스턴스 기반 CPU, 내부 분석 워커 2개로 운용합니다. 엔진과 화면은 그대로 이전되지만 자동 수평 확장은 아직 사용할 수 없습니다. 여러 인스턴스로 확장하려면 작업 상태와 상세 결과를 Firestore·Cloud Tasks·Cloud Storage 같은 외부 저장 계층으로 옮기는 2차 개편이 필요합니다.
