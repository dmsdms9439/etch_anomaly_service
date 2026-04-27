import json
import random
from datetime import datetime
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 220개 특성 생성
spectral = {str(250 + i * 0.5): random.uniform(1000, 20000) for i in range(132)}
process = {f"P_{i}": random.uniform(0, 1000) for i in range(19)}
measurements = {f"M_{i}": random.uniform(0, 10) for i in range(69)}

message = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "run_name": "SIM_RUN_001",
    "fault_name": "Normal",
    "sensors": {
        "spectral": spectral,
        "process": process,
        "measurements": measurements
    },
    "is_synthetic": False,
    "synthesis_method": "original"
}

producer.send('sensor-data-stream', value=message)
producer.flush()
print("Sent 220-feature test message.")
