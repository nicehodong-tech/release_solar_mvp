# Cloud Run 단독 운영 지침

공개 서비스는 Google Cloud Run과 Google Cloud HTTPS 로드밸런서만 사용합니다.

- 프로젝트: `ai-saju-leehyeon`
- 리전: `asia-northeast3`
- 운영 서비스: `aisaju-leehyeon-production`
- 스테이징 서비스: `aisaju-leehyeon-staging`
- 공개 주소: `https://aisajuleehyeon.com`
- 로드밸런서 고정 IP: `136.110.140.162`

## 배포 원칙

1. 로컬 회귀 검사를 통과한 커밋만 배포합니다.
2. Cloud Build에서 컨테이너 이미지를 한 번만 만듭니다.
3. 같은 이미지를 스테이징과 운영 후보 리비전에 사용합니다.
4. 후보 리비전은 트래픽 0% 상태에서 실제 분석과 결과 해시를 검증합니다.
5. 검증을 통과한 후보에만 운영 트래픽 100%를 전환합니다.
6. 전환 후 검증이 실패하면 스크립트가 직전 운영 리비전으로 복구합니다.

## 1. 사전 검사

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
& .\deploy\cloudrun\preflight.ps1 -ProjectId ai-saju-leehyeon
```

검사 범위는 소스 상태, 전체 테스트, 결제, 필수 API, 공개 DNS, 인증서, 운영 상태입니다.

## 2. 스테이징 배포

```powershell
& .\deploy\cloudrun\deploy-staging.ps1 -ProjectId ai-saju-leehyeon
& .\deploy\cloudrun\verify-staging.ps1 -ProjectId ai-saju-leehyeon
```

`verify-staging.ps1`은 운영 서비스와 스테이징의 명식 네 건을 비교합니다. 기존 결과의 전체 해시가 일치하지 않으면 승격하지 않습니다.

## 3. 무중단 운영 승격

```powershell
& .\deploy\cloudrun\promote-production.ps1 -ProjectId ai-saju-leehyeon
```

승격 스크립트는 다음 순서로 작동합니다.

1. 스테이징 재검증
2. 검증된 이미지로 0% 트래픽 후보 리비전 생성
3. 후보 리비전 운영 검사
4. 스테이징과 후보의 결과 해시 비교
5. 후보에 운영 트래픽 100% 전환
6. 공개 도메인 재검증
7. 실패 시 직전 리비전으로 자동 복구

## 4. 공개 경로 검사

```powershell
& .\deploy\cloudrun\verify-edge.ps1 -ProjectId ai-saju-leehyeon
```

다음을 확인합니다.

- 루트 도메인과 `www`가 고정 IP를 가리키는지
- 관리형 인증서가 `ACTIVE`인지
- 두 호스트에서 최신 정적 자산을 제공하는지
- 공개 주소와 Cloud Run 직접 주소의 분석 결과가 일치하는지

## 5. 스테이징 비용 절감

배포 검증이 끝난 뒤 스테이징 최소 인스턴스를 0으로 낮출 수 있습니다.

```powershell
& .\deploy\cloudrun\pause-staging.ps1 -ProjectId ai-saju-leehyeon
```

다음 스테이징 배포 시 최소 인스턴스는 다시 1로 설정됩니다.

## 수동 복구

자동 복구가 실행되지 못한 경우 운영 리비전을 확인합니다.

```powershell
gcloud run revisions list `
  --service aisaju-leehyeon-production `
  --project ai-saju-leehyeon `
  --region asia-northeast3
```

정상 리비전으로 트래픽을 복구합니다.

```powershell
gcloud run services update-traffic aisaju-leehyeon-production `
  --project ai-saju-leehyeon `
  --region asia-northeast3 `
  --to-revisions 정상_리비전_이름=100
```

DNS와 인증서, 로드밸런서는 그대로 유지합니다. 애플리케이션 복구를 위해 DNS를 변경하지 않습니다.
