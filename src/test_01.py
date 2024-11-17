import polars as pl

def main():
  df1 = pl.read_csv("data/test_01_1.csv", dtypes=[pl.Utf8])
  df2 = pl.read_csv("data/test_01_2.csv", dtypes=[pl.Utf8])

  # df = df.filter(pl.col("都道府県") == "東京")[["男", "女"]]
  # df = df1.with_columns((pl.col("男") + pl.col("女")).alias("計"))
  df = df1.join(df2, on=["番号", "都道府県"])

  print(df)

if __name__ == "__main__":
    main()