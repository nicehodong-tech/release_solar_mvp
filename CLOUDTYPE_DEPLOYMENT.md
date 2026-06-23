# Cloudtype 무료 배포 안내

이 문서는 양력 MVP 서비스를 Cloudtype 무료 플랜에 배포하기 위한 기준 절차입니다.

현재 서비스는 외부 DB 없이 Python 서버 하나로 작동합니다. Cloudtype에서는 포트와 시작 명령만 정확히 맞추면 배포할 수 있습니다.

## 1. 배포 기준

```text
저장소: https://github.com/nicehodong-tech/release_solar_mvp
브랜치: main
런타임: Python 3.12
포트: 8765/http
시작 명령: python3 -m saju_web.app --host 0.0.0.0 --port 8765
```

Cloudtype 공식 문서에서는 Python 실행 시 `python`이 아니라 `python3` 명령을 기준으로 안내합니다. 그래서 Cloudtype 설정도 `python3` 기준으로 맞춥니다.

## 2. 대시보드 배포 순서

1. Cloudtype에 로그인합니다.
2. 새 프로젝트 또는 새 서비스를 생성합니다.
3. 템플릿은 `Flask` 또는 Python 계열을 선택합니다.
4. 새 저장소 생성이 아니라, 기존 GitHub 저장소를 선택합니다.
5. 저장소는 `nicehodong-tech/release_solar_mvp`를 선택합니다.
6. 브랜치는 `main`을 선택합니다.
7. 빌드/시작 설정에서 아래 값으로 맞춥니다.

```text
Install Command:
python3 -m pip install -r requirements.txt

Build Command:
python3 -m compileall saju_web saju_analysis_engine saju_birth_engine

Start Command:
python3 -m saju_web.app --host 0.0.0.0 --port 8765

Port:
8765
```

8. 배포를 실행합니다.
9. 배포 로그에서 서버가 정상 시작되는지 확인합니다.
10. 발급된 Cloudtype URL로 접속합니다.

## 3. CLI 또는 설정 파일 기준

저장소에는 아래 설정 파일이 들어 있습니다.

```text
.cloudtype/app.yaml
```

Cloudtype CLI를 사용할 경우 이 설정을 기준으로 배포할 수 있습니다.

```bash
ctype apply
```

처음에는 대시보드 배포가 더 쉽습니다. 이후 자동 배포가 필요해지면 GitHub Actions 또는 Cloudtype CLI로 옮기면 됩니다.

## 4. 배포 후 확인할 것

발급된 URL에서 아래 순서로 확인합니다.

```text
1. 첫 화면이 정상적으로 열리는지
2. 생년월일, 시간, 성별 입력이 가능한지
3. 쿠팡 방문 팝업이 정상적으로 뜨는지
4. 쿠팡 이동 후 돌아왔을 때 분석 결과가 유지되는지
5. 프리미엄 결과 화면의 섹션 버튼이 정상 작동하는지
```

API 직접 확인은 아래처럼 할 수 있습니다.

```bash
curl -X POST "https://발급된주소/api/judgment" \
  -H "Content-Type: application/json" \
  -d '{"birthDate":"19991212","birthTime":"myo","gender":"male","calendarType":"solar","targetYear":2026,"tier":"premium"}'
```

## 5. 문제 발생 시 우선 확인

### 503이 뜨는 경우

포트가 맞지 않는 경우가 가장 흔합니다.

```text
앱 시작 포트: 8765
Cloudtype Port: 8765
```

두 값이 반드시 같아야 합니다.

### 서버가 시작되지 않는 경우

시작 명령이 `python`으로 되어 있으면 `python3`으로 바꿉니다.

```text
python3 -m saju_web.app --host 0.0.0.0 --port 8765
```

### 분석 결과가 늦는 경우

무료 플랜의 자원 제한일 수 있습니다. 우선 같은 요청을 한 번 더 실행해 캐시가 작동하는지 확인합니다. 그래도 느리면 Cloudtype 무료 플랜 한계인지, 엔진 처리 시간이 긴지 따로 분리해서 보아야 합니다.

## 6. 운영 판단

Cloudtype 무료 플랜은 MVP 공개 테스트에 적합합니다.

```text
장점: 국내 서비스, GitHub 연동 쉬움, 무료 테스트 가능
주의: 무료 플랜 자원과 타임아웃 한계, 트래픽 증가 시 유료 전환 가능성
```

따라서 지금 목표는 정식 대규모 운영이 아니라, 먼저 무료로 공개 가능한 URL을 확보하고 실제 사용자 흐름을 검증하는 것입니다.

