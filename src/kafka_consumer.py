import json
import os
import time
import glob
import pickle
import numpy as np
from kafka import KafkaConsumer

# 설정
KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'sensor-data-stream'
MODEL_DIR = 'models'
LOG_DIR = 'logs'

class AnomalyDetectionConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='anomaly-detection-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.current_model = None
        self.model_path = None
        self.last_model_check = 0
        
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

    def load_latest_model(self):
        """models/ 디렉토리에서 가장 최근의 .pkl 모델을 로드합니다."""
        model_files = glob.glob(os.path.join(MODEL_DIR, "*.pkl"))
        if not model_files:
            if self.current_model is None:
                print(f"[!] No model file (.pkl) found in {MODEL_DIR}. Waiting for model...")
            return False

        latest_model_file = max(model_files, key=os.path.getmtime)
        
        if latest_model_file != self.model_path:
            print(f"[*] New model detected: {latest_model_file}")
            try:
                with open(latest_model_file, 'rb') as f:
                    self.current_model = pickle.load(f)
                self.model_path = latest_model_file
                print(f"[OK] Model loaded: {os.path.basename(latest_model_file)}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to load model: {e}")
                return False
        return False

    def process_message(self, message):
        """수신된 센서 데이터를 처리하고 추론을 수행합니다."""
        data = message.value
        
        # 주기적으로 새 모델 체크 (예: 10초마다)
        current_time = time.time()
        if current_time - self.last_model_check > 10:
            self.load_latest_model()
            self.last_model_check = current_time

        if self.current_model is None:
            # 모델이 없어도 데이터 수신은 기록
            # print(f"📩 데이터 수신 (모델 없음): {data.get('timestamp')}")
            return

        try:
            # 특성 추출 (spectral, process, measurements 모두 포함)
            sensors = data.get('sensors', {})
            feature_vector = []
            for category in ['spectral', 'process', 'measurements']:
                if category in sensors:
                    # 키 순서대로 정렬하여 입력 벡터의 일관성 유지
                    sorted_keys = sorted(sensors[category].keys())
                    feature_vector.extend([float(sensors[category][k]) for k in sorted_keys])
            
            if not feature_vector:
                return

            # 추론 (모델이 sklearn/lightgbm 스타일이라고 가정)
            prediction = self.current_model.predict([feature_vector])[0]
            
            # 결과 출력
            print(f"[Inference] Timestamp: {data.get('timestamp')} | Prediction: {prediction}")
            
            # TODO: 결과 저장 또는 알람 발송 로직 추가
            
        except Exception as e:
            print(f"[ERROR] Error during inference: {e}")

    def run(self):
        print(f"[*] Kafka Consumer starting... (Topic: {TOPIC_NAME})")
        self.load_latest_model()
        
        try:
            for message in self.consumer:
                self.process_message(message)
        except KeyboardInterrupt:
            print("\n[*] Stopping consumer.")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    detector = AnomalyDetectionConsumer()
    detector.run()
