import polars as pl

# サンプルデータの作成
data1 = {
    "id": [1, 2, 3],
    "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
    "value1": [10, 20, 30]
}

data2 = {
    "id": [1, 2, 3],
    "date": ["2024-01-01", "2024-01-02", "2024-01-04"],
    "value2": [100, 200, 300]
}

# DataFrameの作成
df1 = pl.DataFrame(data1)
df2 = pl.DataFrame(data2)

# idとdateを基に結合しつつ、value2を追加
merged_df = df1.join(df2, on=["id", "date"], how="outer").sort("id")

print("統合後のDataFrame:")
print(merged_df)
