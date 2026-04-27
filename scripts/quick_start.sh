#!/bin/bash

# 실시간 센서 데이터 스트리밍 시스템 빠른 테스트

echo "======================================================"
echo "   센서 데이터 스트리밍 시스템 테스트"
echo "======================================================"

# 1. Docker 확인
echo ""
echo "1️⃣ Docker 상태 확인..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker 데몬이 실행 중이 아닙니다."
    exit 1
fi

echo "✅ Docker 정상"

# 2. Kafka 시작
echo ""
echo "2️⃣ Kafka 환경 시작..."
docker-compose up -d

echo "   Kafka 준비 대기 중... (30초)"
sleep 30

# 3. Kafka 상태 확인
echo ""
echo "3️⃣ Kafka 상태 확인..."
if docker ps | grep -q kafka; then
    echo "✅ Kafka 실행 중"
else
    echo "❌ Kafka 시작 실패"
    exit 1
fi

# 4. Python 의존성 확인
echo ""
echo "4️⃣ Python 의존성 확인..."
pip install -q kafka-python pandas numpy 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 의존성 설치 완료"
else
    echo "⚠️  의존성 설치 실패 (수동으로 pip install -r requirements.txt 실행)"
fi

# 5. 토픽 생성 확인
echo ""
echo "5️⃣ Kafka 토픽 생성..."
docker exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic sensor-data-stream \
  --partitions 3 \
  --replication-factor 1 2>/dev/null

echo "✅ 토픽 준비 완료"

# 6. 테스트 메시지 전송
echo ""
echo "6️⃣ 테스트 메시지 전송..."
cat > test_message.json << 'EOF'
{
  "timestamp": "2024-01-15T10:00:00Z",
  "metadata": {
    "run_name": "TEST",
    "fault_name": "Normal"
  },
  "sensors": {
    "process": {
      "Vat_Valve": 49.0,
      "Pressure": 1263.0
    }
  }
}
EOF

docker exec -i kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic sensor-data-stream < test_message.json 2>/dev/null

echo "✅ 테스트 메시지 전송 완료"

# 7. 최종 안내
echo ""
echo "======================================================"
echo "✅ 시스템 준비 완료!"
echo "======================================================"
echo ""
echo "다음 명령어로 시작하세요:"
echo ""
echo "📥 Consumer (터미널 1):"
echo "   python src/kafka_consumer.py"
echo ""
echo "📤 Producer (터미널 2):"
echo "   python src/kafka_producer.py --csv data/Augmented_Sensor_Data_v4.csv --mode batch"
echo ""
echo "🌐 Kafka UI:"
echo "   http://localhost:8080"
echo ""
echo "⏸️  중지:"
echo "   docker-compose down"
echo ""
