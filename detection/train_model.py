import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

# 1. Load Data
try:
    data = pd.read_csv('hand_data.csv')
except FileNotFoundError:
    print("Error: hand_data.csv not found. Run record_data.py first!")
    exit()

X = data.drop('label', axis=1) # Features (coordinates)
y = data['label']              # Target (Letters)

# 2. Split Data (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train Model
# RandomForest is great for this because it handles messy data well
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 4. Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# 5. Save Model
with open('model.p', 'wb') as f:
    pickle.dump(model, f)

print("Success! Model saved to 'model.p'")
