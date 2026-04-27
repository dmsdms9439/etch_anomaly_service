"""
Kafka Producer: CSV 데이터를 실시간으로 Kafka에 전송

실행 예시:
  python kafka_producer.py --mode realtime --interval 0.1
  python kafka_producer.py --mode simulation  # Time 컬럼 기반
  python kafka_producer.py --mode batch       # 테스트용 빠른 전송
"""

import pandas as pd
import json
import time
from datetime import datetime
from kafka import KafkaProducer
import argparse
from typing import Dict, Any


class SensorDataProducer:
    def __init__(self, 
                 bootstrap_servers='localhost:9092',
                 topic='sensor-data-stream'):
        """
        Kafka Producer 초기화
        
        Args:
            bootstrap_servers: Kafka 서버 주소
            topic: Kafka 토픽 이름
        """
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',  # 데이터 압축
            max_request_size=10485760  # 10MB (대용량 메시지 허용)
        )
        self.topic = topic
        
    def row_to_json(self, row: pd.Series) -> Dict[str, Any]:
        """
        CSV row를 JSON 형식으로 변환
        
        Args:
            row: DataFrame의 한 행
            
        Returns:
            JSON 형식 딕셔너리
        """
        # 센서 데이터 추출 (숫자형 컬럼만)
        sensor_columns = row.index[row.index.str.match(r'^\d+\.?\d*')]
        spectral_data = {col: float(row[col]) for col in sensor_columns}
        
        # 공정 파라미터 추출
        process_params = {
            'BCl3_Flow': float(row['BCl3 Flow']),
            'Cl2_Flow': float(row['Cl2 Flow']),
            'RF_Btm_Pwr': float(row['RF Btm Pwr']),
            'RF_Btm_Rfl_Pwr': float(row['RF Btm Rfl Pwr']),
            'Endpt_A': float(row['Endpt A']),
            'He_Press': float(row['He Press']),
            'Pressure': float(row['Pressure']),
            'RF_Tuner': float(row['RF Tuner']),
            'RF_Load': float(row['RF Load']),
            'RF_Phase_Err': float(row['RF Phase Err']),
            'RF_Pwr': float(row['RF Pwr']),
            'RF_Impedance': float(row['RF Impedance']),
            'TCP_Tuner': float(row['TCP Tuner']),
            'TCP_Phase_Err': float(row['TCP Phase Err']),
            'TCP_Impedance': float(row['TCP Impedance']),
            'TCP_Top_Pwr': float(row['TCP Top Pwr']),
            'TCP_Rfl_Pwr': float(row['TCP Rfl Pwr']),
            'TCP_Load': float(row['TCP Load']),
            'Vat_Valve': float(row['Vat Valve'])
        }
        
        # 센서값 추출 (S1V1, S2I3 등)
        sensor_values = {}
        for col in row.index:
            if col.startswith(('S1', 'S2', 'S3', 'S4')):
                sensor_values[col] = float(row[col])
        
        # 전체 메시지 구성
        message = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': {
                'data_type': row['Data_Type'],
                'run_name': row['Run_Name'],
                'fault_name': row['Fault_Name'],
                'time_step': int(row['Time_Step']),
                'time': float(row['Time']),
                'is_synthetic': int(row['Is_Synthetic']),
                'synthesis_method': row['Synthesis_Method']
            },
            'sensors': {
                'spectral': spectral_data,
                'process': process_params,
                'measurements': sensor_values
            }
        }
        
        return message
    
    def send_message(self, message: Dict[str, Any], key: str = None):
        """
        Kafka로 메시지 전송
        
        Args:
            message: 전송할 메시지
            key: 메시지 키 (파티셔닝용)
        """
        future = self.producer.send(
            self.topic,
            value=message,
            key=key.encode('utf-8') if key else None
        )
        
        # 전송 완료 대기 (선택사항)
        # future.get(timeout=10)
        
    def stream_data(self, 
                    csv_path: str,
                    mode: str = 'realtime',
                    interval: float = 0.1):
        """
        CSV 데이터를 스트리밍
        
        Args:
            csv_path: CSV 파일 경로
            mode: 스트리밍 모드 ('realtime', 'simulation', 'batch')
            interval: 실시간 모드에서 전송 간격 (초)
        """
        print(f"📊 Loading CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        
        print(f"🚀 Starting {mode} streaming...")
        print(f"   Total rows: {total_rows:,}")
        print(f"   Topic: {self.topic}")
        
        prev_time = None
        start_time = time.time()
        
        for idx, row in df.iterrows():
            message = self.row_to_json(row)
            
            # 메시지 키 (같은 Run을 같은 파티션으로)
            key = f"{row['Run_Name']}"
            
            # 전송
            self.send_message(message, key=key)
            
            # 진행 상황 출력
            if (idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed
                print(f"  ✓ Sent {idx+1:,}/{total_rows:,} "
                      f"({(idx+1)/total_rows*100:.1f}%) "
                      f"@ {rate:.1f} msg/sec")
            
            # 모드별 딜레이
            if mode == 'realtime':
                time.sleep(interval)
            elif mode == 'simulation':
                # Time 컬럼 기반 실제 시간차 재현
                if prev_time is not None:
                    time_diff = row['Time'] - prev_time
                    if time_diff > 0:
                        time.sleep(time_diff)
                prev_time = row['Time']
            # batch 모드는 딜레이 없음
        
        # 남은 메시지 전송 완료 대기
        self.producer.flush()
        
        elapsed = time.time() - start_time
        print(f"\n✅ Streaming completed!")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Average rate: {total_rows/elapsed:.1f} msg/sec")
        
    def close(self):
        """Producer 종료"""
        self.producer.close()


def main():
    parser = argparse.ArgumentParser(description='Kafka Sensor Data Producer')
    parser.add_argument('--csv', type=str, 
                       default='Augmented_Sensor_Data_v4.csv',
                       help='CSV file path')
    parser.add_argument('--broker', type=str, 
                       default='localhost:9092',
                       help='Kafka broker address')
    parser.add_argument('--topic', type=str, 
                       default='sensor-data-stream',
                       help='Kafka topic name')
    parser.add_argument('--mode', type=str, 
                       choices=['realtime', 'simulation', 'batch'],
                       default='realtime',
                       help='Streaming mode')
    parser.add_argument('--interval', type=float, 
                       default=0.1,
                       help='Interval between messages in realtime mode (seconds)')
    
    args = parser.parse_args()
    
    producer = SensorDataProducer(
        bootstrap_servers=args.broker,
        topic=args.topic
    )
    
    try:
        producer.stream_data(
            csv_path=args.csv,
            mode=args.mode,
            interval=args.interval
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        producer.close()


if __name__ == '__main__':
    main()
