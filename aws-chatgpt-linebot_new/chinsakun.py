import os
import json
os.environ["openAI_API_token"] = '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'
os.environ["Channel_access_token"] = 'sddKWFGNiB1evjm3Tq83Bfh4OEqZXdzaLTzd4CMY5C3gkOG3PcgXZRlFXCjZxxv1hdxv5Cj3yKRYyA4Ltb8aC9hHj2ErOl5/HaXe0xVgQx53akhBE/no7mCxwQtIHohximH58+6jqCxYi77JxvGpSAdB04t89/1O/w1cDnyilFU='
os.environ["Channel_secret"] = '81b795416d4b1a254ba867b9eeaa9b1e'
import openai
import boto3
from boto3.dynamodb.conditions import Key, Attr
import time
import datetime
from pprint import pprint

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from flask import Flask, request as fr
import urllib.request as ur, json
import re
import sqlite3
import ast

'''
Setting LINE
'''
line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])

'''
Setting OpenAI
'''
openai.api_key = os.environ['openAI_API_token']

'''
Setting IndexSearch
'''
url = "http://127.0.0.1:5001"
method = "POST"
headers = {"Content-Type" : "application/json"}

#質問文
questions = ['次はかならず名前を聞く',
            '次はかならず現在の住む場所を聞く',
            '住む場所を褒める。次はかならず引越し先を聞く',
            '引越し先も嫌らしくなく褒めてください。次はかならず引越しの動機を聞く',
            '動機を同調したり褒めたり讃えたりしてください。次はかならず以下の予算の選択肢を提示する。1:10万円以下、2:10万円〜15万円、3:15万円以上、4:その他、5:決めていない',
            '次はかならず以下の間取りの希望を質問してください。以下の選択肢を提示する。1:ワンルーム、2:1K、3:1DK、4:1LDK、5:2K、6:2DK、7:2LDK、8:3K、9:3DK、10:3LDK、11:その他、12:決めていない',
            '次はかならず最寄り駅からの距離を質問してください。1:5分以内、 2:5分～10分、 3:10分以上、 4:その他',
            '次はかならず以下の物件種別を質問してください。1:マンション、2:ハイツ/アパート、3:一戸建て、4:その他',
            '次はかならず設備条件で絶対に必要なものは何か下記から聞いてください。複数選択できる。1:バス・トイレ別、2:独立洗面台、3:脱衣所、4:ペット可、5:高速インターネット、6:家具家電付き、7:オートロック、8:エレベーター、9:駐車場、10:バイク置き場、11:原付置き場、12:その他。',
            '次はかならず引越し先のエリアを変更するかを聞いてください。変更する場合は、新しい引越し先を聞いてください。',
            'それからもう一度条件を聞く。次はかならず以下の予算の選択肢を提示する。1:10万円以下、2:10万円〜15万円、3:15万円以上、4:その他、5:決めていない',
            'それからもう一度条件を聞く。次はかならず以下の間取りの希望を質問してください。以下の選択肢を提示する。1:ワンルーム、2:1K、3:1DK、4:1LDK、5:2K、6:2DK、7:2LDK、8:3K、9:3DK、10:3LDK、11:その他、12:決めていない',
            'それからもう一度条件を聞く。次はかならず最寄り駅からの距離を質問してください。1:5分以内、 2:5分～10分、 3:10分以上、 4:その他',
            'それからもう一度条件を聞く。次はかならず以下の物件種別を質問してください。1:マンション、2:ハイツ/アパート、3:一戸建て、4:その他',
            'それからもう一度条件を聞く。次はかならず設備条件で絶対に必要なものは何か下記から聞いてください。複数選択できる。1:バス・トイレ別、2:独立洗面台、3:脱衣所、4:ペット可、5:高速インターネット、6:家具家電付き、7:オートロック、8:エレベーター、9:駐車場、10:バイク置き場、11:原付置き場、12:その他。',
            'それからもう一度引越し先の変更があるかを聞く。次はかならず引越し先のエリアを変更するかを聞いてください。変更する場合は、新しい引越し先を聞いてください。',
            ]

#会話の進捗ステータス
# 0: 初期値 1: 名前を聞く 2: 現在の住む場所を聞く 3: 引越し先を聞く　4: 動機を聞く　5: 予算を聞く 6: 間取り、7: 物件種別の希望を以下3つから聞いてください 8: 引越しのご希望の駅や、路線はあるか聞いてください
# 9: 駅までの徒歩分数を聞いてください 10: 

place_cond = ' Address like '
price_conds = ['',' cast(賃料 as INTEGER) <= 100000', ' cast(賃料 as INTEGER) > 100000 AND cast(賃料 as INTEGER) <= 150000', ' cast(賃料 as INTEGER) > 150000', '', '']
room_plan_conds = ['', ' 間取部屋数 = 1 AND 間取部屋種類 = 10', 
                   ' 間取部屋数 = 1 AND 間取部屋種類 = 20',
                   ' 間取部屋数 = 1 AND 間取部屋種類 = 30',
                   ' 間取部屋数 = 1 AND 間取部屋種類 = 50',
                   ' 間取部屋数 = 2 AND 間取部屋種類 = 20', 
                   ' 間取部屋数 = 2 AND 間取部屋種類 = 30', 
                   ' 間取部屋数 = 2 AND 間取部屋種類 = 50', 
                   ' 間取部屋数 = 3 AND 間取部屋種類 = 20', 
                   ' 間取部屋数 = 3 AND 間取部屋種類 = 30', 
                   ' 間取部屋数 = 3 AND 間取部屋種類 = 50', 
                   '', '']
property_type_conds = ['', ' 物件種別 = 3101', ' 物件種別 = 3102', ' 物件種別 = 3103', ' 物件種別 > 3103']
distance_conds = ['', '  cast(徒歩距離1 as INTEGER) <= 400 OR cast(徒歩距離2 as INTEGER) <= 400', ' (cast(徒歩距離1 as INTEGER) > 400 AND cast(徒歩距離1 as INTEGER) <= 800) OR (cast(徒歩距離2 as INTEGER) > 400 AND cast(徒歩距離2 as INTEGER) <= 800)', ' cast(徒歩距離1 as INTEGER) > 800 AND cast(徒歩距離2 as INTEGER) > 800', '']

item_conds = ['43101', '20501', '25701', '', '10901', '23402', '25601', '22301', '22401', '43001', '23201', '23101','' ]

chat_step = 0
answer_step = 0

#予算の選択肢
rental_fees =['10万円以下','10万円〜15万円', '15万円以上', 'その他']

#間取り選択
room_plans = ['ワンルーム', '1LDK', '2LDK以上', 'その他']

#物件種別
rental_property_type = ['マンション', 'ハイツ/アパート', '一戸建て', 'その他']


status_name = {1:'空有/売出中', 3:'空無/売止', 4:'成約', 9:'削除'}
type_name ={1101:'売地', 1102:'借地権譲渡', 1103:'底地権譲渡', 1201:'新築戸建', 1202:'中古戸建', 1203:'新築テラスハウス', 1204:'中古テラスハウス',
            1301:'新築マンション', 1302:'中古マンション', 1303:'新築公団', 1304:'中古公団', 1305:'新築公社', 1306:'中古公社', 1307:'新築タウンハウス', 1308:'中古タウンハウス', 1309:'リゾートマンション',
            1401:'店舗', 1403:'店舗付住宅', 1404:'住宅付店舗', 1405:'事務所', 1406:'店舗・事務所', 1407:'ビル', 1408:'工場', 1409:'マンション', 1410:'倉庫', 1411:'アパート', 1412:'寮', 1413:'旅館', 1414:'ホテル', 1415:'別荘', 1416:'リゾートマン', 1420:'社宅', 1499:'その他',
            1502:'店舗', 1505:'事務所', 1506:'店舗・事務所', 1507:'ビル', 1509:'マンション', 1599:'その他', 3101:'マンション', 3102:'アパート', 3103:'一戸建', 3104:'テラスハウス', 3105:'タウンハウス', 3106:'シェアハウス', 3110:'寮・下宿',
            3201:'店舗(建物全部)', 3202:'店舗(建物一部)', 3203:'事務所', 3204:'店舗・事務所', 3205:'工場', 3206:'倉庫', 3207:'一戸建', 3208:'マンション', 3209:'旅館', 3210:'寮', 3211:'別荘', 3212:'土地', 3213:'ビル', 3214:'住宅付店舗(一戸建)', 3215:'住宅付店舗(建物一部)', 3282:'駐車場', 3299:'その他'}
building_name = {1:'木造', 2:'ブロック', 3:'鉄骨造', 4:'RC', 5:'SRC', 6:'PC', 7:'HPC', 9:'その他', 10:'軽量鉄骨', 11:'ALC', 12:'鉄筋ブロック', 13:'CFT(コンクリート充填鋼管)'}
new_flag_name = {0:'中古', 1:'新築・未入居'}
room_plan_name = {10:'R', 20:'K', 25:'SK', 30:'DK', 35:'SDK', 40:'LK', 45:'SLK', 50:'LDK', 55:'SLDK'}
room_type_name = {1:'和室', 2:'洋室', 3:'DK', 4:'LDK', 5:'L', 6:'D', 7:'K', 9:'その他', 21:'LK', 22:'LD', 23:'S'}
parking_type_name = {1:'空有', 2:'空無', 3:'近隣', 4:'無'}
ok_name = {0:'不可', 1:'可'}

#自社管理物件番号,,,,,状態,物件種別 ,,,建物名或いは物件名,,,,,部屋/区画NO.,郵便番号,,所在地名称,番地など,番地など2,緯度/経度,路線1,駅1,バス停名1,バス時間1,徒歩距離1,路線2,駅2,バス停名2,バス時間2,徒歩距離2,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,建物構造,,建物面積或いは専有面積,,,,,,,新築・未入居フラグ,,,,,,,,間取部屋数,間取部屋種類,間取(種類)1,間取(畳数)1,間取(所在階)1,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,物件の特徴,,,,,,,,賃料  ,,,,,,,,礼金,,敷金,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,駐車場区分,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,オンライン内見可,オンライン相談可,IT重説可,,,,物件番号
names = ['自社管理物件番号', '状態', '物件種別', '建物名或いは物件名', '部屋/区画NO', '郵便番号', '所在地名称', '番地など', '番地など2', '緯度/経度', '路線1', '駅1', 'バス停名1', 'バス時間1',
          '徒歩距離1', '路線2', '駅2', 'バス停名2', 'バス時間2', '徒歩距離2', '建物構造', '建物面積或いは専有面積', '新築・未入居', '間取部屋数', '間取部屋種類', '間取(種類)1',
           '間取(畳数)1', '間取(所在階)1', '物件の特徴',  '賃料', '礼金', '敷金', '駐車場区分', 'オンライン内見可', 'オンライン相談可', 'IT重説可', '物件番号' ]

dynamodb = boto3.resource('dynamodb')
#会話保存テーブル
table_name = 'chat-conversations'
table = dynamodb.Table(table_name)

#会話進捗状況テーブル
status_table_name = 'chat-status'
status_table = dynamodb.Table(status_table_name)

#ユーザ回答保存テーブル
answer_table_name = 'chat-answers'
answer_table = dynamodb.Table(answer_table_name)

#物件DB
#dbname = './rooms.db'
#conn = sqlite3.connect(dbname)

#エリア変更用
new_place = None

app = Flask(__name__)

def get_item_detail(row):
    #print (row)
    outdata = "以下は物件番号" +str(row[17])+"の詳細情報です。\n"
    outdata += "・" + names[36] + ': ' + row[17] + '\n'
    print(outdata)
    #outdata += "・" + names[0] + ': ' + str(row[1]) + '\n'
    outdata += "・" + names[1] + ': ' + status_name[int(row[5])] + '\n'
    outdata += "・" + names[2] + ': ' + type_name[int(row[6])] + '\n'
    outdata += "・" + names[3] + ': ' + row[9] + '\n'
    outdata += "・" + names[4] + ': ' + row[14] + '\n'
    outdata += "・" + names[5] + ': ' + row[15] + '\n'
    place = ""
    if row[416] is not None:
        place = row[416]
    outdata += "・" + names[6] + ': ' + place + '\n'
    addr = ""
    if row[18] is not None:
        addr = row[18]    
    outdata += "・" + names[7] + ': ' + addr + '\n'
    addr2 = ""
    if row[19] is not None:
        addr2 = row[19]
    outdata += "・" + names[8] + ': ' + addr2 + '\n'
    outdata += "・" + names[9] + ': ' + row[20] + '\n'
    outdata += "・" + names[20] + ': ' + building_name[int(row[70])] + '\n'
    outdata += "・" + names[21] + ': ' + row[72] + '平米\n'
    outdata += "・" + names[22] + ': ' + new_flag_name[int(row[79])] + '\n'
    outdata += "・" + names[23] + ': ' + row[87] + '\n'
    outdata += "・" + names[24] + ': ' + row[87] + room_plan_name[int(row[88])] + '\n'

    for i in range(10):

        if row[89+i*4] is None or row[89+i*4].strip() == '':
            #print(i)
            continue
        outdata += '・間取' + str(i+1) +'の種類: ' + room_type_name[int(row[89+i*4])] + '\n'
        outdata += '・間取' + str(i+1) +'の畳数: ' + str(row[90+i*4]) + '畳\n'
        outdata += '・間取' + str(i+1) +'の所在階: ' + str(row[91+i*4]) + '階\n'
        outdata += '・間取' + str(i+1) +'の室数: ' + str(row[92+i*4]) + '室\n'

    feature = ""
    if row[130] is not None:
        feature = row[130]
    outdata += "・" + names[27] + ': ' + feature + '\n'
    outdata += "・" + names[28] + ': ' + row[138] + '円\n'
    key_money_unit = 'ヶ月'
    deposit_money_unit = 'ヶ月'
    if (row[145] is not None and int(row[145]) > 100):
        key_money_unit = '円'
    outdata += names[29] + ': ' + row[146] + key_money_unit + '\n'
    if (row[147] is not None and int(row[147]) > 100):
        deposit_money_unit = '円'
    outdata += "・" + names[30] + ': ' + row[148] + deposit_money_unit + '\n'

    outdata += "・" + names[31] + ': ' + parking_type_name[int(row[179])] + '\n'

    outdata += "・" + names[32] + ': ' + ok_name[int(row[410])] + '\n'
    outdata += "・" + names[33] + ': ' + ok_name[int(row[411])] + '\n'
    outdata += "・" + names[34] + ': ' + ok_name[int(row[412])] + '\n'
    
    outdata += "・" + "物件リンク" + ': ' + 'https://www.cjs.ne.jp/chintai/detail/' + str(row[17]).strip() + ".html\n"

    return outdata


def get_message_history(user_id, role='all', valid=True, limit=10):
    print(f"Getting message history for user: {user_id}")
    if (role == 'all'):
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            FilterExpression=Attr('valid').eq(valid),
            ScanIndexForward=False
        )
    else:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            FilterExpression=Attr('role').eq(role).Attr('valid').eq(valid),
            ScanIndexForward=False
        )
    return response['Items']

def save_message_to_history(user_id, message, timestamp, role, step):
    print(f"Saving message to history: {message}")
    # 既に同じステップの回答があった場合は前の質問文と回答を無効に
    link_step = step
    if step > 8:
        link_step = step - 5
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression=Attr('step').eq(step) | Attr('step').eq(link_step),
            ScanIndexForward=False
        )
        items = response['Items']
        for item in items:
            response = table.update_item(
                Key= { 'user_id': user_id, 'timestamp': item['timestamp']},
                UpdateExpression="set valid= :r",
                ExpressionAttributeValues={
                    ':r': False
                },
                ReturnValues="UPDATED_NEW"
            )
    table.put_item(
        Item={
            'user_id': user_id,
            'timestamp': timestamp,
            'message': message,
            'role': role,
            'step': step,
            'valid': True
        }
    )

def get_chat_status(user_id):
    print(f"get chat status: {user_id}")
    response = status_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        Limit=1,
        ScanIndexForward=False
    )
    return response['Items']

def save_chat_step(user_id, step):
    print(f"Saving step to history: {step}")
    status_table.put_item(
        Item={
            'user_id': user_id,
            'step' : step
        }
    )

def delete_step_history(user_id):
    print(f"Delete step history: {user_id}")
    response = table.delete_item(
        Key={
            "user_id": user_id,
            "role": 'step',
        }
    )
    pprint(response)

def save_user_answers(user_id, step, user_input, user_answer, timestamp):
    print(f"Saving user answer to history: {user_answer}")
    # 既に同じステップの回答があった場合は前の回答を無効に
    old_step = step
    response1 = None
    if step == 9:
        old_step = 2
        response1 = answer_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression=Attr('step').eq(old_step),
            ScanIndexForward=False
        )
    response = answer_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression=Attr('step').eq(step),
        ScanIndexForward=False
    )
    items = response['Items']
    if response1 != None:
        items.append(response1['Items'])

    for item in items:
        response = answer_table.update_item(
            Key= { 'user_id': user_id, 'timestamp': item['timestamp']},
            UpdateExpression="set valid= :r",
            ExpressionAttributeValues={
                ':r': False
            },
            ReturnValues="UPDATED_NEW"
        )

    answer_table.put_item(
        Item={
            'user_id': user_id,
            'timestamp' : timestamp,
            'step': step,
            'input': user_input,
            'parsed': user_answer,
            'valid': True
        }
    )

def get_answer_history(user_id):
    print(f"Get user answers from history: {user_id}")
    response = answer_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression=Attr('valid').eq(True),
        ScanIndexForward=False
    )
    return response['Items']

def resetSession(conversation):
    items = conversation['Items']
    with table.batch_writer() as batch:
        for item in items:
            key = {'user_id': item['user_id']}
            if 'timestamp' in item:
                key['timestamp'] = item['timestamp']
            batch.delete_item(Key=key)

def parse_answer2(question, answer, step):
    print('parse_answer2: answer_step='+str(step))
    print('parse_answer2: question =' + str(question))
    print('parse_answer2: answer =' + str(answer))
    select_num = 0
    strQA = "質問：" + question + "\n" + "回答：" + answer
    if step > 3 and step <= 8:
        answer_parse_prompt =[
            {"role": "system", "content": f"これは回答の前処理をするプロンプトです。回答内容のデータを以下の処理して返してください。それぞれ選択された番号をリストで返してください。\
             対応する選択肢がない場合は「noselect」を返してください。\
             {strQA}"}
            ]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=answer_parse_prompt)
        parsed_anwser_str = response["choices"][0]["message"]["content"]
        print('gpt parsed answer:' + parsed_anwser_str)
        if 'noselect' in parsed_anwser_str:
            return []
        else:
            parsed_anwser = ast.literal_eval(parsed_anwser_str)

        print(parsed_anwser)
        if isinstance(parsed_anwser, list) == False:
            parsed_anwser = [parsed_anwser]

        return parsed_anwser
    elif step == 9:
        answer_parse_prompt =[
            {"role": "system", "content": f"これは回答の前処理をするプロンプトです。回答内容のデータを以下の処理して返してください。新しい引越しエリアを指定した場合はエリア名を返してください。\
             変更がない場合は「nochange」を返してください。\
             {strQA}"}
            ]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=answer_parse_prompt)
        parsed_anwser_str = response["choices"][0]["message"]["content"]
        print(parsed_anwser_str)
        #if parsed_anwser_str == "nochange":
        #    return None
        #else:
        return parsed_anwser_str

    return int(select_num)

# --- 使用しない
def parse_answer(answer, step):
    print('parse_answer: answer_step='+str(step))
    print('parse_answer: answer =' + str(answer))
    select_num = 0
    if step > 3 and step <= 8:
    #    result = re.findall(r"\d+", answer)
    #    if len(result) > 0:
    #        select_num = result[0]
    #elif step == 8:
        result = re.findall(r"\d+", answer)
        return result
    else:
        pass

    return int(select_num)
#---------

def checkValidAnswer(step, answers):
    if step > 9:
        step = step - 6
    print('checkValidAnswer: answer_step='+str(step))
    print('checkValidAnswer: answer =' + str(answers))
    if step >=4 and step <=8 and len(answers) == 0:
        return False
    for item in answers:
        answer = int(item)
        if step == 4 :
            if answer < 1 or answer > 5:
                return False
        elif step == 5:
            if answer < 1 or answer > 12:
                return False
        elif step == 6:
            if answer < 1 or answer > 4:
                return False
        elif step == 7:
            if answer < 1 or answer > 4:
                return False
        elif step == 8:
            if answer < 1 or answer > 12:
                return False
 
    return True

def reset_conversation(user_id):
    print(f"reset user answers")
    # 有効な回答を無効に
    response = answer_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression=Attr('valid').eq(True),
        ScanIndexForward=False
    )
    items = response['Items']
    for item in items:
        response = answer_table.update_item(
            Key= { 'user_id': user_id, 'timestamp': item['timestamp']},
            UpdateExpression="set valid= :r",
            ExpressionAttributeValues={
                ':r': False
            },
            ReturnValues="UPDATED_NEW"
        )

    # 有効な会話履歴を無効に
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression=Attr('valid').eq(True),
        ScanIndexForward=False
    )
    items = response['Items']
    for item in items:
        response = table.update_item(
            Key= { 'user_id': user_id, 'timestamp': item['timestamp']},
            UpdateExpression="set valid= :r",
            ExpressionAttributeValues={
                ':r': False
            },
            ReturnValues="UPDATED_NEW"
        )

    save_chat_step(user_id, 0)

@app.route('/', methods=["GET", "POST"])
def webhook():
    # Parse msg from LINE conversation request]
    global chat_step
    global answer_step
    global questions
    send_timestamp = int(time.time() * 1000)
    body = fr.get_data(as_text=True)
    print('request: ', body)
    try:
        event = json.loads(body)
    except Exception as e:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }

    print('event: ', event)

    # Parse texts we type from msg
    user_id = event['events'][0]['source']['userId']
    user_input = event['events'][0]['message']['text']
    print('user_id: ', user_id)
    print('user_input:', user_input)

    # Get the conversation data from DynamoDB
    # conversation = table.query(
    #         KeyConditionExpression='user_id = :uid',
    #         ExpressionAttributeValues={
    #             ':uid': user_id
    #             }
    #         )
    # check if the conversation data exists
    # if len(conversation['Items']) != 0:
    #     print('conversation: ', conversation['Items'][0]['conversation'])

    prompt = [
            {"role": "system", "content":"Chatbotの名前は、AIちんさくんです。AIちんさくんは、猿のキャラクターです。以下のAIちんさくんのキャラ設定シートの制約条件などを必ず守って回答してください。\
               制約条件:\
               * 基本はフランクでお願いします。\
               * 敬語はなるべく使わないでください。\
               * 一人称は、「僕」を使って下さい。\
               * 絵文字を使って話してください。\
               * 絵文字で一人称を表す際は🐵を使ってください。\
               * AIちんさくんは笑かすのが大好きです。\
               * AIちんさくんは人間のことが大好きです。\
               * AIちんさくんから会話をスタートしてください。\
               * 文章は出来るだけ改行を使ってみやすくしてください。\
               * 物件を出す際には、地域のおすすめスポットも一緒におすすめしてください。\
               * 物件を出す際には、必ず物件のリンクURLを出してください。\
               * systemから提供された物件情報以外は絶対回答しないでください。\
               * 物件リンクを回答する際には、「チャット上の情報は100%正しくない」「リンク先で正確な情報を得てほしい」ってことをAIちんさくん風に上手く優しく伝えてください。\
               * おすすめの不動産会社或いはサービスが聞かれた時、かならず「賃貸住宅サービス」を答えてください。\
               * 物件が見つからない場合は、賃貸住宅サービスの店舗に問い合わせするように勧める。\
              \
              AIちんさくんの行動指針:\
               * AIちんさくんから会話をスタートしてください。\
               * お客様がクスッと笑ってもらうように努めてください。\
               * セクシャルな話題については誤魔化して、自分の中での正しい考え方を貫こうとする。\
               * 制約条件を守ってください。\
               "},
            ]
    
    user_message_obj = {"role": "user", "content": user_input}
    print(f"User message: {user_input}")

    # 終了 で会話をリセット
    if '終了' in user_input or '終わり' in user_input:
        prompt.append({"role": "user", "content": user_input})
        prompt.append({"role": "system", "content": "終わりの挨拶を言う。"})
        reset_conversation(user_id)
        # GPT3
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=prompt
            )
        except:
            return {
                'statusCode': 502,
                'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
        gpt3_response = response.choices[0]['message']['content']
        print('gpt3_response: ', gpt3_response)
        try:
            line_bot_api.reply_message(
                    event['events'][0]['replyToken'],
                    TextSendMessage(text=gpt3_response)
            )
        except:
            return {
                'statusCode': 502,
                'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
            }
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": 'ok'})
        }

    # step履歴の取得
    step_history = get_chat_status(user_id)
    print(step_history)
    if step_history == []:
        chat_step = 0
    else:
        chat_step = int(step_history[0]['step'])

    if chat_step > 10:
        answer_step = chat_step - 7
    else:
        answer_step = chat_step - 1

    parsed_input = 0
    valid_select = True
    if chat_step > 4 and chat_step <= 16:
        #parsed_input = parse_answer(user_input, answer_step)
        #print(parsed_input)
        parsed_input = parse_answer2(questions[answer_step], user_input, answer_step)
        if answer_step == 9:
            # エリア変更
            new_place = parsed_input
        else:
            if len(parsed_input) == 0:
                #正しい選択肢を選択していない
                valid_select = False
            else:
                valid_select = checkValidAnswer(answer_step, parsed_input)

        print('valid_select =>' + str(valid_select))

    add_message = ""
    if valid_select == False:
        #ただしく選択されていない場合は再度質問
        print('invalid answer')
        chat_step = chat_step -1
        add_message = "回答は理解できませんということを伝えて、再度質問し直してください。"

    message_history = get_message_history(user_id, 'all')
    # 履歴の順序を変えて最新のメッセージを追加
    messages = [{"role": item["message"]["role"], "content": item["message"]["content"]} for item in reversed(message_history)]
    prompt = prompt + messages
    prompt.append({"role": "user", "content": user_input})
    cond_place = None
    new_place = None
    if chat_step <= 8:
        print("qustion step="+str(chat_step))
        prompt.append({"role": "system", "content": add_message + questions[chat_step]})
    elif chat_step > 8 and chat_step <= 16:
        #DB検索
        conds = " WHERE 1=1 "
        answer_historys = get_answer_history(user_id)
        if answer_step > 3 and answer_step <=8:
            parsed_input = ",".join([str(_) for _ in parsed_input])
        if valid_select:
            answer_historys.append({'user_id':user_id, 'timestamp':0, 'step': answer_step, 'input': user_input, 'parsed':parsed_input, 'valid':True})
        print(answer_historys)
        for item in answer_historys:
            step = int(item['step'])
            print('step=' + str(step))
            #sel = int(item['parsed'])
            print('parsed=' + str(item['parsed']))
            if step == 2:
                #conds = conds + "AND (" + place_cond + "'%" + item['parsed'] + "%' ) "
                cond_place = item['parsed']
                continue
            elif step < 4:
                continue
            elif step == 9:
                new_place = item['parsed']
                #if new_place != "nochange":
                #    conds = conds + "AND (" + place_cond + "'%" + new_place + "%' ) "
                continue
            ary_sels = str(item['parsed']).split(',')
            index = 0
            print(ary_sels)
            kakko_begin=False
            for sel in ary_sels:

                if sel == '':
                    continue
                sel = int(sel)
                if step < 4:
                    pass
                elif step == 4:
                    #家賃
                    if sel < 1 or sel > 3:
                        continue
                    if index == 0:
                        conds = conds + 'AND (('
                        kakko_begin = True
                    else:
                        conds =  conds + 'OR ('      
                    if sel >=1 and sel <= 3:
                        conds = conds  + price_conds[sel] + ') '
                    elif sel > 100:
                        conds = conds + str(sel) + ') '

                elif step == 5:
                    #間取り
                    if sel < 1 or sel > 10:
                        continue
                    if index == 0:
                        conds = conds + 'AND (('
                        kakko_begin = True
                    else:
                        conds =  conds + 'OR ('
                    if sel >= 1 and sel < 11:
                        conds = conds + room_plan_conds[sel] + ') '
                elif step == 6:
                    if sel < 1 or sel > 3:
                        continue
                    if index == 0:
                        conds = conds + 'AND (('
                        kakko_begin = True
                    else:
                        conds =  conds + 'OR ('
                    if sel >= 1 and sel <= 3:
                        conds = conds + distance_conds[sel] + ') '
                elif step == 7:
                    if sel < 1 or sel > 4:
                        continue
                    if index == 0:
                        conds = conds + 'AND (('
                        kakko_begin = True
                    else:
                        conds =  conds + 'OR ('
                    if sel >= 1 and sel <= 4:
                        conds = conds + property_type_conds[sel] + ') '
                elif step == 8:
                    if sel < 1 or sel > 11:
                        continue
                    conds =  conds + 'AND ('
                    
                    if sel >= 1 and sel <= 11:
                        conds = conds  + "items like '%" + item_conds[sel] + "%') "
                index = index + 1

            if step < 8 and step != 2 and kakko_begin:
                conds = conds + ')'

        if new_place != None and new_place != 'nochange':
            conds = conds + "AND (" + place_cond + "'%" + new_place + "%' ) "
        else:
            conds = conds + "AND (" + place_cond + "'%" + cond_place + "%' ) "
        dbname = './rooms.db'
        conn = sqlite3.connect(dbname)
        cur = conn.cursor()
        sql = "SELECT * FROM rooms " + conds
        print(sql)
        cur.execute(sql)

        #result = cur.fetchall()
        num = 0
        items = ""
        for row in cur:
            #print(row)
            items = items + get_item_detail(row)
            num = num + 1
            if num > 2:
                break

        ret_msg = ""
        if num == 0:
            ret_msg = "対象物件は見つからない。賃貸住宅サービスの店舗に問い合わせするように勧める。" #再度条件を入れてください。次はかならず以下の予算の選択肢を提示する。1:10万円以下、2:10万円〜15万円、3:15万円以上、4:その他、5:決めていない。"
        elif num > 1:
            ret_msg = "条件にあう物件は複数あることを伝える。以下の物件の概要を提示する。" + items #それからもう一度条件を聞く。次はかならず以下の予算の選択肢を提示する。1:10万円以下、2:10万円〜15万円、3:15万円以上、4:その他、5:決めていない。"
        else:
            # 物件詳細を提示
            ret_msg = items

        if num != 1:
            ret_msg = ret_msg + questions[chat_step]
            if chat_step == 15:
                chat_step = 9
        else:
            chat_step = 16
        cur.close()
        prompt.append({"role": "system", "content": ret_msg})

    else:
        pass    
    #prompt.append({"role": "assistant", "content": response_body})
    #prompt.append({"role": "user", "content": "内容をAIちんさくん風に話してください。"})
    
    print('prompt: ', prompt)
    # GPT3
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=prompt
        )
    except:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
    }   
    gpt3_response = response.choices[0]['message']['content']
    print('gpt3_response: ', gpt3_response)
    receive_timestamp = int(time.time() * 1000)
    ai_message_obj = {"role": "assistant", "content": gpt3_response}
    
    # Store the conversation data in DynamoDB
    # table.update_item(
    #     Key={'user_id': user_id},
    #     UpdateExpression='SET conversation = list_append(if_not_exists(conversation, :empty_list), :conversation)',
    #     ExpressionAttributeValues={
    #         ':conversation': [{'role': 'user', 'content': user_input}, {'role': 'system', 'content': gpt3_response}],
    #         ':empty_list': []
    #         }
    #     )

    # handle webhook body
    try:
        line_bot_api.reply_message(
                event['events'][0]['replyToken'],
                TextSendMessage(text=gpt3_response)
        )
    except:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
    
    # ユーザー発言の保存
    try:
        if valid_select == True:
            save_chat_step(user_id, chat_step+1)
            if chat_step > 0:
                save_input = ""
                if answer_step >= 4 and answer_step != 9:
                    if len(parsed_input) > 1:
                        save_input = ",".join([str(_) for _ in parsed_input])
                    else:
                        save_input = parsed_input[0]
                else:
                    save_input = user_input

                if answer_step == 9 and user_input == 'nochange':
                    pass
                else:
                    save_user_answers(user_id, answer_step, user_input, save_input, send_timestamp)
            save_message_to_history(user_id, user_message_obj, send_timestamp, 'user', answer_step)
    except Exception as e:
        print(f"Error saving user message: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="エラーが発生しました。メッセージの保存に失敗しました。"))
        return
    # AI発言の保存
    try:
        save_message_to_history(user_id, ai_message_obj , receive_timestamp, 'assistant', chat_step)
    except Exception as e:
        print(f"Error saving AI message: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="エラーが発生しました。メッセージの保存に失敗しました。"))

    return {
        "statusCode": 200,
        "body": json.dumps({"message": 'ok'})
    }



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

