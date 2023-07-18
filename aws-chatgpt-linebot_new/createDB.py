# -*- coding: utf-8 -*-
import sqlite3
from os.path import join, split
from glob import glob
import pandas as pd

#csv_path = r"D:\blog\data\pdf2csv\csv"
#db_path = r"D:\blog\data\sqlite\test.db"
db_path = "./rooms.db"
csv = "./csv/tsuruhashi2.csv"

def insert_csv():

        #table_name = split(csv)[1] # テーブル名作成

        #table_name = table_name[0:-4] # テーブル名から拡張子を削除
        table_name = "rooms"

        df = pd.read_csv(csv, dtype=object) # CSV 読込

        with sqlite3.connect(db_path) as conn:
            df.to_sql(table_name, con=conn) # SQLiteにCSVをインポート

if __name__ == '__main__':
    insert_csv()