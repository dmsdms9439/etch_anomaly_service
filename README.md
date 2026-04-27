# 실시간 센서 데이터 스트리밍 시스템 실행 가이드

## 빠른 시작 (3단계)

### 1️⃣ Kafka 환경 구축

```bash
# Docker Compose로 Kafka 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# Kafka 준비 확인 (약 30초 소요)
docker logs kafka | grep "started"
```

**접속 주소**:
- Kafka Broker: `localhost:9092`
- Kafka UI: `http://localhost:8080`
- Redis: `localhost:6379`
- PostgreSQL: `localhost:5432`

### 2️⃣ Python 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3️⃣ 실행

**터미널 1: Consumer 시작** (먼저 실행!)
```bash
python kafka_consumer.py --model lightgbm_model.pkl
```

**터미널 2: Producer 시작**
```bash
# 실시간 모드 (0.1초 간격)
python kafka_producer.py --csv Augmented_Sensor_Data_v4.csv --mode realtime --interval 0.1

# 시뮬레이션 모드 (Time 컬럼 기반)
python kafka_producer.py --mode simulation

# 배치 모드 (테스트용 - 딜레이 없음)
python kafka_producer.py --mode batch
```

---

## 실행 예시 출력

### Producer 출력
```
📊 Loading CSV: Augmented_Sensor_Data_v4.csv
🚀 Starting realtime streaming...
   Total rows: 11,550
   Topic: sensor-data-stream
  ✓ Sent 100/11,550 (0.9%) @ 10.2 msg/sec
  ✓ Sent 200/11,550 (1.7%) @ 10.1 msg/sec
  ...
```

### Consumer 출력
```
🎧 Consumer started. Waiting for messages...
   Topic: frozenset({'sensor-data-stream'})
📊 Processed 100 messages (Anomalies: 5 = 5.0%)

🚨 ANOMALY DETECTED!
   Time: 2024-01-15T10:30:45.123Z
   Run: 3101
   Predicted: BCl3 +10
   Actual: BCl3 +10
   Confidence: 98.50%
   Vat Valve: 52.30
   Pressure: 1285.00
```

---

## 모드별 특징

| 모드 | 용도 | 전송 속도 | 특징 |
|------|------|----------|------|
| **realtime** | 실제 운영 시뮬레이션 | 고정 (예: 0.1초) | 일정한 간격으로 전송 |
| **simulation** | 실제 시간 재현 | Time 컬럼 기반 | CSV의 실제 시간차 반영 |
| **batch** | 테스트/검증 | 최대 속도 | 딜레이 없이 즉시 전송 |

---

## 고급 설정

### Consumer 다중 인스턴스 실행 (병렬 처리)

```bash
# Consumer 1
python kafka_consumer.py --model lightgbm_model.pkl --group group-1

# Consumer 2 (다른 터미널)
python kafka_consumer.py --model catboost_model.pkl --group group-2
```

### 특정 토픽에서 읽기

```bash
python kafka_consumer.py \
  --broker localhost:9092 \
  --topic sensor-data-stream \
  --group my-processor \
  --model lightgbm_model.pkl
```

### Producer 커스터마이징

```bash
python kafka_producer.py \
  --csv /path/to/your/data.csv \
  --broker localhost:9092 \
  --topic my-topic \
  --mode realtime \
  --interval 0.05  # 더 빠른 전송 (초당 20개)
```

---

## Kafka UI 사용법

1. 브라우저에서 `http://localhost:8080` 접속
2. **Topics** 메뉴 → `sensor-data-stream` 선택
3. 실시간 메시지 확인 및 모니터링

**확인 가능한 정보**:
- 토픽 메시지 수
- 파티션별 lag
- Consumer 그룹 상태
- 메시지 내용 (JSON)

---

## 문제 해결

### Kafka 연결 실패
```bash
# Kafka 상태 확인
docker logs kafka

# 재시작
docker-compose restart kafka
```

### Consumer가 메시지를 받지 못함
```bash
# offset 리셋 (처음부터 읽기)
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group sensor-processor --reset-offsets --to-earliest \
  --topic sensor-data-stream --execute
```

### 메모리 부족 (대용량 데이터)
```bash
# Producer 배치 크기 조정
# kafka_producer.py 에서 max_request_size 증가

# Consumer 폴링 개수 조정
# kafka_consumer.py 에서 max_poll_records 감소
```

---

## 다음 단계

1. **SHAP 분석 통합**: Consumer에 SHAP 분석 로직 추가
2. **LLM Agent 연동**: 결함 해석 및 조치 가이드 생성
3. **대시보드 구축**: Grafana + Prometheus로 실시간 모니터링
4. **알림 시스템**: 이상 감지 시 Slack/이메일 알림

---

## 정리

```bash
# 모든 서비스 종료
docker-compose down

# 데이터까지 삭제
docker-compose down -v
```
