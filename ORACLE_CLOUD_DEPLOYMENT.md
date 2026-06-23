# Oracle Cloud Always Free 배포 안내

이 문서는 양력 MVP 서비스를 Oracle Cloud Always Free 서울 리전에 올리기 위한 기준 절차입니다.

목표 구조는 다음과 같습니다.

```text
사용자 브라우저
→ Oracle Cloud VM 공인 IP
→ Nginx 80/443
→ 127.0.0.1:8765 Python 사주 분석 서버
```

## 1. Oracle 인스턴스 생성 기준

Oracle Cloud Console에서 Compute Instance를 만들 때 아래 기준을 권장합니다.

```text
Region: South Korea Central (Seoul), ap-seoul-1
Image: Ubuntu 24.04 LTS 또는 Ubuntu 22.04 LTS
Shape: VM.Standard.A1.Flex
OCPU: 1 또는 2
Memory: 6GB 이상 권장
Boot Volume: 기본값 또는 50GB 이상
Public IPv4: 활성화
SSH key: 새 키 생성 후 private key 저장
```

Always Free는 계정, 리전, 재고 상태에 따라 생성 가능 여부가 달라질 수 있습니다. A1 Flex 재고가 없으면 같은 서울 리전에서 시간을 두고 다시 시도하는 편이 낫습니다.

## 2. Oracle 네트워크 규칙

VCN의 Security List 또는 Network Security Group에서 아래 포트를 열어야 합니다.

```text
22/tcp   SSH 접속
80/tcp   HTTP 접속
443/tcp  HTTPS 접속
```

처음에는 80번만 열어도 접속 확인이 가능합니다. 도메인 연결 후 HTTPS를 적용할 때 443번을 사용합니다.

## 3. 서버 최초 설치

인스턴스에 SSH로 접속한 뒤 아래 순서로 실행합니다.

```bash
sudo mkdir -p /opt/aisaju-leehyeon
sudo chown -R "$USER:$USER" /opt/aisaju-leehyeon
cd /opt/aisaju-leehyeon
git clone https://github.com/nicehodong-tech/release_solar_mvp.git current
cd current
chmod +x deploy/oracle/install_ubuntu.sh deploy/oracle/update_app.sh
sudo ./deploy/oracle/install_ubuntu.sh
```

설치가 끝난 뒤 브라우저에서 다음 주소로 확인합니다.

```text
http://서버공인IP/
```

## 4. 업데이트 배포

GitHub에 새 버전을 push한 뒤 Oracle 서버에서 아래 명령만 실행하면 됩니다.

```bash
cd /opt/aisaju-leehyeon/current
sudo ./deploy/oracle/update_app.sh
```

## 5. 상태 확인 명령

서비스 상태:

```bash
sudo systemctl status saju-web --no-pager
```

실시간 로그:

```bash
sudo journalctl -u saju-web -f
```

Nginx 상태:

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
```

서버 내부 API 확인:

```bash
curl -I http://127.0.0.1:8765/
```

외부 접속 확인:

```bash
curl -I http://서버공인IP/
```

## 6. 도메인 연결 후 HTTPS

도메인 DNS에서 A 레코드를 Oracle VM의 공인 IP로 연결합니다.

```text
Type: A
Name: @ 또는 원하는 서브도메인
Value: Oracle VM 공인 IP
```

DNS가 전파된 뒤 서버에서 다음 명령을 실행합니다.

```bash
sudo certbot --nginx -d 도메인주소
```

예:

```bash
sudo certbot --nginx -d example.com
```

HTTPS 적용 후에는 아래 주소로 접속합니다.

```text
https://도메인주소/
```

## 7. 운영상 주의

Oracle Always Free는 비용 면에서는 유리하지만, 서버 관리는 직접 해야 합니다.

```text
장점: 무료에 가깝게 장기 운영 가능, 콜드스타트 없음, 한국 리전 사용 가능
주의: SSH 키 보관, 방화벽 설정, 업데이트, 장애 대응은 직접 관리
```

서비스가 실제 유입을 받기 시작하면 최소한 아래 항목은 주기적으로 확인해야 합니다.

```bash
df -h
free -h
sudo journalctl -u saju-web --since "1 hour ago" --no-pager
```

