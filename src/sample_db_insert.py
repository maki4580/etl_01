import polars as pl
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

# サンプルデータの作成
input_data = {
    "id": [1, 2, 3, 4],
    "value": [10, 20, 30, 40]
}

delete_data = {
    "id": [2, 3]
}

# DataFrameの作成
input_df = pl.DataFrame(input_data)
delete_df = pl.DataFrame(delete_data)

# 削除データを除去
filtered_df = input_df.filter(~input_df["id"].is_in(delete_df["id"]))

# PostgreSQLに接続
DATABASE_URL = "postgresql+psycopg2://username:password@hostname/dbname"
engine = sa.create_engine(DATABASE_URL)

# テーブルの作成（例としてidを主キーとします）
metadata = sa.MetaData()
table = sa.Table(
    'example_table',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('value', sa.Integer)
)

metadata.create_all(engine)

# データベースにデータを挿入
reject_data = []

with engine.connect() as connection:
    for record in filtered_df.iter_rows(named=True):
        try:
            ins = table.insert().values(record)
            connection.execute(ins)
        except IntegrityError as e:
            reject_data.append(record)

# リジェクトDataFrameの作成
reject_df = pl.DataFrame(reject_data)

print("登録後のDataFrame:")
print(filtered_df)

print("リジェクトDataFrame:")
print(reject_df)
