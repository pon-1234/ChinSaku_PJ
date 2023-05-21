import sys
import os
from llama_index import LLMPredictor, load_index_from_storage, StorageContext, PromptHelper, ServiceContext
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
os.environ["OPENAI_API_KEY"] = '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'

template = """ 
与えられた質問に対して日本語で回答してください。
また、以下のフォーマットで答えてください。
```
質問: {question}
解答:
```
"""
prompt = PromptTemplate(
    input_variables=["question"],
    template = template,
)

max_input_size = 4096
num_output = 2048
max_chunk_overlap = 20
prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=2048))
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)


storage_context = StorageContext.from_defaults(persist_dir='storage')
index = load_index_from_storage(storage_context,)
query_engine = index.as_query_engine(service_context=service_context)


args = sys.argv
question = args[1]
output = query_engine.query(prompt.format(question=question))
print(output)