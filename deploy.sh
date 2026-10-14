#!/usr/bin/env bash
set -e

# ==============================================================================
# FastAPI Blog API — Bir buyruqli Avtomatik Deploy Skripti (AWS EC2)
# ==============================================================================

TARGET="${1:-aws-blog}"

if [ "$TARGET" = "aws-ec2" ]; then
    SERVER="aws-ec2"
    IP="3.27.76.136"
else
    SERVER="aws-blog"
    IP="3.27.91.152"
fi

REMOTE_DIR="/var/www/learnfastapi"

echo "🚀 Deploy boshlandi: $SERVER ($IP)"

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

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${IP}/ || echo "000")
if [ "$STATUS" = "200" ]; then
    echo "=========================================================="
    echo "🎉 SERVER BITTA BUYRUQ BILAN YANGILANDI! (Status: $STATUS)"
    echo "🌐 Asosiy API: http://${IP}/ (yoki http://${IP}/learnapi/)"
    echo "📖 Swagger UI: http://${IP}/docs"
    echo "=========================================================="
else
    echo "⚠️ Diqqat: HTTP javob kodi $STATUS bo'ldi. Loglarni tekshiring: ssh ${SERVER} 'journalctl -u learnfastapi -n 20'"
fi
