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

# +
import random
import os
import sys

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import RobustScaler

from supervised.automl import AutoML

import warnings
warnings.filterwarnings(action='ignore')

# -

# ## 버젼 확인하기

print("python version : ", sys.version)
print("pandas version : ", pd.__version__)
print("numpy version : ", np.__version__)
print("seaborn version : ", sns.__version__)
print("scikit version : ", sklearn.__version__)


# ## 시드 고정

# +
def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)

seed_everything(38) # Seed 고정
# -

# # 데이터 불러오기

train = pd.read_csv('https://raw.githubusercontent.com/puzzle38/python_repository/main/dacon/rent/data/train.csv')
test = pd.read_csv('https://raw.githubusercontent.com/puzzle38/python_repository/main/dacon/rent/data/test.csv')
submission = pd.read_csv('https://raw.githubusercontent.com/puzzle38/python_repository/main/dacon/rent/data/sample_submission.csv')

# # EDA

# EDA용 df 데이터셋 생성
total_df = train.drop(columns = ['ID'])
#qualitative: 질적 변수입니다
qual_df = total_df[['propertyType', 'suburbName']]
#quantitative: 양적 변수입니다
quan_df = total_df.drop(columns = ['propertyType', 'suburbName'])

# ## 결측치 확인

train.isnull().sum()

test.isnull().sum()

# ## 양적변수

# 양적변수 기초통계량 확인
total_df.describe()

#양적 변수 분포 시각화
quan_df.hist(bins=100, figsize=(18,18))
plt.show()

# ## 질적변수

# +
#질적 변수 빈도 시각화
fig, axes = plt.subplots(2, 1, figsize=(20,15))

sns.countplot(x = qual_df['propertyType'], ax=axes[0])
sns.countplot(x = qual_df['suburbName'], ax=axes[1])

plt.show()
# -

# ## 이상치 확인

# +
#이상치 확인
fig, axes = plt.subplots(3,3, figsize=(15,15))

sns.boxplot(y = quan_df['bedrooms'], ax=axes[0][0])
sns.boxplot(y = quan_df['latitude'], ax=axes[0][1])
sns.boxplot(y = quan_df['longitude'], ax=axes[0][2])

sns.boxplot(y = quan_df['distanceMetro(km)'], ax=axes[1][0])
sns.boxplot(y = quan_df['distanceAirport(km)'], ax=axes[1][1])
sns.boxplot(y = quan_df['distanceHospital(km)'], ax=axes[1][2])

sns.boxplot(y = quan_df['distanceRailway(km)'], ax=axes[2][0])
sns.boxplot(y = quan_df['area(square_meters)'], ax=axes[2][1])
sns.boxplot(y = quan_df['monthlyRent(us_dollar)'], ax=axes[2][2])

plt.show()
# -

# ## 상관관계

# +
#상관관계 히트맵
plt.figure(figsize = (15,15))
sns.heatmap(quan_df.corr(), annot = True, fmt = '.1f', linewidth = 1, cmap = 'Blues')

plt.show()
# -

# # 전처리

# ## 변수명 조정

# ID와 타겟 컬럼 제거
x_train = train.drop(columns=['ID', 'monthlyRent(us_dollar)'])
y_train = train['monthlyRent(us_dollar)']
x_test = test.drop(columns=['ID'])

# North Delhi -> Delhi North
# West Delhi -> Delhi west
x_train.loc[x_train['suburbName']=='North Delhi','suburbName']='Delhi North'
x_train.loc[x_train['suburbName']=='West Delhi','suburbName']='Delhi West'
x_test.loc[x_test['suburbName']=='North Delhi','suburbName']='Delhi North'
x_test.loc[x_test['suburbName']=='West Delhi','suburbName']='Delhi West'
x_train.loc[x_train['suburbName']=='South West Delhi','suburbName']='Other'
x_train.loc[x_train['suburbName']=='Rohini','suburbName']='Other'
x_train.loc[x_train['suburbName']=='North West Delhi','suburbName']='Other'
x_test.loc[x_test['suburbName']=='South West Delhi','suburbName']='Other'
x_test.loc[x_test['suburbName']=='Rohini','suburbName']='Other'
x_test.loc[x_test['suburbName']=='North West Delhi','suburbName']='Other'

plt.figure(figsize=(15,15))
sns.countplot(x = x_train['suburbName'])
plt.show()

# ## One-Hot 인코딩

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
# -

x_train = x_train.drop(columns=['propertyType','suburbName'])
x_test = x_test.drop(columns=['propertyType','suburbName'])

# ## 로그 정규화

x_train.loc[:,:'area(square_meters)'] = np.log1p(x_train.loc[:,:'area(square_meters)'])
x_test.loc[:,:'area(square_meters)'] = np.log1p(x_test.loc[:,:'area(square_meters)'])

# ## Robust Scaler()

rs = RobustScaler()
rs.fit(x_train.loc[:,:'area(square_meters)'])
x_train.loc[:,:'area(square_meters)'] = rs.transform(x_train.loc[:,:'area(square_meters)'])
x_test.loc[:,:'area(square_meters)'] = rs.transform(x_test.loc[:,:'area(square_meters)'])

# # 모델링

# ## AutoML

val_strategy = {
    'validation_type' : 'kfold',
    'k_folds' : 5,
    'shuffle' : True,
    "stratify": True
}

# automl 모델 생성
automl = AutoML(mode = 'Compete', eval_metric='mae', ml_task='regression', n_jobs=-1, validation_strategy=val_strategy)
automl.fit(x_train, y_train)

# 생성된 모델을 test로 예측하기
pred = automl.predict(x_test)
submission['monthlyRent(us_dollar)'] = pred
# 제출파일 생성
submission.to_csv('./result1_20221222.csv', index=False)

# 변수중요도
importances_values = model.feature_importances_
importances = pd.Series(importances_values, index = x_train.columns)
top20 = importances.sort_values(ascending = False)
plt.figure(figsize=(8,6))
plt.title('Feature importances')
sns.barplot(x = top20, y = top20.index)
plt.show()


