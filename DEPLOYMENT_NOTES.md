# 배포 메모

## 현재 출시 범위

이번 MVP는 양력 입력만 지원합니다.

음력 변환은 원본 개발본에 남아 있지만, 서버 환경에서 안정적으로 운영하기 전까지 출시본에서는 제외합니다.

## 권장 호스팅

현재 서비스는 정적 페이지가 아니라 Python 서버가 필요합니다.

1차 권장 후보는 Render입니다.

이유는 다음과 같습니다.

- GitHub 저장소 연결이 단순합니다.
- Python Web Service를 바로 실행할 수 있습니다.
- `render.yaml`로 배포 설정을 저장소 안에 둘 수 있습니다.
- 기본 `onrender.com` 주소와 HTTPS를 제공합니다.

대안 후보:

- Render
- Railway
- Fly.io

GitHub Pages는 이번 MVP에 맞지 않습니다.

## 실행 명령

```bash
python -m saju_web.app
```

호스팅 서비스가 `PORT` 환경변수를 제공하면 서버가 자동으로 해당 포트를 사용합니다.

## 배포 후 확인 주소

배포가 끝나면 아래 두 가지를 확인합니다.

```text
/
/api/judgment
```

첫 화면이 열리고, 프리미엄 분석 API가 정상 응답해야 합니다.

## Render 배포 값

Render에서 직접 입력해야 할 경우 아래 값을 사용합니다.

```text
Service Type: Web Service
Repository: https://github.com/nicehodong-tech/release_solar_mvp.git
Branch: main
Runtime: Python
Build Command: python -m compileall saju_web saju_analysis_engine saju_birth_engine
Start Command: python -m saju_web.app
```

## 도메인 연결

Render 서비스가 Live 상태가 된 뒤 진행합니다.

1. Render 서비스의 Settings로 들어갑니다.
2. Custom Domains에서 도메인을 추가합니다.
3. 도메인 구매처 또는 DNS 관리 화면에서 Render가 안내하는 DNS 값을 입력합니다.
4. Render에서 Verify를 누릅니다.
5. HTTPS 인증서가 발급된 뒤 실제 도메인으로 접속합니다.

## 광고 준비

광고 코드는 사이트가 실제 도메인에서 열리고, AdSense 사이트 심사가 시작된 뒤 적용합니다.

현재 단계에서는 광고 코드를 넣지 않습니다.

이유는 다음과 같습니다.

- AdSense의 `ca-pub-...` 값이 아직 없습니다.
- 심사 전 임의 광고 코드를 넣으면 검증이 불가능합니다.
- `ads.txt`도 AdSense가 제시하는 정확한 값이 나온 뒤 추가해야 합니다.

AdSense에서 사이트를 추가한 뒤 제공되는 코드가 나오면 `saju_web/static/index.html`의 `<head>` 안에 넣습니다.
