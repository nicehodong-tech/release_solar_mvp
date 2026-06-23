#!/usr/bin/env bash
set -euo pipefail

APP_USER="sajuapp"
APP_ROOT="/opt/aisaju-leehyeon/current"
APP_PORT="8765"
SERVICE_NAME="saju-web"

if [ "$(id -u)" -ne 0 ]; then
  echo "sudo로 실행해야 합니다: sudo ./deploy/oracle/install_ubuntu.sh"
  exit 1
fi

if [ ! -d "$APP_ROOT" ]; then
  echo "앱 경로를 찾을 수 없습니다: $APP_ROOT"
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git \
  nginx \
  python3 \
  python3-venv \
  python3-pip \
  certbot \
  python3-certbot-nginx \
  curl

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd --system --home /opt/aisaju-leehyeon --shell /usr/sbin/nologin "$APP_USER"
fi

chown -R "$APP_USER:$APP_USER" /opt/aisaju-leehyeon

cd "$APP_ROOT"
sudo -u "$APP_USER" python3 -m venv .venv
sudo -u "$APP_USER" .venv/bin/python -m pip install --upgrade pip
if [ -s requirements.txt ]; then
  sudo -u "$APP_USER" .venv/bin/python -m pip install -r requirements.txt
fi
sudo -u "$APP_USER" .venv/bin/python -m compileall saju_web saju_analysis_engine saju_birth_engine

install -m 0644 deploy/oracle/saju-web.service /etc/systemd/system/${SERVICE_NAME}.service
install -m 0644 deploy/oracle/nginx_saju.conf /etc/nginx/sites-available/saju-web
ln -sfn /etc/nginx/sites-available/saju-web /etc/nginx/sites-enabled/saju-web
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

nginx -t
systemctl enable nginx
systemctl restart nginx

if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 'Nginx Full' || true
fi

echo "설치가 완료되었습니다."
echo "서비스 확인: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "외부 접속: http://서버공인IP/"

