# Cloudtype 48시간 운영 지침

이 문서는 Cloud Run 이전 전 48시간 동안 공개 서비스를 안정적으로 유지하기 위한 운영 기준입니다.

## 1. 권장 리소스

```text
CPU: 2 vCPU
Memory: 2 GB
Replica: 1
Region: Seoul
Port: 8765
```

현재 작업 상태와 결과 캐시는 프로세스 메모리에 저장됩니다. 따라서 Cloudtype에서는 복제본을 2개 이상 실행하지 않습니다. 복제본을 늘리면 사용자가 요청한 작업과 상태 조회가 서로 다른 복제본으로 전달될 수 있습니다.

## 2. 배포 설정

```text
Repository: nicehodong-tech/release_solar_mvp
Branch: main
Runtime: Python 3.12

Install Command:
python3 -m pip install -r requirements.txt

Build Command:
python3 -m compileall -q saju_web saju_analysis_engine saju_birth_engine scripts

Start Command:
python3 -m saju_web.app --host 0.0.0.0 --port 8765

Health Check Path:
/healthz

Initial Delay Seconds:
45
```

## 3. 환경변수

```text
PYTHONHASHSEED=0
SAJU_ANALYSIS_WORKERS=2
SAJU_JOB_MAX_PENDING=12
SAJU_JOB_STALE_SECONDS=600
SAJU_JOB_ESTIMATED_SECONDS=15
SAJU_JOB_HARD_TIMEOUT_SECONDS=120
SAJU_LOG_LEVEL=INFO
PORT=8765
```

- `PYTHONHASHSEED=0`: 동일 명식의 동률 후보 정렬이 프로세스마다 달라지는 것을 막습니다.
- `SAJU_ANALYSIS_WORKERS=2`: 2 vCPU에서 분석 두 건을 병렬 처리합니다.
- `SAJU_JOB_MAX_PENDING=12`: 과도한 요청을 무한 적재하지 않고 명시적으로 재시도시킵니다.
- `SAJU_JOB_STALE_SECONDS=600`: 중단된 작업 상태를 10분 뒤 새 요청으로 교체할 수 있게 합니다.
- `SAJU_JOB_HARD_TIMEOUT_SECONDS=120`: 단일 분석이 2분 이상 멈추면 헬스체크를 실패시켜 컨테이너 복구를 유도합니다.

## 4. 운영 계약

- 분석 실행 프로세스는 최대 2개입니다.
- 세 번째 요청부터는 서버 내부 대기열에서 순서대로 처리합니다.
- 동시 활성 작업이 12건을 넘으면 HTTP 429와 `Retry-After: 5`를 반환합니다.
- 화면은 대기 순서와 예상 시간을 표시하며, 진행률은 뒤로 움직이지 않습니다.
- 동일 입력의 결과는 압축 캐시에서 재사용합니다.
- 정적 파일은 gzip, ETag, 브라우저 캐시를 사용합니다.
- `/healthz`는 워커 수, 활성 작업, 대기 작업, 최장 실행 시간, 캐시 사용량을 반환합니다.
- 실행 중인 단일 분석이 120초를 넘으면 `/healthz`는 HTTP 503과 `degraded`를 반환합니다.

## 5. 배포 직후 점검

저장소 루트에서 다음 명령을 실행합니다.

```bash
python3 scripts/operational_check.py https://aisajuleehyeon.com --concurrency 2 --timeout 240
```

정상 기준:

```text
ok: true
health.status: healthy
health.analysisWorkers: 2
health.jobs.hardTimeoutSeconds: 120
모든 분석 sections >= 10
모든 분석 factors > 0
known birth time: hour pillar present
unknown birth time: hour pillar absent
staticGzip: true
```

## 6. 48시간 감시 기준

Cloudtype 대시보드와 `/healthz`를 함께 확인합니다.

| 항목 | 정상 | 경고 | 조치 |
| --- | --- | --- | --- |
| 메모리 | 1.2 GB 미만 | 1.5 GB 이상 5분 지속 | 재시작 전 로그와 활성 작업 확인 |
| CPU | 순간 100% 허용 | 90% 이상 10분 지속 | 대기열과 홍보 유입량 확인 |
| 대기 작업 | 0~4 | 8 이상 지속 | 홍보 유입 완화 또는 429 정상 여부 확인 |
| 분석 시간 | 약 10~20초 | 30초 이상 반복 | 오류 로그와 워커 재시작 여부 확인 |
| 5xx | 일시 1건 이하 | 연속 3건 | 직전 배포로 롤백 |

분석 중 CPU 100%는 계산형 서비스에서 정상일 수 있습니다. CPU 수치만 보고 재시작하지 말고 완료 시간과 오류율을 함께 봅니다.

## 7. 장애 대응

1. `/healthz`가 열리는지 확인합니다.
2. `status`, `jobs.running`, `jobs.queued`, `jobs.oldestRunningSeconds`를 확인합니다.
3. `analysis worker pool stopped unexpectedly` 로그가 있으면 Cloudtype에서 서비스 한 번만 재시작합니다.
4. 재시작 후 운영 점검 스크립트를 실행합니다.
5. 같은 장애가 반복되면 현재 배포를 중지하고 직전 Git 커밋으로 롤백합니다.

## 8. 배포 원칙

48시간 동안은 엔진, 지표, 문장, 화면 구조를 바꾸지 않습니다. 긴급 수정은 서버 안정성 또는 명백한 기능 장애에만 한정하며, 수정 뒤 운영 점검과 실제 모바일 화면 확인을 모두 통과해야 합니다.

## 9. 현재 배포 기준

```text
main: c09dea6
운영 안정화: e90d98a
고착 분석 복구: c09dea6
```

배포 직후 `/healthz`가 404이면 새 커밋이 적용되지 않은 것입니다. Cloudtype 배포 이력에서
`c09dea6`을 사용하는지 확인한 뒤 수동 재배포합니다. 문제가 생기면 `a396a6e`로 되돌리는 대신
우선 `e90d98a`를 사용합니다. `e90d98a`에는 계산 격리, 큐, 압축 캐시, 과부하 방어가 모두 포함되어
있고 장기 실행 헬스체크만 빠져 있습니다.
