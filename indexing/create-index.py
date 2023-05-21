import os
os.environ["OPENAI_API_KEY"] = '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'
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader


documents = SimpleDirectoryReader('data/', recursive=True).load_data()
index = GPTVectorStoreIndex.from_documents(documents)
index.storage_context.persist()