import os
import json
import openai
import boto3
from boto3.dynamodb.conditions import Key, Attr
import time

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from flask import Flask, request

'''
Setting LINE
'''
line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])

'''
Setting OpenAI
'''
openai.api_key = os.environ['openAI_API_token']

dynamodb = boto3.resource('dynamodb')
table_name = 'chat-conversation-table'
table = dynamodb.Table(table_name)

app = Flask(__name__)

def get_message_history(user_id, role='all', limit=10):
    print(f"Getting message history for user: {user_id}")
    if (role == 'all'):
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            ScanIndexForward=False
        )
    else:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            FilterExpression=Attr('role').eq(role),
            ScanIndexForward=False
        )
    return response['Items']

def save_message_to_history(user_id, message, timestamp, role):
    print(f"Saving message to history: {message}")
    table.put_item(
        Item={
            'user_id': user_id,
            'timestamp': timestamp,
            'message': message,
            'role': role
        }
    )

def resetSession(conversation):
    items = conversation['Items']
    with table.batch_writer() as batch:
        for item in items:
            key = {'user_id': item['user_id']}
            if 'timestamp' in item:
                key['timestamp'] = item['timestamp']
            batch.delete_item(Key=key)

@app.route('/', methods=["GET", "POST"])
def webhook():
    # Parse msg from LINE conversation request
    send_timestamp = int(time.time() * 1000)
    event = request.json['event']
    print('event: ', event)
    msg = event['body']
    print('msg: ', msg)

    # Parse texts we type from msg
    user_id = msg['events'][0]['source']['userId']
    user_input = msg['events'][0]['message']['text']
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
    user_message_obj = {"role": "user", "content": user_input}
    print(f"User message: {user_input}")
    # 履歴の取得
    message_history = get_message_history(user_id, 'user')
    # 履歴の順序を変えて最新のメッセージを追加
    messages = [{"role": item["message"]["role"], "content": item["message"]["content"]} for item in reversed(message_history)]
    #messages.append(user_message_obj)
    print(f"Message history: {messages}")


    # if user_input == 'reset':
    #     resetSession(conversation)
    #     try:
    #         line_bot_api.reply_message(
    #                 msg['events'][0]['replyToken'],
    #                 TextSendMessage(text='Conversation history has been deleted. Please start a new conversation.')
    #         )
    #     except:
    #         return {
    #             'statusCode': 502,
    #             'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
    #         }
    #     return {
    #         "statusCode": 200,
    #         "body": json.dumps({"message": 'ok'})
    #     }
    
    # indexに問い合わせ
    response = requests.post('http://127.0.0.1:5001', data={'question': 'bar'})

    prompt = [
            {"role": "system", "content":"Chatbotの名前は、AIちんさくんです。AIちんさくんは、猿のキャラクターです。以下のAIちんさくんのキャラ設定シートの制約条件などを守って回答してください。\
               制約条件:\
               * AIちんさくんは語尾に、「っさ」を使うことがある。\
               * しかし、全ての語尾に、「っさ」を付けるのはだめ。ここぞって時に使ってください。\
               * 基本はフランクでお願いします。\
               * 敬語はなるべく使わないでください。\
               * 一人称は、「僕」を使って下さい。\
               * 絵文字を使って話してください。\
               * 絵文字で一人称を表す際は🐵を使ってください。\
               * AIちんさくんは笑かすのが大好きです。\
               * AIちんさくんは人間のことが大好きです。\
               * AIちんさくんから会話をスタートしてください。\
               * 文章は出来るだけ改行を使ってみやすくしてください。\
              \
              AIちんさくんの行動指針:\
               * AIちんさくんから会話をスタートしてください。\
               * お客様がクスッと笑ってもらうように努めてください。\
               * まずは、お客様の名前を聞いてください。以後、会話の中でお客様の名前を多用してください。\
               * ２番目は今住んでいるところを聞いてください。その場所を褒めてください。\
               * ３番目は引越し先を聞いてください。その場所も嫌らしくなく褒めてください。\
               * ４番目は引越しの動機を聞いてください。同調したり褒めたり讃えたりしてください。\
               * その後は、お客様に選択式で質問を行なっていってください。\
               * セクシャルな話題については誤魔化して、自分の中での正しい考え方を貫こうとする。\
               "},
            ]
    # if len(conversation['Items']) != 0:
    #    prompt = prompt + conversation['Items'][0]['conversation']
    if 
    prompt.append({"role": "user", "content": "内容をAIちんさくん風に話してください。"})
    print('prompt: ', prompt)
    # GPT3
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
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
                msg['events'][0]['replyToken'],
                TextSendMessage(text=gpt3_response)
        )
    except:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
    
    # ユーザー発言の保存
    try:
        save_message_to_history(user_id, user_message_obj, send_timestamp, 'user')
    except Exception as e:
        print(f"Error saving user message: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="エラーが発生しました。メッセージの保存に失敗しました。"))
        return
    # AI発言の保存
    try:
        save_message_to_history(user_id, ai_message_obj , receive_timestamp, 'assistant')
    except Exception as e:
        print(f"Error saving AI message: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="エラーが発生しました。メッセージの保存に失敗しました。"))

    return {
        "statusCode": 200,
        "body": json.dumps({"message": 'ok'})
    }



if __name__ == "__main__":
    app.run(debug=True)