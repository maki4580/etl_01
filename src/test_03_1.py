from pathlib import Path
from typing import Dict, Tuple, Union
import polars as pl
import time

def main():
    start_time = time.time()

    names_and_widths = {"<vin>": 17, "<make>": 13, "<model>": 19, "<year>": 4, "<price>": 10}

    df = read_fixed_width_file_as_strs("data/test_02_1.txt", names_and_widths, skip_rows=2)

    df = df.group_by("<make>", maintain_order=True).agg(pl.col("<price>").count().alias("count")).sort("count").head()

    finish_time = time.time()

    print(df)
    print(f"Execution time: {finish_time - start_time} seconds")

def read_fixed_width_file_as_strs(file_path: Union[Path, str], col_names_and_widths: Dict[str, int], *, skip_rows: int = 0) -> pl.DataFrame:
	"""
	Reads a fixed-width file into a dataframe.
	Reads all values as strings (as indicated by function name).
	Strips all values of leading/trailing whitespaces.

	Args:
		col_names_and_widths: A dictionary where the keys are the column names and the values are the widths of the columns.
	"""

	df = pl.read_csv(
		file_path,
		has_header=False,
		skip_rows=skip_rows,
		new_columns=["full_str"],
	)

	# transform col_names_and_widths into a Dict[cols name, Tuple[start, width]]
	slices: Dict[str, Tuple[int, int]] = {}
	start = 0
	for col_name, width in col_names_and_widths.items():
		slices[col_name] = (start, width)
		start += width

	df = df.with_columns(
		[
			pl.col("full_str").str.slice(slice_tuple[0], slice_tuple[1]).str.strip_chars().alias(col)
			for col, slice_tuple in slices.items()
		]
	).drop(["full_str"])

	return df

if __name__ == "__main__":
    main()