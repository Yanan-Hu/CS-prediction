# import packages
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.feature_selection import RFECV
from sklearn.pipeline import Pipeline
import joblib
import os
from scipy.stats import uniform
from uti import data_import
import time

pathes = ['../results', '../model']
for path in pathes:
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        pass

seed = 42
# no warning sign
pd.options.mode.chained_assignment = None

start_time = time.time()

# import dataset
train_path = '../data/pdc_dev.sas7bdat'
X_train, y_train = data_import(train_path)

# creat model
estimator = LogisticRegression(max_iter=int(1e10), random_state=seed)

# hyperparameter tuning and feature selection
rfecv = RFECV(estimator=estimator, step=1, cv=5, scoring='roc_auc')
param_dist = {'classification__C': uniform(0.01, 10), 'classification__penalty': ['l1', 'l2', 'elasticnet', None],
              'classification__solver': ['sag', 'saga', 'liblinear', 'lbfgs', 'newton-cg']}
pipeline = Pipeline([('feature_selection', rfecv), ('classification', estimator)])
rand_search = RandomizedSearchCV(pipeline, param_distributions=param_dist, n_iter=10, cv=5, random_state=seed,
                                    scoring='roc_auc')
rand_search.fit(X_train, y_train)

end_time = time.time()

# output best mean performance on test data during cross-validation and standard deviation of mean_test_score
cv_results = pd.DataFrame.from_dict(rand_search.cv_results_)

mean_test_score = round(cv_results[cv_results['rank_test_score'] == 1]['mean_test_score'].values[0], 3)
std_test_score = round(cv_results[cv_results['rank_test_score'] == 1]['std_test_score'].values[0], 3)

# save output
with open('../results/results.txt', 'a') as a:
    print('Logistic regression', file=a)
    print(f'Training time: {(end_time - start_time) / 60: .4f} mins.', file=a)
    print('the best model in cv, mean test score:', mean_test_score, file=a)
    print('the best model in cv, std test score:', std_test_score, file=a)

# best pipeline
best_pipeline = rand_search.best_estimator_

# fit best pipeline on the entire dataset
best_pipeline.fit(X_train, y_train)

# save model
joblib.dump(best_pipeline, f'../model/best_pipeline_lr.clf')

# best classifier
best_classifier = best_pipeline.named_steps['classification']

# save model
joblib.dump(best_classifier, f'../model/best_classifier_lr.clf')

# save csv
csv_data = pd.DataFrame({'Model': ['Logistic Regression'], 'mean test score': mean_test_score, 'SD test score': std_test_score})
csv_path = '../results/internal_test_score.csv'
if os.path.exists(csv_path):
    csv_data.to_csv(csv_path, mode='a', index=False, header=False)
else:
    csv_data.to_csv(csv_path, mode='w', index=False, header=True)
