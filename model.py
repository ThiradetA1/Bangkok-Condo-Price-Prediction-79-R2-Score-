import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

file = "livinginsider_big_data.csv"
df = pd.read_csv(file)

#print(df.head())
print("Data Info:")
print(df.info())

print(df.isnull().sum())

df.dropna(inplace=True)

print(df.isnull().sum())

df_clean = df.drop_duplicates() 
print(df_clean.info())

df_condo = df_clean[ (df_clean['price'] > 450000) & (df_clean['price'] < 10000000) & (df_clean['size_sqm'] > 0) & (df_clean['size_sqm'] < 200) & (df_clean['bedroom'] > 0) & (df_clean['bedroom'] < 6 ) & (df_clean['bathroom'] > 0) & (df_clean['bathroom'] < 5)].copy()

le = LabelEncoder()
df_condo['project_id'] = le.fit_transform(df_condo['project_name'].astype(str))


features = ['size_sqm', 'floor_num', 'bedroom', 'bathroom', 'project_id', 
            'is_corner', 'is_river_view', 'near_bts']
target = 'price'

X = df_condo[features]
y = df_condo[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100


print(f"Mean Absolute Error (MAE): {mae}")
print(f"R-squared (R2): {r2}")
print(f"Mean Absolute Percentage Error (MAPE): {mape}")

feature_imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("\nปัจจัยที่มีผลต่อราคาคอนโดมากที่สุด:")
print(feature_imp)

print("\nExample Prediction:")
example_index = 2
real_price = y_test.iloc[example_index]
pred_price = y_pred[example_index]

print(f"ห้องตัวอย่างจากโครงการ ID: {X_test.iloc[example_index]['project_id']}")
print(f"ขนาด: {X_test.iloc[example_index]['size_sqm']} ตรม., ชั้น: {X_test.iloc[example_index]['floor_num']}")
print(f"ราคาจริง: {real_price:,.0f} บาท")
print(f"โมเดลทาย: {pred_price:,.0f} บาท")
print(f"ส่วนต่าง: {abs(real_price - pred_price):,.0f} บาท")

joblib.dump(model, 'my_condo_model.pkl')
joblib.dump(le, 'my_encoder.pkl')

plt.figure(figsize=(10, 6))
sns.scatterplot(x=y_test, y=y_pred, alpha=0.5, color='purple')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('(Actual Price)')
plt.ylabel('(Predicted Price)')
plt.title(f'Actual vs Predicted Price ($R^2$: {r2:.2f})')
plt.show()


