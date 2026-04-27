# 실시간 센서 데이터 스트리밍 아키텍처

## 시스템 구조

```
┌─────────────────┐
│ CSV Data Source │ (Augmented_Sensor_Data_v4.csv)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Producer  │ → CSV의 각 row를 JSON으로 변환하여 전송
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka Topic    │ (sensor-data-stream)
│  (Message Queue)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Consumer  │ → 실시간으로 데이터 수신
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ML Model Engine │ → LightGBM/CatBoost 추론
│   (LightGBM)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SHAP Agent    │ → 결함 원인 분석
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Agent     │ → 자연어 해석 + 조치 가이드
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │ → 실시간 모니터링
└─────────────────┘
```

## 메시지 형식 (JSON)

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "run_name": "3101",
  "fault_name": "Normal",
  "sensors": {
    "250.0": 1508.3,
    "261.8": 16853.0,
    "BCl3_Flow": 751.0,
    "Cl2_Flow": 753.0,
    "RF_Btm_Pwr": 135.0,
    "Pressure": 1263.0,
    "Vat_Valve": 49.0,
  },
  "is_synthetic": false,
  "synthesis_method": "original"
}
```

## 주요 컴포넌트

1. **Producer**: CSV 데이터를 행 단위로 읽어 Kafka로 전송
2. **Consumer**: Kafka에서 데이터 수신 후 모델 추론
3. **Model Service**: LightGBM 결함 분류 + SHAP 분석
4. **LLM Agent**: 결함 해석 및 조치 가이드 생성

## 스트리밍 주기

- **실시간 모드**: 0.1초 간격 (초당 10개 데이터 포인트)
- **시뮬레이션 모드**: Time 컬럼 기반 실제 시간차 재현
- **배치 모드**: 빠른 테스트용 (딜레이 없음)
