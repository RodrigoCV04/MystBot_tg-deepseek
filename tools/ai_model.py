from langchain_deepseek import ChatDeepSeek

from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import  RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain

from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate



DEEPSEEK_KEY = "sk-7b3c7cf39b354e1b8ba5258f633e8b94"
MODEL = "deepseek-chat"
API_URL = "https://api.deepseek.com/v1/chat/completions"


#Hacer una pregunta básica
def ChatModel(query: str, prompt:str) -> str:
    llm = ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL)
    res = llm.invoke, f'{prompt}: {query}'
    return res.content



def ConversationMemory() -> ConversationBufferMemory:
    return ConversationBufferMemory(memory_key="chat_history", output_key="answer", return_messages=True) 



#Plantilla para el prompt
def PromptTemplate(prompt:str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", f"{prompt}"),
    ])



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
    files = []
    for file_path in files_path:
        try:
            loader = UnstructuredLoader(file_path=file_path)
            pages = loader.load()
            files.append(RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(pages))
        except Exception as e:
            print(f'ERR: Could not read the file {file_path} \n{e}')
    return files



#Crea la DB
def CreateDB(docs) -> FAISS:
    embeddings = HuggingFaceEmbeddings()
    db = FAISS.from_documents(documents=docs, embedding=embeddings)
    db.save_local('deepseek_db')
    return db



#Consulta a la DB sin memoria
def DBQuery(db:FAISS, query:str):
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
        llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL, temperature=0.3),
        retriever=db.as_retriever(),
        memory=memory,
        return_source_documents=True,
        condense_question_prompt=prompt
    )

    res = qa.invoke({"question": query})
    return res['chat_history'][-1].content



#Consulta sobre un archivo
def FileQuery(query: str, file_path: str) -> str:
    docs = SplitFile(file_path=file_path)
    db = CreateDB(docs)
    
    qa = RetrievalQA.from_chain_type(
        llm=ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL),
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    res = qa.invoke({"query": query})
    return res['result']
    
