import polars as pl

# サンプルデータの作成
data = {
    "name": ["Alice", "Bob", "Charlie", "David"],
    "age": [23, 35, 45, 31],
    "city": ["New York", "Los Angeles", "Chicago", "San Francisco"]
}

# DataFrameの作成
df = pl.DataFrame(data)

# 条件に基づいて2つのDataFrameに分割
condition = df["age"] > 30
df1 = df.filter(condition)
df2 = df.filter(~condition)

print("DataFrame 1:")
print(df1)
print("DataFrame 2:")
print(df2)
