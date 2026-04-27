import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_recall_curve, f1_score, confusion_matrix

# --- 1. 모델 및 데이터 로드 ---
MODEL_DIR = 'models'
ae_data = torch.load(f'{MODEL_DIR}/autoencoder.pth', weights_only=False)
scaler = joblib.load(f'{MODEL_DIR}/scaler.joblib')
FEATURES = ae_data['features']
OLD_THRESHOLD = ae_data['threshold']

class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 16))
        self.decoder = nn.Sequential(nn.Linear(16, 32), nn.ReLU(), nn.Linear(32, 64), nn.ReLU(), nn.Linear(64, input_dim))
    def forward(self, x): return self.decoder(self.encoder(x))

model = Autoencoder(len(FEATURES))
model.load_state_dict(ae_data['model_state_dict'])
model.eval()

print("📊 Validation 데이터셋 분석 중...")
val_df = pd.read_csv('fdata/val_split.csv')
X_scaled = scaler.transform(val_df[FEATURES].fillna(0))
y_true = (val_df['Fault_Name'] != 'Normal').astype(int)

# --- 2. MSE 계산 ---
with torch.no_grad():
    X_tensor = torch.FloatTensor(X_scaled)
    recon = model(X_tensor)
    mse_list = torch.mean((X_tensor - recon)**2, dim=1).numpy()

val_df['mse'] = mse_list

# --- 3. 최적 임계값 검색 ---
# F1-Score를 극대화하는 지점 찾기
precisions, recalls, thresholds = precision_recall_curve(y_true, mse_list)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
best_idx = np.argmax(f1_scores)
BEST_THRESHOLD = thresholds[best_idx]

print(f"✅ 기존 임계값 (Train 95%): {OLD_THRESHOLD:.4f}")
print(f"🚀 최적 임계값 (Val F1-max): {BEST_THRESHOLD:.4f}")

# --- 4. 결과 시각화 ---
plt.figure(figsize=(12, 6))

# Histogram
sns.histplot(data=val_df, x='mse', hue='Fault_Name', element='step', palette='viridis', bins=50)
plt.axvline(OLD_THRESHOLD, color='red', linestyle='--', label=f'Old Threshold ({OLD_THRESHOLD:.3f})')
plt.axvline(BEST_THRESHOLD, color='green', linestyle='-', label=f'Optimized Threshold ({BEST_THRESHOLD:.3f})')

plt.title('Validation MSE Distribution: Normal vs Faults', fontsize=15)
plt.xlabel('Reconstruction Error (MSE)')
plt.ylabel('Frequency')
plt.legend()
plt.yscale('log') # 오차 범위가 클 수 있으므로 로그 스케일 적용
plt.grid(alpha=0.3)

report_path = 'threshold_optimization_report.png'
plt.savefig(report_path)
print(f"📸 분석 결과 도표 저장 완료: {report_path}")

# --- 5. 모델 업데이트 ---
ae_data['threshold'] = BEST_THRESHOLD
torch.save(ae_data, f'{MODEL_DIR}/autoencoder.pth')
print("💾 모델 파일에 최적화된 임계값 업데이트 완료.")

# 성능 지표 출력
y_pred = (mse_list > BEST_THRESHOLD).astype(int)
cm = confusion_matrix(y_true, y_pred)
print("\n[최적화 후 성능 지표]")
print(f"Precision: {precisions[best_idx]:.4f}")
print(f"Recall:    {recalls[best_idx]:.4f}")
print(f"F1-Score:  {f1_scores[best_idx]:.4f}")
print(f"Confusion Matrix:\n{cm}")
