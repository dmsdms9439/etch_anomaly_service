# 실시간 센서 데이터 스트리밍 시스템 구조

## 핵심 구성요소

```
┌─────────────────────────────────────────────────────────────────┐
│                     실시간 예지 보전 시스템                        │
└─────────────────────────────────────────────────────────────────┘

1️⃣ 데이터 소스
   └─ Augmented_Sensor_Data_v4.csv (11,550개 샘플)
      └─ 220개 센서 특성
      └─ 21개 결함 클래스

2️⃣ Kafka Producer (kafka_producer.py)
   └─ CSV → JSON 변환
   └─ 실시간/시뮬레이션/배치 모드 지원
   └─ 메시지 압축 (gzip)
   
3️⃣ Kafka Broker (Docker)
   └─ Topic: sensor-data-stream
   └─ 3 파티션 (병렬 처리)
   └─ 24시간 메시지 보관

4️⃣ Kafka Consumer (kafka_consumer.py)
   └─ 실시간 데이터 수신
   └─ 특성 벡터 추출
   └─ 모델 추론 (LightGBM/CatBoost)
   
5️⃣ Detection Agent
   └─ 결함 분류 (F1-score 0.96+)
   └─ 이상 탐지
   
6️⃣ Interpretation Agent (TODO)
   └─ SHAP 분석
   └─ 특성 중요도 계산
   
7️⃣ Prescriptive Agent (TODO)
   └─ LLM 기반 조치 가이드 생성
   └─ 자연어 해석
```

---

## 메시지 플로우

```
CSV Row → JSON → Kafka → Consumer → Model → SHAP → LLM → Action
  ↓         ↓       ↓       ↓         ↓       ↓      ↓      ↓
원본데이터  압축   큐잉    수신    추론   분석   해석   조치권고
```

---

## JSON 메시지 구조

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "metadata": {
    "data_type": "calibration",
    "run_name": "3101",
    "fault_name": "Normal",
    "time_step": 1,
    "time": 15.32,
    "is_synthetic": 0,
    "synthesis_method": "original"
  },
  "sensors": {
    "spectral": {
      "250.0": 1508.3,
      "261.8": 16853.0,
      ... (132개 파장)
    },
    "process": {
      "BCl3_Flow": 751.0,
      "Cl2_Flow": 753.0,
      "RF_Btm_Pwr": 135.0,
      "Pressure": 1263.0,
      "Vat_Valve": 49.0,
      ... (19개 공정 파라미터)
    },
    "measurements": {
      "S1V1": 7.47,
      "S1I1": 0.0040,
      ... (69개 센서 측정값)
    }
  }
}
```

---

## 파일 구조

```
project/
├── src/                    # 소스 코드
│   ├── kafka_producer.py   # CSV → Kafka 스트리밍
│   └── kafka_consumer.py   # Kafka → 실시간 모델 로드 및 추론
├── models/                 # 학습된 모델 및 실시간 수신 모델 (.pkl)
├── data/                   # 데이터 파일 (예: Augmented_Sensor_Data_v4.csv)
├── docs/                   # 시스템 설계 및 구조 문서
│   ├── architecture.md
│   └── STRUCTURE.md
├── scripts/                # 실행 스크립트
│   └── quick_start.sh
├── logs/                   # 실행 로그
├── docker-compose.yml      # Kafka 및 인프라 설정
├── requirements.txt        # Python 의존성
└── README.md               # 프로젝트 메인 가이드
```

---

## 핵심 파라미터

### Producer
- `--mode`: 스트리밍 모드 (realtime/simulation/batch)
- `--interval`: 전송 간격 (초, realtime 모드)
- `--csv`: 데이터 파일 경로
- `--broker`: Kafka 브로커 주소
- `--topic`: Kafka 토픽 이름

### Consumer
- `--model`: 학습된 모델 경로
- `--group`: Consumer 그룹 ID (병렬 처리)
- `--broker`: Kafka 브로커 주소
- `--topic`: 구독할 토픽

---

## 성능 지표

| 항목 | 값 |
|------|------|
| 처리량 | ~10 msg/sec (realtime) |
| 처리량 | ~1000 msg/sec (batch) |
| 지연시간 | < 100ms (추론 포함) |
| 메시지 크기 | ~15KB (압축 전) |
| 메시지 크기 | ~3KB (gzip 압축 후) |

---

## 확장 포인트

### 1. SHAP 분석 추가
```python
# kafka_consumer.py의 process_message()에 추가
def analyze_with_shap(self, message, result):
    import shap
    explainer = shap.TreeExplainer(self.model)
    shap_values = explainer.shap_values(features)
    # 중요 특성 추출
    top_features = get_top_features(shap_values)
    return top_features
```

### 2. LLM Agent 연동
```python
def generate_action_plan(self, message, shap_analysis):
    prompt = f"""
    결함 유형: {result['prediction']}
    주요 원인: Vat Valve ({shap_values['Vat_Valve']:.2f})
    
    조치 방안을 제시하세요.
    """
    response = llm_agent.generate(prompt)
    return response
```

### 3. 알림 시스템
```python
def send_alert(self, result):
    # Slack, Email, SMS 등
    slack.send_message(
        channel="#alerts",
        text=f"🚨 Anomaly: {result['prediction']}"
    )
```

---

## 모니터링

### Kafka UI
- URL: http://localhost:8080
- 메시지 내용 확인
- Consumer Lag 모니터링

### Prometheus + Grafana (선택사항)
```yaml
# docker-compose.yml에 추가
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

---

## 다음 단계

- [ ] LightGBM 모델 학습 및 저장
- [ ] SHAP 분석 통합
- [ ] LLM Agent 개발 (Claude/GPT)
- [ ] 대시보드 구축
- [ ] 알림 시스템 연동
- [ ] 성능 최적화 (배치 처리, 캐싱)
