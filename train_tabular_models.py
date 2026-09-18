import os
import time
import json
import pandas as pd
import numpy as np
import kagglehub
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from imblearn.over_sampling import SMOTE

def categorize_gad7(score):
    if score <= 4: return 0
    elif score <= 9: return 1
    elif score <= 14: return 2
    else: return 3

def categorize_phq9(score):
    if score <= 4: return 0
    elif score <= 9: return 1
    elif score <= 14: return 2
    elif score <= 19: return 3
    else: return 4

def benchmark_tabular():
    print("Downloading datasets via KaggleHub...")
    gad_path = kagglehub.dataset_download('petalme/student-anxiety-dataset')
    phq_path = kagglehub.dataset_download('thedevastator/phq-9-depression-assessment')
    
    anxiety_csv = os.path.join(gad_path, 'anxiety.csv')
    phq9_csv = os.path.join(phq_path, 'Dataset_14-day_AA_depression_symptoms_mood_and_PHQ-9.csv')
    
    print("Loading data...")
    try:
        anxiety_df = pd.read_csv(anxiety_csv, encoding='utf-8')
    except:
        anxiety_df = pd.read_csv(anxiety_csv, encoding='latin-1')
        
    try:
        phq9_df = pd.read_csv(phq9_csv, encoding='utf-8')
    except:
        phq9_df = pd.read_csv(phq9_csv, encoding='latin-1')

    # Prepare GAD-7
    anxiety_df.fillna(anxiety_df.median(numeric_only=True), inplace=True)
    gad_features = ['GAD1', 'GAD2', 'GAD3', 'GAD4', 'GAD5', 'GAD6', 'GAD7']
    # Calculate GAD_T
    anxiety_df['GAD_T'] = anxiety_df[gad_features].sum(axis=1)
    anxiety_df['GAD_CATEGORY'] = anxiety_df['GAD_T'].apply(categorize_gad7)
    
    X_gad = anxiety_df[gad_features]
    y_gad = anxiety_df['GAD_CATEGORY']
    
    # Prepare PHQ-9
    phq_features = ['phq1', 'phq2', 'phq3', 'phq4', 'phq5', 'phq6', 'phq7', 'phq8', 'phq9']
    phq9_clean = phq9_df.dropna(subset=phq_features).copy()
    for col in phq_features:
        phq9_clean[col] = pd.to_numeric(phq9_clean[col], errors='coerce')
    phq9_clean.fillna(phq9_clean[phq_features].median(), inplace=True)
    
    phq9_clean['PHQ_TOTAL'] = phq9_clean[phq_features].sum(axis=1)
    phq9_clean['PHQ_CATEGORY'] = phq9_clean['PHQ_TOTAL'].apply(categorize_phq9)
    
    X_phq = phq9_clean[phq_features]
    y_phq = phq9_clean['PHQ_CATEGORY']

    # SMOTE
    print("Applying SMOTE...")
    smote = SMOTE(random_state=42)
    X_gad_bal, y_gad_bal = smote.fit_resample(X_gad, y_gad)
    X_phq_bal, y_phq_bal = smote.fit_resample(X_phq, y_phq)
    
    scaler_gad = StandardScaler()
    X_gad_scaled = scaler_gad.fit_transform(X_gad_bal)
    scaler_phq = StandardScaler()
    X_phq_scaled = scaler_phq.fit_transform(X_phq_bal)
    
    X_gad_train, X_gad_test, y_gad_train, y_gad_test = train_test_split(X_gad_scaled, y_gad_bal, test_size=0.2, random_state=42)
    X_phq_train, X_phq_test, y_phq_train, y_phq_test = train_test_split(X_phq_scaled, y_phq_bal, test_size=0.2, random_state=42)
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'KNN': KNeighborsClassifier(),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'SVM': SVC(),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
    }

    results = []

    def evaluate_model(name, model, X_train, y_train, X_test, y_test, dataset_name):
        print(f"Training {name} on {dataset_name}...")
        start_train = time.time()
        model.fit(X_train, y_train)
        
        start_inf = time.time()
        y_pred = model.predict(X_test)
        end_inf = time.time()
        
        # Calculate Latency per request in ms
        latency = ((end_inf - start_inf) / len(X_test)) * 1000
        
        acc = accuracy_score(y_test, y_pred) * 100
        prec = precision_score(y_test, y_pred, average='macro', zero_division=0) * 100
        rec = recall_score(y_test, y_pred, average='macro', zero_division=0) * 100
        f1 = f1_score(y_test, y_pred, average='macro', zero_division=0) * 100
        
        results.append({
            'Pipeline': dataset_name,
            'Model': name,
            'Accuracy (%)': f"{acc:.2f}%",
            'Precision (%)': f"{prec:.2f}%",
            'Recall (%)': f"{rec:.2f}%",
            'Macro F1-Score (%)': f"{f1:.2f}%",
            'Latency (ms)': f"{latency:.2f} ms"
        })

    for name, model in models.items():
        evaluate_model(name, model, X_gad_train, y_gad_train, X_gad_test, y_gad_test, "GAD-7 (Anxiety)")
        evaluate_model(name, model, X_phq_train, y_phq_train, X_phq_test, y_phq_test, "PHQ-9 (Depression)")

    with open('tabular_benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    print("\nBenchmark completed. Results saved to tabular_benchmark_results.json")

if __name__ == "__main__":
    benchmark_tabular()
