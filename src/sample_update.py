import polars as pl

# サンプルデータの作成
data = {
    "name": ["Alice", "Bob", "Charlie", "David"],
    "age": [23, 35, 45, 31],
    "city": ["New York", "Los Angeles", "Chicago", "San Francisco"]
}

# DataFrameの作成
df = pl.DataFrame(data)

# データの一部を更新
df = df.with_columns([
    pl.when(df["age"] > 30).then(40).otherwise(df["age"]).alias("age")
])

print("更新後のDataFrame:")
print(df)
