import pandas as pd
import numpy as np
import lightgbm as lgb
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
from lightgbm import early_stopping, log_evaluation

def main():
    df = pd.read_csv("data.csv")

    # Separate features and target
    y = df['y']
    X = df.drop(columns=['y','Unnamed: 0','group_id'])

    print(X.columns)

    # Identify categorical features
    cat_features = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Encode categorical features
    for col in cat_features:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Handle class imbalance with class weights
    class_weights = y_train.value_counts(normalize=True).to_dict()
    sample_weight = y_train.map(lambda x: 1 / class_weights[x])

    # Create LightGBM dataset
    train_data = lgb.Dataset(X_train, label=y_train, weight=sample_weight, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data, categorical_feature=cat_features)

    # Define and train the model
    model = lgb.LGBMClassifier(
        objective='binary',
        metric='auc',
        boosting_type='gbdt',
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        min_data_in_leaf=20,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=5,
        verbosity=-1,
        random_state=42,
        n_estimators=1000
    )

    model.fit(
        X_train, y_train,
        sample_weight=sample_weight,
        eval_set=[(X_test, y_test)],
        eval_metric='auc',
        callbacks=[early_stopping(50), log_evaluation(100)]
    )

    # Make predictions and evaluate
    preds = model.predict(X_test)
    auc_score = roc_auc_score(y_test, preds)
    print(f"Test AUC: {auc_score:.4f}")

    preds = model.predict(X_train)
    auc_score = roc_auc_score(y_train, preds)
    print(f"Train AUC: {auc_score:.4f}")

    # Feature importance analysis
    importance = model.feature_importances_
    feature_names = X.columns
    feature_importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
    feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)

    # Plot feature importance
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance_df['Feature'], feature_importance_df['Importance'])
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title("LightGBM Feature Importance")
    plt.gca().invert_yaxis()
    plt.show()


    # Make predictions and evaluate
    preds = model.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, preds)
    print(f"Test AUC: {auc_score:.4f}")

    # Group-wise selection: Predicting the most likely positive case per group
    if 'group_id' in df.columns:  # Ensure group_id exists
        X_test['group_id'] = df.loc[X_test.index, 'group_id']  # Add back group_id for evaluation
        X_test['probability'] = preds
        X_test['true_label'] = y_test.values  # Ensure true labels are included
        top_per_group = X_test.groupby('group_id', group_keys=False).apply(lambda df: df.nlargest(1, 'probability'))
        correct_selections = (top_per_group['true_label'] == 1).sum()
        total_groups = X_test['group_id'].nunique()
        print(f"Correctly identified positive case in {correct_selections} out of {total_groups} groups.")
        print("Selected top predictions per group:")
        print(top_per_group[['group_id', 'probability', 'true_label']])



if __name__ == "__main__":
    main()