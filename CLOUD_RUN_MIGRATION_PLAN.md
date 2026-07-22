# Google Cloud Run 이전 계획

## 0. 현재 이전 단계

공개 Cloudtype 서버를 중단하지 않고 다음 두 단계로 이전합니다.

1. **병행 스테이징:** 현재 서버를 그대로 컨테이너화해 서울 리전 Cloud Run의 별도 URL에 배포합니다. 프로세스 메모리 상태가 갈라지지 않도록 최소·최대 인스턴스를 모두 1로 고정하고, 비동기 분석이 응답 뒤에도 계속되도록 인스턴스 기반 CPU 할당을 사용합니다.
2. **확장 구조 전환:** 스테이징 결과가 Cloudtype과 정확히 일치한 뒤 Firestore, Cloud Tasks, Cloud Storage로 작업 상태와 결과를 분리합니다. 이 단계가 끝난 뒤에만 여러 web-api와 worker 인스턴스로 확장합니다.

1단계에서는 공개 도메인, 가비아 DNS, Cloudtype 설정을 변경하지 않습니다. 실제 명식 4건의 `chart`와 `report` 전체 해시가 일치해야 다음 단계로 진행합니다. 구체적인 실행 명령은 `CLOUD_RUN_DEPLOYMENT.md`에 정리합니다.

## 1. 이전 목표

현재의 분석 품질과 화면 계약을 그대로 유지하면서 다음 문제를 해결합니다.

- 단일 서버 메모리에 의존하는 작업 상태와 결과 캐시
- 유입 급증 시 한 서버에서 길게 대기하는 구조
- 재배포 또는 재시작 시 진행 중 작업이 사라지는 문제
- CPU 사용량과 상관없이 고정되는 서버 비용

## 2. 현재 서비스의 측정 기준

```text
분석 1건: 약 11~14초
분석 결과 JSON: 약 8.3~8.4 MB
동시 분석 워커: 2
4건 동시 요청: 앞의 2건 약 13초, 뒤의 2건 약 23~25초
부모 + 워커 2개 메모리: 약 580 MB
```

따라서 결과 전체를 Firestore 문서 하나에 넣을 수 없습니다. 작업 메타데이터는 Firestore, 압축된 전체 결과는 Cloud Storage에 저장합니다.

## 3. 목표 구조

```text
사용자
  -> Cloud Run web-api
       -> Firestore: 작업 상태, 만료 시각, 결과 위치
       -> Cloud Tasks: 분석 요청 적재
  -> 상태 조회
       -> Firestore
  -> 상세 결과 조회
       -> Cloud Storage의 gzip JSON

Cloud Tasks
  -> 비공개 Cloud Run analysis-worker
       -> 현재 명리 엔진 실행
       -> Cloud Storage 결과 저장
       -> Firestore 완료 상태 기록
```

### web-api

- 정적 페이지와 기존 `/api/judgment`, `/api/judgment-status`, `/api/judgment-detail` 계약을 유지합니다.
- 요청 검증, 작업 식별자 생성, 중복 요청 제거만 담당합니다.
- 분석 계산을 직접 수행하지 않습니다.
- 권장 시작값: `1 vCPU / 512 MiB`, 동시성 `40`, 최소 인스턴스 `1`, 최대 인스턴스 `10`.

### analysis-worker

- 기존 `build_report_payload`를 변경하지 않고 호출합니다.
- 한 컨테이너가 한 번에 분석 1건만 처리합니다.
- 권장 시작값: `2 vCPU / 2 GiB`, 동시성 `1`, 최소 인스턴스 `0`, 최대 인스턴스 `5`, 요청 제한시간 `300초`.
- `PYTHONHASHSEED=0`을 고정합니다.

### Cloud Tasks

- 작업 유실 방지, 재시도, 유입 급증 완충을 담당합니다.
- 최초 설정: 최대 동시 전달 `5`, 초당 전달 `5`, 최대 재시도 `3`.
- 동일 명식 키를 작업 이름에 반영해 중복 등록을 막습니다.

### Firestore

작업 문서에는 다음만 저장합니다.

```text
job_id
payload_hash
status: queued | running | done | error
created_at / started_at / finished_at / expires_at
attempt_count
result_object
error_code
```

원본 생년월일과 이름은 작업 문서 키에 직접 쓰지 않습니다. 만료된 문서는 애플리케이션 정리 작업으로 삭제합니다. Firestore TTL 삭제는 무료 할당량 대상이 아니므로 초기에는 명시적 정리 작업을 사용합니다.

### Cloud Storage

- 분석 결과를 `results/{job_id}.json.gz`로 저장합니다.
- 버킷은 `asia-northeast3`에 두고 공개 액세스를 차단합니다.
- 객체 수명은 기본 30분으로 관리합니다.
- web-api 서비스 계정만 읽고 analysis-worker 서비스 계정만 쓸 수 있게 권한을 분리합니다.

## 4. API 호환 원칙

프런트엔드 코드를 대폭 바꾸지 않기 위해 현재 응답 형식을 유지합니다.

```text
POST /api/judgment
  -> 202 + jobId + queuePosition + estimatedWaitSeconds

GET /api/judgment-status?jobId=...
  -> 202 queued/running 또는 200 initial payload

GET /api/judgment-detail?token=...
  -> 200 complete report
```

브라우저에는 GCS 주소를 직접 노출하지 않고 web-api가 결과를 읽어 전달합니다.

## 5. 컨테이너와 배포 파일

병행 스테이징 단계에서는 다음 파일을 사용합니다.

```text
Dockerfile
.dockerignore
deploy/cloudrun/bootstrap.ps1
deploy/cloudrun/preflight.ps1
deploy/cloudrun/deploy-staging.ps1
deploy/cloudrun/verify-staging.ps1
deploy/cloudrun/pause-staging.ps1
deploy/cloudrun/prepare-certificate.ps1
deploy/cloudrun/promote-production.ps1
deploy/cloudrun/prepare-edge.ps1
deploy/cloudrun/verify-edge.ps1
deploy/cloudrun/verify-cutover.ps1
deploy/cloudrun/verify-rollback.ps1
scripts/cloudrun_parity_check.py
```

확장 구조 단계에서 다음 모듈을 추가합니다.

```text
cloudrun/web_api.py
cloudrun/analysis_worker.py
cloudrun/job_store.py
cloudrun/result_store.py
cloudrun/task_queue.py
deploy/cloudrun/deploy-production-scalable.ps1
```

엔진 모듈을 따로 복제하지 않고 현재 패키지를 같은 커밋과 이미지에서 사용합니다. 특히 `saju_analysis_engine/data/명리 핵심어 파일 2`의 Markdown 원문과 JSONL·CSV 자료를 컨테이너에 모두 포함합니다.

## 6. 첫째 날 작업

1. 현재 API의 저장소 인터페이스를 `in-memory`와 `Firestore/GCS` 구현으로 분리합니다.
2. 분석 실행 함수를 비공개 worker HTTP 엔드포인트로 이동합니다.
3. Cloud Tasks enqueue와 OIDC 인증을 연결합니다.
4. Docker 이미지를 만들고 로컬에서 엔진 회귀 테스트를 실행합니다.
5. 서울 리전 스테이징 서비스를 생성합니다.
6. 동일 명식 반복 요청, 생시 모름, 동시 10건, worker 재시도 테스트를 수행합니다.

## 7. 둘째 날 작업

1. 스테이징에서 실제 모바일 광고 방문·복귀 흐름을 확인합니다.
2. 20건 동시 요청 부하 시험으로 완료율, p50, p95, 비용 추정치를 기록합니다.
3. 최소 인스턴스와 최대 worker 수를 조정합니다.
4. 사용자 도메인 전환 전 Cloudtype과 Cloud Run 결과 해시 및 화면을 비교합니다.
5. DNS TTL을 낮추고 새 서비스로 트래픽을 전환합니다.
6. 2시간 동안 Cloudtype을 롤백 대상으로 유지합니다.
7. 이상이 없으면 Cloudtype 자동 배포를 중지하되 즉시 재가동 가능한 상태로 보관합니다.

## 8. 도메인 전환

Cloud Run의 직접 도메인 매핑은 제한된 리전에서만 제공되고 공식 문서에서도 운영용으로 권장되지 않습니다. 서울 리전 서비스에는 글로벌 외부 Application Load Balancer를 앞에 두는 방식을 기본안으로 사용합니다.

```text
aisajuleehyeon.com
  -> Google-managed HTTPS certificate
  -> Global external Application Load Balancer
  -> Serverless NEG
  -> Cloud Run web-api (asia-northeast3)
```

전환 전 가비아 DNS TTL을 300초로 낮춥니다. 인증서가 활성화된 것을 확인한 뒤 A/AAAA 레코드를 교체하며, `www`는 루트 도메인으로 308 리디렉션합니다.

## 9. 보안과 개인정보

- web-api만 공개하고 analysis-worker는 인증된 Cloud Tasks 호출만 허용합니다.
- 서비스 계정을 web-api, worker, deploy 세 종류로 분리합니다.
- 생년월일이 로그에 남지 않도록 job ID와 해시 앞부분만 기록합니다.
- 결과 객체와 작업 문서는 짧게 보관하고 자동 정리합니다.
- CORS는 현재 도메인만 허용합니다.
- Cloud Armor에서는 비정상 요청 빈도와 대용량 본문을 제한합니다.

## 10. 관측과 경보

다음 지표를 Cloud Monitoring 대시보드에 둡니다.

- web-api 4xx/5xx 비율
- worker 성공률과 재시도 횟수
- 분석 시간 p50/p95
- Cloud Tasks 대기 작업 수와 가장 오래된 작업 나이
- worker 인스턴스 수, CPU, 메모리
- GCS 결과 저장 실패
- 사용자 완료율: 분석 시작 대비 상세 결과 조회 비율

경보 기준은 5xx 2% 초과, worker 실패 3회 연속, 가장 오래된 작업 90초 초과, p95 45초 초과로 시작합니다.

## 11. 출시 승인 기준

아래 조건을 모두 만족해야 도메인을 전환합니다.

```text
엔진 회귀 샘플 전부 통과
기존 화면 섹션과 버튼 전부 유지
생시 모름 시 시주 미생성
20건 동시 요청 완료율 100%
p95 완료 시간 45초 이하
재시도 후 중복 결과 없음
worker 재시작 뒤 작업 상태 복구
쿠팡 방문 및 뒤로가기 복귀 정상
모바일 360/390/430px 화면 이상 없음
Cloudtype으로 5분 이내 롤백 가능
```

## 12. 비용 운영 원칙

Cloud Run은 요청 기반 과금과 scale-to-zero를 우선 사용합니다. 다만 web-api 최소 인스턴스 1개는 첫 화면과 상태 조회 지연을 줄이기 위한 비용입니다. worker는 최소 인스턴스 0으로 시작하고 실제 홍보 유입에서 콜드 스타트가 사용자 경험을 해칠 때만 1로 올립니다.

Cloud Tasks는 월 첫 100만 작업이 무료이며, Firestore 기본 데이터베이스도 일일 무료 할당량이 있습니다. 실제 비용은 분석 건수, worker 실행 시간, 최소 인스턴스 설정, 결과 전송량을 기준으로 이전 직전 가격 계산기에서 다시 산정합니다.
