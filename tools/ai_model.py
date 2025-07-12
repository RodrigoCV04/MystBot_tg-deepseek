#Model
from langchain_deepseek import ChatDeepSeek
#DB
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import  RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
#Memory
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate

import json
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import messages_from_dict, HumanMessage

#
import requests



DEEPSEEK_KEY = "sk-7b3c7cf39b354e1b8ba5258f633e8b94"
MODEL = "deepseek-chat"
API_URL = "https://api.deepseek.com/v1/chat/completions"


#Hacer una pregunta básica
def ChatModel(query:str, prompt:ChatPromptTemplate=None, memory:ConversationBufferMemory=None) -> str:
    llm = ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL, temperature=0.3)
    if prompt == None or memory == None:
        res = llm.invoke(f'{query}')
        return res.content
    else:
        messages = memory.chat_memory.messages + [HumanMessage(content=f'Keep the role {prompt.messages[0].prompt.template} and answer: {query}')]
        res = llm.invoke(messages)
        return res.content
        


#Crear Memoria
def ConversationMemory(chat:list[any]=[]) -> ConversationBufferMemory:
    chat_history = ChatMessageHistory(messages=chat)
    return ConversationBufferMemory(
        chat_memory=chat_history,
        memory_key="chat_history", 
        output_key="answer", 
        return_messages=True) 



#Plantilla para el prompt
def PromptTemplate(prompt:str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("system", f"{prompt}"),])


#Separar un archivo
def SplitFile(file_path:str):
    try:
        loader = UnstructuredLoader(file_path=file_path)
        pages = loader.load()
        return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(pages)
    except Exception as e:
        print(f'ERR: Could not read the file \n{e}')
        return None
            


#Separar un archivos
def SliptFiles(files_path:list[str]) -> list:
    docs = []
    for file_path in files_path:
        try:
            loader = UnstructuredLoader(file_path=file_path)
            pages = loader.load()
            docs.append(RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(pages))
        except Exception as e:
            print(f'ERR: Could not read the file {file_path} \n{e}')
    if len(docs) == 0: print(f'Could not read any file')
    return docs



#Crea la DB
def CreateDB(docs:list) -> FAISS:
    embeddings = HuggingFaceEmbeddings()
    for doc in docs:
        db = FAISS.from_documents(documents=doc, embedding=embeddings)
    db.save_local('deepseek_db')
    return db



#Consulta sobre un archivo
def FileQuery(db: FAISS, query: str) -> str:
    qa = RetrievalQA.from_chain_type(
        llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL),
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    res = qa.invoke({"query": query})
    return res['result']




#Consulta a la DB sin memoria
def DBQuery(db:FAISS, query:str) -> str:
    qa = RetrievalQA.from_chain_type(
        llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL),
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    res = qa.invoke({"query": query})
    return res['result']



#Consulta a la DB con memoria
def DBQueryMemory(db:FAISS, query:str, memory:ConversationBufferMemory, prompt:ChatPromptTemplate):
    
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL, temperature=0.2),
        retriever=db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 6, 'lambda_mult': 0.25}
        ),
        memory=memory,
        return_source_documents=True,
        condense_question_prompt=prompt
    )

    res = qa.invoke({"question": query})
    return res['chat_history'][-1].content




#Consulta a la DB con memoria y clasifica preguntas
def ClassifyDBQueryMemory(db:FAISS, query:str, memory:ConversationBufferMemory, prompt:ChatPromptTemplate):
    
    sorter = f"¿Does the following question is related to your role: {prompt.messages[0].prompt.template} and requires reference to the document, or is it a general discussion?\n"
    sorter += f"Question: {query}\n"
    sorter += "Please answer only with 'document' or 'general'."
    intention = ChatModel(query=sorter)
    
    if intention == 'document':
        qa = ConversationalRetrievalChain.from_llm(
            llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL, temperature=0.3),
            retriever=db.as_retriever(),
            memory=memory,
            return_source_documents=True,
            condense_question_prompt=prompt
        )
        res = qa.invoke({"question": query})
        return res['chat_history'][-1].content
    
    if intention == 'general':
        return ChatModel(query=query, prompt=prompt, memory=memory)

    

def JSONtoBaseMessage() -> list[any]:
    with open(f"chat.json", "r", encoding="utf-8") as f:
        historial_data = json.load(f)
    mensajes = messages_from_dict(historial_data)
    print(mensajes)
    return mensajes


