#!/usr/bin/env bash
set -euo pipefail

APP_USER="sajuapp"
APP_ROOT="/opt/aisaju-leehyeon/current"
SERVICE_NAME="saju-web"

if [ "$(id -u)" -ne 0 ]; then
  echo "sudo로 실행해야 합니다: sudo ./deploy/oracle/update_app.sh"
  exit 1
fi

if [ ! -d "$APP_ROOT/.git" ]; then
  echo "Git 저장소를 찾을 수 없습니다: $APP_ROOT"
  exit 1
fi

cd "$APP_ROOT"
git fetch origin main
git reset --hard origin/main
chown -R "$APP_USER:$APP_USER" "$APP_ROOT"

sudo -u "$APP_USER" .venv/bin/python -m pip install --upgrade pip
if [ -s requirements.txt ]; then
  sudo -u "$APP_USER" .venv/bin/python -m pip install -r requirements.txt
fi
sudo -u "$APP_USER" .venv/bin/python -m compileall saju_web saju_analysis_engine saju_birth_engine

systemctl restart "$SERVICE_NAME"
systemctl reload nginx

echo "업데이트가 완료되었습니다."
systemctl status "$SERVICE_NAME" --no-pager

