import polars as pl
import time

def main():
  start_time = time.time()

  # Read file as a single-column DataFrame
  a = pl.read_csv(
      "data/test_02_1.txt",
      separator="\n",
      skip_rows=2,
      has_header=False,
      new_columns=["data"],
  )

  # Extract columns with regex and cast dtypes
  df = a.select(
      pl.col("data").str.extract_groups(
          r"^(?<vin>.{17})  (?<make>.{13})  (?<model>.{19})  (?<year>\d{4})  (?<price>.{10})$"
      )
  ).unnest("data").with_columns(
      pl.col("vin", "make", "model").str.strip_chars(),
      pl.col("year").cast(int),
      pl.col("price").cast(float),
  )

  finish_time = time.time()

  print(df)
  print(df.describe())
  print(f"Execution time: {finish_time - start_time} seconds")

if __name__ == "__main__":
    main()