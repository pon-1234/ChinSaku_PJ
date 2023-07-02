import sys
import os
os.environ["OPENAI_API_KEY"] = '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'
from llama_index import LLMPredictor, load_index_from_storage, StorageContext, PromptHelper, ServiceContext
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
from flask import Flask, request



query_engine = None

app = Flask(__name__)

def init():
    global query_engine
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=2048))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

    storage_context = StorageContext.from_defaults(persist_dir='storage')
    index = load_index_from_storage(storage_context,)
    query_engine = index.as_query_engine(service_context=service_context)
    print("init query_engine")



def query(question):
    global query_engine
    send_question = "以下のルールを守って回答をしてください。\
        ・日本語で回答する。\
        ・挨拶だけの場合は検索しないで、挨拶を返す。\
        ・まずは件数を回答する。\
        ・条件にあうすべての物件名を回答する。\
        ・件数が1件の場合は、物件の詳細と物件URLを必ず回答する。\
        ・件数が２件以上の場合は、詳細を回答しない。以下の条件に合う物件を探してください。" + question
    response = query_engine.query(send_question)
    print(str(response))
    return str(response)


@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return 'クエリーはPOSTのみです。'

    else:
        qdata = request.json['question']
        return query(qdata)

init()

if __name__ == "__main__":
    app.run(port=5001, debug=True)

# 

