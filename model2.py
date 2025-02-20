import pandas as pd
import numpy as np
import lightgbm as lgb
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
from lightgbm import early_stopping, log_evaluation

def main():
    df = pd.read_csv("data.csv")
    df['parent_type'] = df['parent_type'].astype('category')
    cat_features = ['parent_type']

    # splt off 25% of groups
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=420)
    groups = df['group_id']
    for train_idx, test_idx in splitter.split(df, groups=groups):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]

    y_train = train_df.pop('y')
    y_test = test_df.pop('y')
    train_g_ids = train_df.pop('group_id')
    test_g_ids = test_df.pop('group_id')

    rem_feats = ['length','diameter','internode_length','node_count']
    rem_feats = []
    feats = [f for f in list(train_df.columns) if f not in (['Unnamed: 0', 'group_id', 'side', 'y']+rem_feats)]
    X_train = train_df[feats]
    X_test = test_df[feats]

    print(X_train.info())

    # Handle class imbalance with class weights
    class_weights = y_train.value_counts(normalize=True).to_dict()
    sample_weight = y_train.map(lambda x: 1 / class_weights[x])

    # Create LightGBM dataset
    # cat_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
    train_data = lgb.Dataset(X_train, label=y_train, weight=sample_weight, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data, categorical_feature=cat_features)

    # Define and train the model
    model = lgb.LGBMClassifier(
        objective='binary',
        metric='auc',
        boosting_type='gbdt',
        class_weight='balanced',
        categorical_feature=cat_features,
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
    feature_names = X_train.columns
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
    
    # see you many groups (sides of a plant) would have been same as labeled
    preds = model.predict_proba(X_test)[:, 1]
    X_test['group_id'] = df.loc[X_test.index, 'group_id']  
    X_test['probability'] = preds
    X_test['true_label'] = y_test.values 

    top_per_group = X_test.groupby('group_id', group_keys=False).apply(lambda df: df.nlargest(1, 'probability'))
    correct_selections = (top_per_group['true_label'] == 1).sum()
    total_groups = X_test['group_id'].nunique()
    print(f"{correct_selections} out of {total_groups} groups ({correct_selections/total_groups}).")
    print("Selected top predictions per group:")
    print(top_per_group[['group_id', 'probability', 'true_label']])


if __name__ == "__main__":
    main()