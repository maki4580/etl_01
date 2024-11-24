import polars as pl

# サンプルデータの作成
data1 = {
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"]
}

data2 = {
    "id": [4, 5, 6],
    "name": ["David", "Eve", "Frank"]
}

# DataFrameの作成
df1 = pl.DataFrame(data1)
df2 = pl.DataFrame(data2)

# 縦方向に連結
merged_df = pl.concat([df1, df2], how="vertical")

print("統合後のDataFrame (concat):")
print(merged_df)
