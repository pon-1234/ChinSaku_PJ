# ChinSaku_PJ　事前準備
```
pip install llama-index
```
# indexing用データ生成
```
python create-input_datas.py
```
# indexを生成
```
python create-index.py
```
# クエリーを実行
```
python query.py '質問文'
```

# DB連携方式に変更
## CSVデータを読み込み、SQLiteのDBファイルに投入
```
python3 createDB.py
```

## Botプロセス起動
```
 pm2 start chinsakun.py --name bot --interpreter=python3
 ```