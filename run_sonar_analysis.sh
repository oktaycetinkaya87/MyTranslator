#!/bin/bash

# Renkler
GREEN='\033[0;32m'
Blue='\033[0;34m'
NC='\033[0m' # No Color

# Token repoda tutulmaz; çalıştırmadan önce ortam değişkeni olarak verin.
: "${SONAR_TOKEN:?SONAR_TOKEN ortam değişkenini ayarlayın}"

echo -e "${Blue}🚀 SonarQube Analizi Başlatılıyor...${NC}"

# 1. SonarQube Sunucusunu Başlat
if [ ! "$(docker ps -q -f name=sonarqube)" ]; then
    if [ "$(docker ps -aq -f name=sonarqube)" ]; then
        echo "🔄 Mevcut SonarQube konteyneri başlatılıyor..."
        docker start sonarqube
    else
        echo "🆕 Yeni SonarQube konteyneri oluşturuluyor..."
        docker run -d --name sonarqube -p 9000:9000 sonarqube:community
    fi
else
    echo "✅ SonarQube zaten çalışıyor."
fi

# 2. Sunucunun hazır olmasını bekle
echo "⏳ Sunucunun hazır olması bekleniyor (Bu işlem biraz sürebilir)..."
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do
  printf '.'
  sleep 5
done
echo -e "\n✅ SonarQube Sunucusu Hazır!"

# 3. Şifreyi Değiştir (Zorunlu)
echo -e "${Blue}🔑 Varsayılan şifre güncelleniyor...${NC}"
# curl -s -u admin:admin -X POST "http://localhost:9000/api/users/change_password?login=admin&previousPassword=admin&password=AdminPassword123!" > /dev/null

# 4. Analizi Başlat
echo -e "${Blue}🔍 Kod Analizi Başlatılıyor...${NC}"

# Mac M1/M2 (ARM64) uyumluluğu için platform belirtilebilir, ancak genellikle otomatik algılanır.
docker run \
    --rm \
    --network host \
    -v "$(pwd):/usr/src" \
    sonarsource/sonar-scanner-cli \
    -Dsonar.projectKey=mytranslator \
    -Dsonar.sources=. \
    -Dsonar.host.url=http://host.docker.internal:9000 \
    -Dsonar.python.coverage.reportPaths=coverage.xml \
    -Dsonar.token="$SONAR_TOKEN"

echo -e "${GREEN}✅ Analiz Tamamlandı!${NC}"
echo -e "📊 Raporu görüntülemek için: http://localhost:9000/dashboard?id=mytranslator"
echo -e "🔑 Giriş: admin / AdminPassword123! (Şifre güncellendi)"
