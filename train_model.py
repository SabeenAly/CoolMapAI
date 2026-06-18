import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

# Training data based on published urban heat research
# Features: [current_temp, existing_green_cover_percent, area_density]
# Target: temperature_reduction_per_10_trees

np.random.seed(42)

n_samples = 500
current_temp = np.random.uniform(30, 50, n_samples)
green_cover = np.random.uniform(0, 40, n_samples)
density = np.random.uniform(0.2, 1.0, n_samples)

# Based on research: hotter areas with less green cover get more benefit per tree
temp_reduction_per_10_trees = (
    0.5 + (current_temp - 35) * 0.15
    - green_cover * 0.02
    + density * 0.8
    + np.random.normal(0, 0.3, n_samples)
)
temp_reduction_per_10_trees = np.clip(temp_reduction_per_10_trees, 0.2, 4.0)

X = np.column_stack([current_temp, green_cover, density])
y = temp_reduction_per_10_trees

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

with open('tree_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")
print(f"Sample prediction for temp=47, green=10%, density=0.8:")
sample = model.predict([[47, 10, 0.8]])
print(f"Reduction per 10 trees: {sample[0]:.2f}°C")