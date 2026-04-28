import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv("Combined_Flights_2022.csv")

# Sample 50K rows randomly
df_sample = df.sample(n=50000, random_state=42)

# Clean dataset
df_sample = df_sample[
    (df_sample['AirTime'] > 0) &
    (df_sample['Distance'] > 0) &
    (df_sample['CRSElapsedTime'] > 0) &
    (df_sample['DepDelay'].notnull()) &
    (df_sample['ArrDelay'].notnull())
]

# Select features and target
features = ['DepDelay', 'Distance', 'AirTime', 'CRSElapsedTime', 'TaxiIn', 'TaxiOut']
target = 'ArrDelay'

X = df_sample[features]
y = df_sample[target]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train Random Forest
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluation
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.2f}")
print(f"Mean Absolute Error: {mae:.2f}")
print(f"R^2 Score: {r2:.3f}")

# Plot feature importances
importances = model.feature_importances_
feat_imp = pd.Series(importances, index=features).sort_values(ascending=False)

plt.figure(figsize=(8, 5))
sns.barplot(x=feat_imp, y=feat_imp.index)
plt.title("Feature Importances (Random Forest)")
plt.xlabel("Importance Score")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig("RandomForest_FeatureImportance.png")
plt.show()
