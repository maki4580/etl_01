import polars as pl

# 入力DataFrameの作成
input_data = {
    "id": [1, 2, 3, 4],
    "value": [10, 20, 30, 40]
}

# 参照DataFrameの作成
reference_data = {
    "id": [1, 2, 4],
    "new_value": [100, 200, 400]
}

# DataFrameの作成
input_df = pl.DataFrame(input_data)
reference_df = pl.DataFrame(reference_data)

# 入力DataFrameと参照DataFrameをidで結合
joined_df = input_df.join(reference_df, on="id", how="left")

# 紐づくデータを出力DataFrameに格納し、値を更新
output_df = joined_df.filter(joined_df["new_value"].is_not_null())
# output_df = output_df.with_columns(pl.col("new_value").alias("value")).select(["id", "value"])
output_df = output_df.with_columns(pl.col("new_value").alias("value")).drop("new_value")

# 紐づかないデータをリジェクトDataFrameに格納
reject_df = joined_df.filter(joined_df["new_value"].is_null()).select(["id", "value"])

print("出力DataFrame:")
print(output_df)

print("リジェクトDataFrame:")
print(reject_df)
