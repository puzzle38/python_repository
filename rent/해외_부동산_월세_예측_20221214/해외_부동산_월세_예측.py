# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # 라이브러리 불러오기

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from supervised.automl import AutoML

# # 데이터 불러오기

train = pd.read_csv('train.csv')
test = pd.read_csv('test.csv')
submission = pd.read_csv('sample_submission.csv')


# # 시드 고정

# +
def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)

seed_everything(38) # Seed 고정
# -

# # data load

x_train = train.drop(columns=['ID', 'monthlyRent(us_dollar)'])
y_train = train['monthlyRent(us_dollar)']
x_test = pd.read_csv('./test.csv').drop(columns=['ID'])

# +
# qualitative column one-hot encoding
qual_col = ['propertyType','suburbName']
ohe = OneHotEncoder(sparse=False)

for i in qual_col:
    x_train = pd.concat([x_train, pd.DataFrame(ohe.fit_transform(x_train[[i]]), columns=ohe.categories_[0])], axis=1)
    
    for qual_value in np.unique(x_test[i]): 
        if qual_value not in np.unique(ohe.categories_): 
            ohe.categories_ = np.append(ohe.categories_, qual_value)
    # One Hot Encoder가 Test 데이터로부터 Fitting되는 것은 Data Leakage이므로, Test 데이터에는 Train 데이터로 Fitting된 One Hot Encoder로부터 transform만 수행되어야 합니다.
    x_test = pd.concat([x_test, pd.DataFrame(ohe.transform(x_test[[i]]), columns=ohe.categories_[0])], axis=1)
    
x_train = x_train.drop(qual_col, axis=1)
x_test = x_test.drop(qual_col, axis=1)
print('Done.')
# -

# train 데아터와 검증 데이터로 분할
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=0.2)

# automl 모델 생성
automl = AutoML(mode = 'Compete', eval_metric='mae')
automl.fit(x_train, y_train)

# 생성된 모델을 test로 예측하기
pred = automl.predict(x_test)
submission['monthlyRent(us_dollar)'] = pred
# 제출파일 생성
submission.to_csv('./result3_20221214.csv', index=False)

# 변수중요도
importances_values = model.feature_importances_
importances = pd.Series(importances_values, index = x_train.columns)
top20 = importances.sort_values(ascending = False)
plt.figure(figsize=(8,6))
plt.title('Feature importances')
sns.barplot(x = top20, y = top20.index)
plt.show()

x_test.latitude

x_test.latitude.nunique()


