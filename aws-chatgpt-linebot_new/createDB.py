# -*- coding: utf-8 -*-
import sqlite3
import os
from os.path import join, split
from glob import glob
import pandas as pd
import requests

#csv_path = r"D:\blog\data\pdf2csv\csv"
#db_path = r"D:\blog\data\sqlite\test.db"
db_path = "./rooms.db"
src_path = "./rooms"
#csv = "./csv/tsuruhashi2.csv"
addres = {}
def zipinfo(zipcode):
    for key, value in addres.items():
         if key == zipcode:
              return value
         
    url = "https://zip-cloud.appspot.com/api/search?zipcode=" + str(zipcode)
    x = requests.get(url)
    x = x.json()
    x = x['results']
    y = pd.DataFrame(x)
    yall = y['address1']+y['address2'] + y['address3']
    print(yall[0])
    addres[zipcode] = yall[0]
    print(addres[zipcode])
    return addres[zipcode]

def insert_csv(csv):
    #table_name = split(csv)[1] # テーブル名作成
    print(csv)
    #table_name = table_name[0:-4] # テーブル名から拡張子を削除
    table_name = "rooms"

    df = pd.read_csv(csv, dtype=object) # CSV 読込

    address_col = []

    for index, row in df.iterrows():
        zip_code = row[15]
        print('zipcode =' + zip_code)
        address_col.append(zipinfo(zip_code))

    df['Address'] = address_col
    df = df.rename(columns={df.columns[249]: 'items'})
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, con=conn, if_exists='append', index=False) # SQLiteにCSVをインポート

if __name__ == '__main__':
    files = os.listdir(src_path)
    print(files)
    for file in files:
         insert_csv(src_path + '/' + file)