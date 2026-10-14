#!/usr/bin/env bash
set -e

# ==============================================================================
# FastAPI Blog API — Bir buyruqli Avtomatik Deploy Skripti (AWS EC2)
# ==============================================================================

SERVER="aws-ec2"
REMOTE_DIR="/var/www/learnfastapi"

# 1. Kodlarni serverga sinxronizatsiya qilish
echo "📦 1/3 Fayllar serverga sinxronlashtirilmoqda..."
rsync -avz \
  --exclude="venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".pytest_cache" \
  --exclude=".git" \
  --exclude=".env" \
  ./ ${SERVER}:${REMOTE_DIR}/

# 2. Serverda migratsiyalarni yurgizish va servisni qayta ishga tushirish
echo "🔄 2/3 Serverda paketlar tekshirilib, servis qayta yuklanmoqda..."
ssh ${SERVER} "
  cd ${REMOTE_DIR}
  ${REMOTE_DIR}/venv/bin/pip install -q -r requirements.txt
  ${REMOTE_DIR}/venv/bin/alembic upgrade head
  sudo systemctl restart learnfastapi.service
"

# 3. Yangilangan serverni tekshirish
echo "🔍 3/3 Server tekshirilmoqda..."
sleep 2

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://3.27.76.136/learnapi/ || echo "000")
if [ "$STATUS" = "200" ]; then
    echo "=========================================================="
    echo "🎉 SERVER BITTA BUYRUQ BILAN YANGILANDI! (Status: $STATUS)"
    echo "🌐 Asosiy API: http://3.27.76.136/learnapi/"
    echo "📖 Swagger UI: http://3.27.76.136/learnapi/docs"
    echo "=========================================================="
else
    echo "⚠️ Diqqat: HTTP javob kodi $STATUS bo'ldi. Loglarni tekshiring: ssh aws-ec2 'journalctl -u learnfastapi -n 20'"
fi
