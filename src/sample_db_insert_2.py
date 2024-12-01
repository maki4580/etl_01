import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# サンプルデータの作成
data = {
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
}
df = pl.DataFrame(data)

# PostgreSQLの設定
DATABASE_URI = 'postgresql://postgres:passw0rd@localhost:5432/postgres'
engine = create_engine(DATABASE_URI)

# エラーデータ用のDataFrame
error_df = pl.DataFrame(schema={'id': pl.Int64, 'name': pl.Utf8})

for row in df.iter_rows(named=True):
    insert_query = text(f"INSERT INTO my_table (id, name) VALUES ({row['id']}, '{row['name']}')")
    try:
        with engine.connect() as connection:
            connection.execute(insert_query)
            connection.commit()
    except IntegrityError:
        error_df = error_df.vstack(pl.DataFrame([row]))

print("エラーデータ:")
print(error_df)
